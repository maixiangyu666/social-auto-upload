"""
分组管理路由
"""
import sqlite3
from flask import Blueprint, request, jsonify
from services.group_service import GroupService

group_bp = Blueprint('group', __name__)


@group_bp.route('/api/groups', methods=['GET'])
def get_groups_api():
    """获取所有分组"""
    try:
        group_service = GroupService()
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)
        groups = group_service.get_groups_paginated(limit=limit, offset=offset)

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": groups
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取分组列表失败: {str(e)}",
            "data": None
        }), 500


@group_bp.route('/api/groups/<int:group_id>', methods=['GET'])
def get_group_detail_api(group_id):
    """获取分组详情"""
    try:
        group_service = GroupService()
        group = group_service.get_group_by_id(group_id)

        if not group:
            return jsonify({
                "code": 404,
                "msg": "分组不存在",
                "data": None
            }), 404

        return jsonify({
            "code": 200,
            "msg": "获取成功",
            "data": group
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"获取分组详情失败: {str(e)}",
            "data": None
        }), 500


@group_bp.route('/api/groups', methods=['POST'])
def create_group_api():
    """创建分组"""
    try:
        data = request.get_json()

        if not data.get('name'):
            return jsonify({
                "code": 400,
                "msg": "分组名称不能为空",
                "data": None
            }), 400

        group_service = GroupService()
        group_id = group_service.create_group(data)

        return jsonify({
            "code": 200,
            "msg": "创建成功",
            "data": {"id": group_id}
        }), 200
    except sqlite3.IntegrityError:
        return jsonify({
            "code": 400,
            "msg": "分组名称已存在",
            "data": None
        }), 400
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"创建分组失败: {str(e)}",
            "data": None
        }), 500


@group_bp.route('/api/groups/<int:group_id>', methods=['PUT'])
def update_group_api(group_id):
    """更新分组"""
    try:
        data = request.get_json()

        group_service = GroupService()
        success = group_service.update_group(group_id, data)

        if not success:
            return jsonify({
                "code": 404,
                "msg": "分组不存在或无需更新",
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
            "msg": f"更新分组失败: {str(e)}",
            "data": None
        }), 500


@group_bp.route('/api/groups/<int:group_id>', methods=['DELETE'])
def delete_group_api(group_id):
    """删除分组"""
    try:
        group_service = GroupService()
        success = group_service.delete_group(group_id)

        if not success:
            return jsonify({
                "code": 404,
                "msg": "分组不存在",
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
            "msg": f"删除分组失败: {str(e)}",
            "data": None
        }), 500


@group_bp.route('/api/accounts/batch-assign-group', methods=['POST'])
def batch_assign_group_api():
    """批量分配账号到分组"""
    try:
        data = request.get_json()
        account_ids = data.get('account_ids', [])
        group_id = data.get('group_id')  # None表示取消分组

        if not account_ids:
            return jsonify({
                "code": 400,
                "msg": "账号ID列表不能为空",
                "data": None
            }), 400

        group_service = GroupService()
        assigned_count = group_service.batch_assign_accounts(account_ids, group_id)

        return jsonify({
            "code": 200,
            "msg": "批量分配成功",
            "data": {"assigned_count": assigned_count}
        }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": f"批量分配失败: {str(e)}",
            "data": None
        }), 500

