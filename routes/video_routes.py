"""
视频发布路由
"""
import sqlite3
import threading
from pathlib import Path
from flask import Blueprint, request, jsonify
from conf import BASE_DIR
from services.task_service import TaskService
from services.task_executor import TaskExecutor
from utils.files_times import generate_schedule_time_next_day

video_bp = Blueprint('video', __name__)


def _get_file_id_by_path(file_path: str) -> int:
    """根据文件路径获取文件ID"""
    with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM file_records WHERE file_path = ?', (file_path,))
        row = cursor.fetchone()
        return row[0] if row else None


def _get_account_id_by_filepath(file_path: str) -> int:
    """根据账号文件路径获取账号ID"""
    with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM user_info WHERE filePath = ?', (file_path,))
        row = cursor.fetchone()
        return row[0] if row else None


@video_bp.route('/postVideo', methods=['POST'])
def postVideo():
    """
    发布视频接口（重构版 - 使用任务服务）
    现在创建任务并立即返回，任务在后台异步执行
    """
    try:
        # 获取JSON数据
        data = request.get_json()

        # 从JSON数据中提取参数
        file_list = data.get('fileList', [])  # 文件路径列表
        account_list = data.get('accountList', [])  # 账号文件路径列表
        platform_type = data.get('type')
        title = data.get('title')
        tags = data.get('tags', [])
        category = data.get('category', 0)
        enableTimer = data.get('enableTimer', False)
        productLink = data.get('productLink', '')
        productTitle = data.get('productTitle', '')
        thumbnail_path = data.get('thumbnail', '')
        is_draft = data.get('isDraft', False)
        videos_per_day = data.get('videosPerDay', 1)
        daily_times = data.get('dailyTimes', ['10:00'])
        start_days = data.get('startDays', 0)

        # 参数验证
        if not file_list:
            return jsonify({
                "code": 400,
                "msg": "文件列表不能为空",
                "data": None
            }), 400

        if not account_list:
            return jsonify({
                "code": 400,
                "msg": "账号列表不能为空",
                "data": None
            }), 400

        if not title:
            return jsonify({
                "code": 400,
                "msg": "标题不能为空",
                "data": None
            }), 400

        # 转换文件路径和账号路径为ID
        file_ids = []
        for file_path in file_list:
            file_id = _get_file_id_by_path(file_path)
            if file_id:
                file_ids.append(file_id)
            else:
                return jsonify({
                    "code": 400,
                    "msg": f"文件不存在: {file_path}",
                    "data": None
                }), 400

        account_ids = []
        for account_file_path in account_list:
            account_id = _get_account_id_by_filepath(account_file_path)
            if account_id:
                account_ids.append(account_id)
            else:
                return jsonify({
                    "code": 400,
                    "msg": f"账号不存在: {account_file_path}",
                    "data": None
                }), 400

        # 生成计划发布时间（如果需要定时发布）
        scheduled_times = None
        if enableTimer:
            try:
                # daily_times可能是字符串格式（如"10:00"）或整数格式（如10）
                # 需要转换为整数小时列表
                daily_hours = []
                for time_str in daily_times:
                    if isinstance(time_str, str):
                        # 解析"HH:MM"格式，只取小时部分
                        parts = time_str.split(':')
                        if len(parts) >= 1:
                            daily_hours.append(int(parts[0]))
                        else:
                            daily_hours.append(10)  # 默认10点
                    else:
                        daily_hours.append(int(time_str))

                # 生成发布时间列表（每个文件对应一个时间）
                scheduled_times = generate_schedule_time_next_day(
                    len(file_ids),
                    videos_per_day,
                    daily_hours,
                    timestamps=False,
                    start_days=start_days
                )

                # 如果scheduled_times长度不足，用最后一个时间填充
                if len(scheduled_times) < len(file_ids):
                    last_time = scheduled_times[-1] if scheduled_times else None
                    scheduled_times.extend([last_time] * (len(file_ids) - len(scheduled_times)))
            except Exception as e:
                import traceback
                print(f"生成发布时间失败: {e}")
                print(traceback.format_exc())
                return jsonify({
                    "code": 400,
                    "msg": f"生成发布时间失败: {str(e)}",
                    "data": None
                }), 400

        # 创建任务
        task_service = TaskService()
        task_ids = task_service.create_batch_tasks(
            platform_type=platform_type,
            account_ids=account_ids,
            file_ids=file_ids,
            title=title,
            tags=tags,
            category=category,
            product_link=productLink,
            product_title=productTitle,
            thumbnail_path=thumbnail_path,
            is_draft=1 if is_draft else 0,
            schedule_enabled=1 if enableTimer else 0,
            scheduled_times=scheduled_times
        )

        # 启动后台任务执行
        def execute_tasks_async():
            """异步执行任务"""
            import asyncio
            executor = TaskExecutor()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            for task_id in task_ids:
                try:
                    loop.run_until_complete(executor.execute_with_retry(task_id))
                except Exception as e:
                    print(f"任务 {task_id} 执行失败: {e}")

            loop.close()

        # 在新线程中执行任务
        thread = threading.Thread(target=execute_tasks_async, daemon=True)
        thread.start()

        # 立即返回任务ID列表
        return jsonify({
            "code": 200,
            "msg": "任务已创建，正在后台执行",
            "data": {
                "task_ids": task_ids,
                "total_tasks": len(task_ids)
            }
        }), 200

    except Exception as e:
        print(f"创建发布任务失败: {e}")
        return jsonify({
            "code": 500,
            "msg": f"创建任务失败: {str(e)}",
            "data": None
        }), 500

