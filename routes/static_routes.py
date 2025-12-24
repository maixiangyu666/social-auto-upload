"""
静态资源路由
"""
import os
from flask import Blueprint, send_from_directory

static_bp = Blueprint('static', __name__)

# 获取当前目录
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@static_bp.route('/')
def index():
    """首页"""
    return send_from_directory(current_dir, 'index.html')


@static_bp.route('/assets/<filename>')
def custom_static(filename):
    """静态资源"""
    return send_from_directory(os.path.join(current_dir, 'assets'), filename)


@static_bp.route('/favicon.ico')
def favicon():
    """Favicon"""
    return send_from_directory(os.path.join(current_dir, 'assets'), 'vite.svg')


@static_bp.route('/vite.svg')
def vite_svg():
    """Vite SVG"""
    return send_from_directory(os.path.join(current_dir, 'assets'), 'vite.svg')

