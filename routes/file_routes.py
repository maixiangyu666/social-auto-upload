"""
文件管理路由
"""
import os
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, send_from_directory, send_file
from conf import BASE_DIR

file_bp = Blueprint('file', __name__)


def _safe_resolve_under(base_dir: Path, relative_path: str) -> Path:
    """
    将相对路径安全解析到 base_dir 下，防止路径穿越。
    允许形如 'YYYY/MM/DD/xxx.ext' 的子目录结构。
    """
    # 统一分隔符，去掉可能的前导斜杠
    rel = str(relative_path).lstrip("/\\").replace("\\", "/")
    target = (base_dir / rel).resolve()
    base = base_dir.resolve()
    if base not in target.parents and target != base:
        raise ValueError("Invalid path")
    return target


@file_bp.route('/upload', methods=['POST'])
def upload_file():
    """简单文件上传（不保存到数据库）"""
    if 'file' not in request.files:
        return jsonify({
            "code": 200,
            "data": None,
            "msg": "No file part in the request"
        }), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 200,
            "data": None,
            "msg": "No selected file"
        }), 400
    try:
        # 保存文件到指定位置
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 按日期分目录：videoFile/YYYY/MM/DD/
        date_dir = datetime.now().strftime("%Y/%m/%d")
        save_dir = Path(BASE_DIR / "videoFile" / date_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        filepath = save_dir / f"{uuid_v1}_{file.filename}"
        file.save(filepath)
        return jsonify({"code": 200, "msg": "File uploaded successfully", "data": f"{date_dir}/{uuid_v1}_{file.filename}"}), 200
    except Exception as e:
        return jsonify({"code": 200, "msg": str(e), "data": None}), 500


@file_bp.route('/getFile', methods=['GET'])
def get_file():
    """获取文件"""
    # 新：支持传 file_path（含子目录）；旧：兼容 filename（仅根目录）
    file_path = request.args.get('file_path') or request.args.get('path')
    filename = request.args.get('filename')

    base_dir = Path(BASE_DIR / "videoFile")

    try:
        if file_path:
            target = _safe_resolve_under(base_dir, file_path)
            if not target.exists() or not target.is_file():
                return {"error": "File not found"}, 404
            return send_file(str(target), as_attachment=False)

        if not filename:
            return {"error": "file_path or filename is required"}, 400

        # 旧逻辑：仅允许根目录文件名
        if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
            return {"error": "Invalid filename"}, 400
        return send_from_directory(str(base_dir), filename)
    except ValueError:
        return {"error": "Invalid path"}, 400


@file_bp.route('/download/<path:file_path>', methods=['GET'])
def download_file(file_path: str):
    """下载文件（支持子目录）"""
    base_dir = Path(BASE_DIR / "videoFile")
    try:
        target = _safe_resolve_under(base_dir, file_path)
        if not target.exists() or not target.is_file():
            return jsonify({"code": 404, "msg": "File not found", "data": None}), 404
        return send_file(str(target), as_attachment=True, download_name=target.name)
    except ValueError:
        return jsonify({"code": 400, "msg": "Invalid path", "data": None}), 400


@file_bp.route('/uploadSave', methods=['POST'])
def upload_save():
    """上传文件并保存到数据库"""
    if 'file' not in request.files:
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No file part in the request"
        }), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "code": 400,
            "data": None,
            "msg": "No selected file"
        }), 400

    # 获取表单中的自定义文件名（可选）
    custom_filename = request.form.get('filename', None)
    if custom_filename:
        filename = custom_filename + "." + file.filename.split('.')[-1]
    else:
        filename = file.filename

    try:
        # 生成 UUID v1
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")

        # 按日期分目录：videoFile/YYYY/MM/DD/
        date_dir = datetime.now().strftime("%Y/%m/%d")
        save_dir = Path(BASE_DIR / "videoFile" / date_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        # 构造文件名和路径（file_path 存相对路径，含日期目录）
        final_filename = f"{uuid_v1}_{filename}"
        relative_path = f"{date_dir}/{final_filename}"
        filepath = save_dir / final_filename

        # 保存文件
        file.save(filepath)

        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO file_records (filename, filesize, file_path)
                VALUES (?, ?, ?)
            ''', (filename, round(float(os.path.getsize(filepath)) / (1024 * 1024), 2), relative_path))
            conn.commit()
            print("✅ 上传文件已记录")

        return jsonify({
            "code": 200,
            "msg": "File uploaded and saved successfully",
            "data": {
                "filename": filename,
                "filepath": relative_path
            }
        }), 200

    except Exception as e:
        print(f"Upload failed: {e}")
        return jsonify({
            "code": 500,
            "msg": f"upload failed: {e}",
            "data": None
        }), 500


@file_bp.route('/getFiles', methods=['GET'])
def get_all_files():
    """获取所有文件列表"""
    try:
        limit = request.args.get('limit', default=50, type=int)
        offset = request.args.get('offset', default=0, type=int)
        keyword = request.args.get('keyword', default=None, type=str)

        # 使用 with 自动管理数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row  # 允许通过列名访问结果
            cursor = conn.cursor()

            where = ["is_deleted = 0"]
            params = []
            if keyword:
                where.append("filename LIKE ?")
                params.append(f"%{keyword}%")
            where_sql = "WHERE " + " AND ".join(where) if where else ""

            cursor.execute(f"SELECT COUNT(1) as cnt FROM file_records {where_sql}", params)
            total = int(cursor.fetchone()['cnt'])

            cursor.execute(
                f"SELECT * FROM file_records {where_sql} ORDER BY upload_time DESC LIMIT ? OFFSET ?",
                params + [limit, offset],
            )
            rows = cursor.fetchall()

            # 将结果转为字典列表，并提取UUID
            data = []
            for row in rows:
                row_dict = dict(row)
                # 从 file_path 中提取 UUID (文件名的第一部分，下划线前)
                if row_dict.get('file_path'):
                    # file_path 可能包含子目录：YYYY/MM/DD/uuid_xxx.ext
                    name = Path(row_dict['file_path']).name
                    file_path_parts = name.split('_', 1)  # 只分割第一个下划线
                    if len(file_path_parts) > 0:
                        row_dict['uuid'] = file_path_parts[0]  # UUID 部分
                    else:
                        row_dict['uuid'] = ''
                else:
                    row_dict['uuid'] = ''
                data.append(row_dict)

            return jsonify({
                "code": 200,
                "msg": "success",
                "data": {
                    "items": data,
                    "total": total,
                    "limit": limit,
                    "offset": offset
                }
            }), 200
    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("get file failed!"),
            "data": None
        }), 500


@file_bp.route('/deleteFile', methods=['GET'])
def delete_file():
    """删除文件"""
    file_id = request.args.get('id')

    if not file_id or not file_id.isdigit():
        return jsonify({
            "code": 400,
            "msg": "Invalid or missing file ID",
            "data": None
        }), 400

    try:
        # 获取数据库连接
        with sqlite3.connect(Path(BASE_DIR / "db" / "database.db")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询要删除的记录
            cursor.execute("SELECT * FROM file_records WHERE id = ?", (file_id,))
            record = cursor.fetchone()

            if not record:
                return jsonify({
                    "code": 404,
                    "msg": "File not found",
                    "data": None
                }), 404

            record = dict(record)

            # 获取文件路径并删除实际文件
            file_path = Path(BASE_DIR / "videoFile" / record['file_path'])
            if file_path.exists():
                try:
                    file_path.unlink()  # 删除文件
                    print(f"✅ 实际文件已删除: {file_path}")
                except Exception as e:
                    print(f"⚠️ 删除实际文件失败: {e}")
                    # 即使删除文件失败，也要继续删除数据库记录，避免数据不一致
            else:
                print(f"⚠️ 实际文件不存在: {file_path}")

            # 删除数据库记录
            cursor.execute("DELETE FROM file_records WHERE id = ?", (file_id,))
            conn.commit()

        return jsonify({
            "code": 200,
            "msg": "File deleted successfully",
            "data": {
                "id": record['id'],
                "filename": record['filename']
            }
        }), 200

    except Exception as e:
        return jsonify({
            "code": 500,
            "msg": str("delete failed!"),
            "data": None
        }), 500

