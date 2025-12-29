"""
登录相关路由
"""
import json
import threading
import uuid
from queue import Queue
from flask import Blueprint, request, jsonify, Response
from services.login_service import LoginService
from services.account_service import AccountService

login_bp = Blueprint('login', __name__)

# 全局变量（需要在主文件中初始化）
active_queues = {}
login_service = None


def init_login_routes(app_instance, queues_dict, service_instance):
    """初始化登录路由的全局变量"""
    global active_queues, login_service
    active_queues = queues_dict
    login_service = service_instance


def run_login_async(session_id, platform_type, account_name, status_queue, account_id=None):
    """在新线程中运行异步登录逻辑"""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(
            login_service.login_platform(
                int(platform_type),
                account_name,
                status_queue,
                account_id=int(account_id) if account_id else None,
                session_id=session_id,
            )
        )
    except Exception as e:
        try:
            status_queue.put(json.dumps({"event": "error", "code": 500, "msg": str(e)}, ensure_ascii=False))
        except Exception:
            pass
    finally:
        loop.close()


def sse_stream(status_queue):
    """SSE 流生成器函数"""
    import time
    while True:
        if not status_queue.empty():
            msg = status_queue.get()
            if isinstance(msg, (dict, list)):
                msg = json.dumps(msg, ensure_ascii=False)
            yield f"data: {msg}\n\n"
        else:
            # 避免 CPU 占满
            time.sleep(0.1)


@login_bp.route('/login')
def login():
    """
    SSE 登录（向后兼容）
    参数：
      - type: 平台类型 (1-7)
      - id: 账号名称（自定义）
    """
    platform_type = request.args.get('type')
    account_name = request.args.get('id')
    if not platform_type or not account_name:
        return jsonify({"code": 400, "msg": "缺少type或id参数", "data": None}), 400

    # 统一使用 session_id 做并发隔离（避免同名账号重复登录互相覆盖）
    session_id = str(uuid.uuid4())

    status_queue = Queue()
    active_queues[session_id] = status_queue

    # 推送 session_id，前端手动登录时需要它进行 confirm
    status_queue.put(json.dumps({"event": "session", "session_id": session_id}, ensure_ascii=False))

    thread = threading.Thread(target=run_login_async, args=(session_id, platform_type, account_name, status_queue), daemon=True)
    thread.start()

    response = Response(sse_stream(status_queue), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # 关键：禁用 Nginx 缓冲
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Connection'] = 'keep-alive'
    return response


@login_bp.route('/api/accounts/login/confirm', methods=['POST'])
def confirm_login():
    """
    手动登录确认（百家号/TikTok）
    body: { "session_id": "..." }
    """
    try:
        data = request.get_json(force=True) or {}
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({"code": 400, "msg": "缺少session_id", "data": None}), 400
        ok = login_service.confirm_manual_session(session_id)
        if not ok:
            return jsonify({"code": 404, "msg": "session不存在或已过期", "data": None}), 404
        return jsonify({"code": 200, "msg": "confirmed", "data": None}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": f"confirm失败: {str(e)}", "data": None}), 500


@login_bp.route('/api/accounts/login', methods=['POST'])
def login_rest():
    """
    RESTful 登录（可选）
    - 返回 session_id
    - 前端可轮询 /api/accounts/login/status/<session_id> 获取进度
    """
    try:
        data = request.get_json(force=True) or {}
        platform_type = data.get('platform_type')
        account_name = data.get('account_name')
        account_id = data.get('account_id')

        if not platform_type or not account_name:
            return jsonify({"code": 400, "msg": "缺少platform_type或account_name", "data": None}), 400

        session_id = str(uuid.uuid4())
        q = Queue()
        active_queues[session_id] = q
        q.put(json.dumps({"event": "session", "session_id": session_id}, ensure_ascii=False))

        thread = threading.Thread(
            target=run_login_async,
            args=(session_id, str(platform_type), account_name, q, account_id),
            daemon=True
        )
        thread.start()

        return jsonify({"code": 200, "msg": "started", "data": {"session_id": session_id}}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": f"login启动失败: {str(e)}", "data": None}), 500


@login_bp.route('/api/accounts/login/status/<session_id>', methods=['GET'])
def login_status(session_id):
    """轮询登录状态（与 /api/accounts/login 配合）"""
    q = active_queues.get(session_id)
    if not q:
        return jsonify({"code": 404, "msg": "session不存在或已完成清理", "data": {"messages": [], "done": True}}), 404
    msgs = []
    while not q.empty():
        msgs.append(q.get())
    # done: 如果已经出现 success/error 事件，认为结束
    done = any(
        (isinstance(m, str) and ('"event":"success"' in m or '"event":"error"' in m or '"event": "success"' in m or '"event": "error"' in m))
        for m in msgs
    )
    return jsonify({"code": 200, "msg": "ok", "data": {"messages": msgs, "done": done}}), 200


@login_bp.route('/api/accounts/<int:account_id>/refresh-cookie-with-login', methods=['POST'])
def refresh_cookie_with_login(account_id: int) -> tuple[Response, int]:
    """
    刷新Cookie（复用登录流程）
    返回 session_id，前端通过轮询 /api/accounts/login/status/<session_id> 获取进度
    """
    try:
        acc = AccountService().get_account_by_id(account_id)
        if not acc:
            return jsonify({"code": 404, "msg": "账号不存在", "data": None}), 404

        session_id = str(uuid.uuid4())
        q = Queue()
        active_queues[session_id] = q
        q.put(json.dumps({"event": "session", "session_id": session_id}, ensure_ascii=False))

        thread = threading.Thread(
            target=run_login_async,
            args=(session_id, str(acc.get('type')), str(acc.get('userName')), q, int(account_id)),
            daemon=True
        )
        thread.start()

        return jsonify({"code": 200, "msg": "started", "data": {"session_id": session_id}}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": f"启动刷新失败: {str(e)}", "data": None}), 500

