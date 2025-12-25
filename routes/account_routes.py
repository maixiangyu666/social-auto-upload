"""
账号管理路由
"""
import asyncio
import sqlite3
import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify, send_from_directory
from conf import BASE_DIR
from myUtils.auth import check_cookie
from services.account_service import AccountService
from services.cookie_refresh_service import CookieRefreshService

account_bp = Blueprint('account', __name__)


@account_bp.route('/uploadCookie', methods=['POST'])
def upload_cookie():
    """Cookie文件上传API"""
    try:
        if 'file' not in request.files:
            return jsonify({
                "code": 500,
                "msg": "没有找到Cookie文件",
                "data": None
            }), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({
                "code": 500,
                "msg": "Cookie文件名不能为空",
                "data": None
            }), 400

        if not file.filename.endswith('.json'):
            return jsonify({
                "code": 500,
                "msg": "Cookie文件必须是JSON格式",
                "data": None
            }), 400

        # 兼容两种模式：
        # 1) 更新已有账号 cookie：传 form.id + form.platform
        # 2) 新增账号（Bilibili）：传 form.platform + form.account_name（不传 id）
        account_id = request.form.get('id')
        platform = request.form.get('platform') or request.form.get('platform_type')
        account_name = request.form.get('account_name') or request.form.get('userName') or request.form.get('name')

        if not platform:
            return jsonify({"code": 500, "msg": "缺少平台信息(platform)", "data": None}), 400

        platform_type = int(platform)
        account_service = AccountService()

        # -------- 更新已有账号 --------
        if account_id:
            with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT filePath FROM user_info WHERE id = ?', (account_id,))
                result = cursor.fetchone()

            if not result:
                return jsonify({"code": 500, "msg": "账号不存在", "data": None}), 404

            cookie_file_path = Path(BASE_DIR / "cookiesFile" / result['filePath'])
            cookie_file_path.parent.mkdir(parents=True, exist_ok=True)
            file.save(str(cookie_file_path))

            # 校验并更新状态
            ok = asyncio.run(check_cookie(platform_type, result['filePath']))
            account_service.update_verify_time(int(account_id), ok)

            return jsonify({"code": 200, "msg": "Cookie文件上传成功", "data": {"valid": ok}}), 200

        # -------- 新增账号（Bilibili 推荐）--------
        if platform_type != 5:
            return jsonify({"code": 400, "msg": "新增账号的Cookie上传目前仅支持Bilibili(platform=5)", "data": None}), 400

        if not account_name:
            return jsonify({"code": 400, "msg": "缺少账号名称(account_name)", "data": None}), 400

        new_cookie_name = f"{uuid.uuid4()}.json"
        cookie_file_path = Path(BASE_DIR / "cookiesFile" / new_cookie_name)
        cookie_file_path.parent.mkdir(parents=True, exist_ok=True)
        file.save(str(cookie_file_path))

        ok = asyncio.run(check_cookie(platform_type, new_cookie_name))
        if not ok:
            try:
                cookie_file_path.unlink()
            except Exception:
                pass
            return jsonify({"code": 400, "msg": "Cookie校验失败", "data": None}), 400

        new_id = account_service.create_account({
            "type": platform_type,
            "filePath": new_cookie_name,
            "userName": account_name,
            "status": AccountService.STATUS_VALID
        })
        account_service.update_verify_time(new_id, True)
        account_service.schedule_next_refresh(new_id)

        return jsonify({"code": 200, "msg": "Cookie上传并创建账号成功", "data": {"account_id": new_id}}), 200

    except Exception as e:
        print(f"上传Cookie文件时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"上传Cookie文件失败: {str(e)}",
            "data": None
        }), 500


@account_bp.route('/downloadCookie', methods=['GET'])
def download_cookie():
    """Cookie文件下载API"""
    try:
        file_path = request.args.get('filePath')
        if not file_path:
            return jsonify({
                "code": 500,
                "msg": "缺少文件路径参数",
                "data": None
            }), 400

        # 验证文件路径的安全性，防止路径遍历攻击
        cookie_file_path = Path(BASE_DIR / "cookiesFile" / file_path).resolve()
        base_path = Path(BASE_DIR / "cookiesFile").resolve()

        if not cookie_file_path.is_relative_to(base_path):
            return jsonify({
                "code": 500,
                "msg": "非法文件路径",
                "data": None
            }), 400

        if not cookie_file_path.exists():
            return jsonify({
                "code": 500,
                "msg": "Cookie文件不存在",
                "data": None
            }), 404

        # 返回文件
        return send_from_directory(
            directory=str(cookie_file_path.parent),
            path=cookie_file_path.name,
            as_attachment=True
        )

    except Exception as e:
        print(f"下载Cookie文件时出错: {str(e)}")
        return jsonify({
            "code": 500,
            "msg": f"下载Cookie文件失败: {str(e)}",
            "data": None
        }), 500


@account_bp.route('/api/accounts', methods=['GET'])
def get_accounts_api():
    """获取账号列表（支持筛选）"""
    try:
        account_service = AccountService()

        # 获取筛选参数
        filters = {}
        platform_type = request.args.get('platform_type')
        status = request.args.get('status')
        group_id = request.args.get('group_id')
        keyword = request.args.get('keyword')
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)

        if platform_type:
            filters['platform_type'] = int(platform_type)
        if status is not None:
            filters['status'] = int(status)
        if group_id is not None:
            filters['group_id'] = int(group_id) if group_id != '0' else 0
        if keyword:
            filters['keyword'] = keyword

        accounts = account_service.get_accounts_paginated(filters, limit=limit, offset=offset)

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": accounts
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取账号列表失败: {str(e)}",
            "data": None
        }), 500


@account_bp.route('/api/accounts/<int:account_id>', methods=['GET'])
def get_account_detail_api(account_id):
    """获取账号详情"""
    try:
        account_service = AccountService()
        account = account_service.get_account_by_id(account_id)

        if not account:
            return jsonify({
                "code": 404,
                "msg": "账号不存在",
                "data": None
            }), 404

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": account
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取账号详情失败: {str(e)}",
            "data": None
        }), 500


@account_bp.route('/api/accounts', methods=['POST'])
def create_account_api():
    """创建账号"""
    try:
        data = request.get_json()

        if not data.get('type') or not data.get('filePath') or not data.get('userName'):
            return jsonify({
                "code": 400,
                "msg": "缺少必填字段",
                "data": None
            }), 400

        account_service = AccountService()
        account_id = account_service.create_account(data)

        return jsonify({
            "code": 200,
            "msg": "创建成功",
            "data": {"id": account_id}
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"创建账号失败: {str(e)}",
            "data": None
        }), 500


@account_bp.route('/api/accounts/<int:account_id>', methods=['PUT'])
def update_account_api(account_id):
    """更新账号"""
    try:
        data = request.get_json()

        account_service = AccountService()
        success = account_service.update_account(account_id, data)

        if not success:
            return jsonify({
                "code": 404,
                "msg": "账号不存在或无需更新",
                "data": None
            }), 404

        return jsonify({
            "code": 200,
            "msg": "更新成功",
            "data": None
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"更新账号失败: {str(e)}",
            "data": None
        }), 500


@account_bp.route('/api/accounts/<int:account_id>', methods=['DELETE'])
def delete_account_api(account_id):
    """删除账号"""
    try:
        account_service = AccountService()
        success = account_service.delete_account(account_id)

        if not success:
            return jsonify({
                "code": 404,
                "msg": "账号不存在",
                "data": None
            }), 404

        return jsonify({
            "code": 200,
            "msg": "删除成功",
            "data": None
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"删除账号失败: {str(e)}",
            "data": None
        }), 500


@account_bp.route('/api/accounts/batch-delete', methods=['POST'])
def batch_delete_accounts_api():
    """批量删除账号"""
    try:
        data = request.get_json()
        account_ids = data.get('account_ids', [])

        if not account_ids:
            return jsonify({
                "code": 400,
                "msg": "账号ID列表不能为空",
                "data": None
            }), 400

        account_service = AccountService()
        deleted_count = account_service.batch_delete_accounts(account_ids)

        return jsonify({
            "code": 200,
            "msg": "批量删除成功",
            "data": {"deleted_count": deleted_count}
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"批量删除失败: {str(e)}",
            "data": None
        }), 500


@account_bp.route('/api/accounts/batch-verify', methods=['POST'])
def batch_verify_accounts_api():
    """批量验证Cookie"""
    try:
        data = request.get_json()
        account_ids = data.get('account_ids', [])

        if not account_ids:
            return jsonify({
                "code": 400,
                "msg": "账号ID列表不能为空",
                "data": None
            }), 400

        account_service = AccountService()
        accounts = [account_service.get_account_by_id(id) for id in account_ids]

        async def verify_all():
            results = []
            for account in accounts:
                if account:
                    result = await check_cookie(account['type'], account['filePath'])
                    account_service.update_verify_time(account['id'], result)
                    results.append({
                        'account_id': account['id'],
                        'success': result
                    })
            return results

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        verify_results = loop.run_until_complete(verify_all())
        loop.close()

        return jsonify({
            "code": 200,
            "msg": "批量验证完成",
            "data": verify_results
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"批量验证失败: {str(e)}",
            "data": None
        }), 500


@account_bp.route('/api/accounts/<int:account_id>/refresh-cookie', methods=['POST'])
def refresh_cookie_api(account_id):
    """手动刷新Cookie"""
    try:
        cookie_refresh_service = CookieRefreshService()
        mode = request.args.get('mode') or (request.get_json(silent=True) or {}).get('mode') or 'background'

        async def refresh():
            if mode == 'login':
                return await cookie_refresh_service.refresh_account_cookie(account_id)
            # 默认：后台无感刷新
            return await cookie_refresh_service.refresh_account_cookie_background(account_id)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(refresh())
        loop.close()

        if result['success']:
            return jsonify({
                "code": 200,
                "msg": result['message'],
                "data": result
            }), 200
        else:
            return jsonify({
                "code": 500,
                "msg": result['message'],
                "data": None
            }), 500
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"刷新Cookie失败: {str(e)}",
            "data": None
        }), 500


@account_bp.route('/api/accounts/<int:account_id>/cookie-refresh-logs', methods=['GET'])
def get_cookie_refresh_logs(account_id: int):
    """获取单账号 Cookie 刷新/验证日志（分页）"""
    try:
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)
        cookie_refresh_service = CookieRefreshService()
        data = cookie_refresh_service.get_refresh_logs(account_id, limit=limit, offset=offset)
        return jsonify({"code": 200, "msg": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"code": 500, "msg": f"获取日志失败: {str(e)}", "data": None}), 500


@account_bp.route('/api/accounts/batch-refresh-cookie', methods=['POST'])
def batch_refresh_cookies_api():
    """批量刷新Cookie"""
    try:
        data = request.get_json()
        account_ids = data.get('account_ids', [])

        if not account_ids:
            return jsonify({
                "code": 400,
                "msg": "账号ID列表不能为空",
                "data": None
            }), 400

        cookie_refresh_service = CookieRefreshService()

        async def refresh_all():
            return await cookie_refresh_service.batch_refresh_cookies(account_ids)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(refresh_all())
        loop.close()

        return jsonify({
            "code": 200,
            "msg": "批量刷新完成",
            "data": results
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"批量刷新失败: {str(e)}",
            "data": None
        }), 500


@account_bp.route('/api/accounts/<int:account_id>/statistics', methods=['GET'])
def get_account_statistics_api(account_id):
    """获取账号统计"""
    try:
        account_service = AccountService()
        statistics = account_service.get_account_statistics(account_id)

        if not statistics:
            return jsonify({
                "code": 404,
                "msg": "账号不存在",
                "data": None
            }), 404

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": statistics
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取统计失败: {str(e)}",
            "data": None
        }), 500

