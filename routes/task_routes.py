"""
任务管理路由
"""
import threading
from flask import Blueprint, request, jsonify
from services.task_service import TaskService
from services.task_executor import TaskExecutor

task_bp = Blueprint('task', __name__)


@task_bp.route('/getTask/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """获取任务详情"""
    try:
        task_service = TaskService()
        task = task_service.get_task(task_id)

        if task:
            return jsonify({
                "code": 200,
                "msg": "success",
                "data": task
            }), 200
        else:
            return jsonify({
                "code": 404,
                "msg": "任务不存在",
                "data": None
            }), 404
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取任务失败: {str(e)}",
            "data": None
        }), 500


@task_bp.route('/listTasks', methods=['GET'])
def list_tasks():
    """查询任务列表"""
    try:
        platform_type = request.args.get('platform_type', type=int)
        account_id = request.args.get('account_id', type=int)
        status = request.args.get('status', type=int)
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)

        task_service = TaskService()
        tasks = task_service.list_tasks(
            platform_type=platform_type,
            account_id=account_id,
            status=status,
            limit=limit,
            offset=offset
        )

        return jsonify({
            "code": 200,
            "msg": "success",
            "data": tasks
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"查询任务列表失败: {str(e)}",
            "data": None
        }), 500


@task_bp.route('/cancelTask/<int:task_id>', methods=['POST'])
def cancel_task(task_id):
    """取消任务"""
    try:
        task_service = TaskService()
        success = task_service.cancel_task(task_id)

        if success:
            return jsonify({
                "code": 200,
                "msg": "任务已取消",
                "data": None
            }), 200
        else:
            return jsonify({
                "code": 404,
                "msg": "任务不存在或无法取消",
                "data": None
            }), 404
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"取消任务失败: {str(e)}",
            "data": None
        }), 500


@task_bp.route('/retryTask/<int:task_id>', methods=['POST'])
def retry_task(task_id):
    """重试失败的任务"""
    try:
        task_service = TaskService()
        task = task_service.get_task(task_id)

        if not task:
            return jsonify({
                "code": 404,
                "msg": "任务不存在",
                "data": None
            }), 404

        if task['status'] != TaskService.STATUS_FAILED:
            return jsonify({
                "code": 400,
                "msg": "只能重试失败的任务",
                "data": None
            }), 400

        # 将任务状态重置为待发布
        task_service.update_task_status(task_id, TaskService.STATUS_PENDING, error_message=None)

        # 启动后台任务执行
        def execute_task_async():
            import asyncio
            executor = TaskExecutor()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(executor.execute_with_retry(task_id))
            except Exception as e:
                print(f"重试任务 {task_id} 失败: {e}")
            finally:
                loop.close()

        thread = threading.Thread(target=execute_task_async, daemon=True)
        thread.start()

        return jsonify({
            "code": 200,
            "msg": "任务已重新执行",
            "data": None
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"重试任务失败: {str(e)}",
            "data": None
        }), 500

