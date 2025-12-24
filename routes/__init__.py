"""
路由模块
按功能拆分不同的路由文件
"""
from flask import Blueprint

# 导入所有路由模块
from .static_routes import static_bp
from .file_routes import file_bp
from .account_routes import account_bp
from .login_routes import login_bp
from .task_routes import task_bp
from .group_routes import group_bp
from .video_routes import video_bp

__all__ = [
    'static_bp',
    'file_bp',
    'account_bp',
    'login_bp',
    'task_bp',
    'group_bp',
    'video_bp',
]

