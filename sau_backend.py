"""
Flask 后端主文件
负责初始化应用和注册路由
"""
import os
from flask_cors import CORS
from flask import Flask
from services.scheduler_service import SchedulerService
from services.login_service import LoginService
from routes import (
    static_bp,
    file_bp,
    account_bp,
    login_bp,
    task_bp,
    group_bp,
    video_bp,
    proxy_bp
)

# 设置 Flask CLI 默认端口（用于 flask run 命令）
os.environ.setdefault('FLASK_RUN_PORT', '5409')
os.environ.setdefault('FLASK_RUN_HOST', '0.0.0.0')

# 初始化 Flask 应用
app = Flask(__name__)

# 允许所有来源跨域访问
CORS(app)

# 限制上传文件大小为160MB
app.config['MAX_CONTENT_LENGTH'] = 160 * 1024 * 1024

# 初始化全局变量
active_queues = {}
login_service = LoginService()

# 初始化登录路由的全局变量
from routes.login_routes import init_login_routes
init_login_routes(app, active_queues, login_service)

# 注册路由蓝图
app.register_blueprint(static_bp)
app.register_blueprint(file_bp)
app.register_blueprint(account_bp)
app.register_blueprint(login_bp)
app.register_blueprint(task_bp)
app.register_blueprint(group_bp)
app.register_blueprint(video_bp)
app.register_blueprint(proxy_bp)

_scheduler = SchedulerService()


def _should_start_scheduler() -> bool:
    """
    确保在以下场景启动一次 scheduler：
    - python sau_backend.py
    - flask run（避免 reloader 导致启动两次）
    """
    if os.environ.get("RUN_SCHEDULER", "1") != "1":
        return False
    # Flask reloader 子进程标记
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        return True
    # 不开 reloader 时，WERKZEUG_RUN_MAIN 不存在；此时直接启动即可
    if os.environ.get("FLASK_RUN_FROM_CLI") == "true" and os.environ.get("WERKZEUG_RUN_MAIN") is None:
        return True
    # 直接运行脚本
    return __name__ == "__main__"


if _should_start_scheduler():
    _scheduler.start_cookie_refresh_scheduler()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5409)
