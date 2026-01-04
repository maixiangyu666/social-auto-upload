"""
代理管理路由
"""
from flask import Blueprint, request, jsonify
from services.proxy_service import ProxyService

proxy_bp = Blueprint('proxy', __name__)


@proxy_bp.route('/api/proxies', methods=['GET'])
def get_proxies_api():
    """获取代理列表（支持筛选和分页）"""
    try:
        proxy_service = ProxyService()

        # 获取筛选参数
        filters = {}
        proxy_type = request.args.get('proxy_type')
        is_enabled = request.args.get('is_enabled')
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)

        if proxy_type:
            filters['proxy_type'] = proxy_type
        if is_enabled is not None:
            filters['is_enabled'] = int(is_enabled)

        proxies = proxy_service.get_proxies_paginated(filters, limit=limit, offset=offset)

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": proxies
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取代理列表失败: {str(e)}",
            "data": None
        }), 500


@proxy_bp.route('/api/proxies/<int:proxy_id>', methods=['GET'])
def get_proxy_detail_api(proxy_id):
    """获取代理详情"""
    try:
        proxy_service = ProxyService()
        proxy = proxy_service.get_proxy_by_id(proxy_id)

        if not proxy:
            return jsonify({
                "code": 404,
                "msg": "代理不存在",
                "data": None
            }), 404

        # 隐藏密码
        if proxy.get('password'):
            proxy['password'] = '******'

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": proxy
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取代理详情失败: {str(e)}",
            "data": None
        }), 500


@proxy_bp.route('/api/proxies', methods=['POST'])
def create_proxy_api():
    """创建代理"""
    try:
        data = request.get_json()

        if not data.get('proxy_name') or not data.get('proxy_type') or not data.get('host') or not data.get('port'):
            return jsonify({
                "code": 400,
                "msg": "缺少必填字段",
                "data": None
            }), 400

        # 验证代理类型
        if data['proxy_type'] not in ['http', 'https', 'socks5']:
            return jsonify({
                "code": 400,
                "msg": "代理类型必须是 http、https 或 socks5",
                "data": None
            }), 400

        proxy_service = ProxyService()
        proxy_id = proxy_service.create_proxy(data)

        return jsonify({
            "code": 200,
            "msg": "创建成功",
            "data": {"id": proxy_id}
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"创建代理失败: {str(e)}",
            "data": None
        }), 500


@proxy_bp.route('/api/proxies/<int:proxy_id>', methods=['PUT'])
def update_proxy_api(proxy_id):
    """更新代理"""
    try:
        data = request.get_json()

        # 验证代理类型
        if 'proxy_type' in data and data['proxy_type'] not in ['http', 'https', 'socks5']:
            return jsonify({
                "code": 400,
                "msg": "代理类型必须是 http、https 或 socks5",
                "data": None
            }), 400

        proxy_service = ProxyService()
        success = proxy_service.update_proxy(proxy_id, data)

        if not success:
            return jsonify({
                "code": 404,
                "msg": "代理不存在或无需更新",
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
            "msg": f"更新代理失败: {str(e)}",
            "data": None
        }), 500


@proxy_bp.route('/api/proxies/<int:proxy_id>', methods=['DELETE'])
def delete_proxy_api(proxy_id):
    """删除代理"""
    try:
        proxy_service = ProxyService()
        success = proxy_service.delete_proxy(proxy_id)

        if not success:
            return jsonify({
                "code": 404,
                "msg": "代理不存在",
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
            "msg": f"删除代理失败: {str(e)}",
            "data": None
        }), 500


@proxy_bp.route('/api/proxies/batch-delete', methods=['POST'])
def batch_delete_proxies_api():
    """批量删除代理"""
    try:
        data = request.get_json()
        proxy_ids = data.get('proxy_ids', [])

        if not proxy_ids:
            return jsonify({
                "code": 400,
                "msg": "代理ID列表不能为空",
                "data": None
            }), 400

        proxy_service = ProxyService()
        deleted_count = proxy_service.batch_delete_proxies(proxy_ids)

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


@proxy_bp.route('/api/proxies/simple', methods=['GET'])
def get_proxies_simple_api():
    """获取代理简单列表（用于下拉选择）"""
    try:
        proxy_service = ProxyService()
        proxies = proxy_service.get_proxies({'is_enabled': 1})

        # 只返回必要字段
        simple_proxies = []
        for p in proxies:
            simple_proxies.append({
                'id': p['id'],
                'proxy_name': p['proxy_name'],
                'proxy_type': p['proxy_type']
            })

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": simple_proxies
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取代理列表失败: {str(e)}",
            "data": []
        }), 500
