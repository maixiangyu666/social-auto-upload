#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代理管理服务
负责代理的CRUD操作
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from conf import BASE_DIR


class ProxyService:
    """代理管理服务"""

    def __init__(self):
        self.db_path = BASE_DIR / "db" / "database.db"

    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def get_proxies(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        获取代理列表

        Args:
            filters: 筛选条件
                - proxy_type: 代理类型
                - is_enabled: 是否启用

        Returns:
            代理列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM proxies WHERE 1=1"
            params = []

            if filters:
                if filters.get('proxy_type'):
                    query += " AND proxy_type = ?"
                    params.append(filters['proxy_type'])

                if filters.get('is_enabled') is not None:
                    query += " AND is_enabled = ?"
                    params.append(filters['is_enabled'])

            query += " ORDER BY create_time DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_proxies_paginated(self, filters: Optional[Dict] = None, limit: int = 50, offset: int = 0) -> Dict:
        """分页获取代理列表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            base = "FROM proxies WHERE 1=1"
            where = ""
            params = []

            if filters:
                if filters.get('proxy_type'):
                    where += " AND proxy_type = ?"
                    params.append(filters['proxy_type'])

                if filters.get('is_enabled') is not None:
                    where += " AND is_enabled = ?"
                    params.append(filters['is_enabled'])

            cursor.execute(f"SELECT COUNT(1) as cnt {base} {where}", params)
            total = int(cursor.fetchone()['cnt'])

            cursor.execute(
                f"SELECT * {base} {where} ORDER BY create_time DESC LIMIT ? OFFSET ?",
                params + [limit, offset],
            )
            rows = cursor.fetchall()

            items = [dict(row) for row in rows]
            return {"items": items, "total": total, "limit": limit, "offset": offset}
        finally:
            conn.close()

    def get_proxy_by_id(self, proxy_id: int) -> Optional[Dict]:
        """获取单个代理详情"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM proxies WHERE id = ?", (proxy_id,))
            row = cursor.fetchone()

            return dict(row) if row else None
        finally:
            conn.close()

    def create_proxy(self, data: Dict) -> int:
        """
        创建代理

        Args:
            data: 代理数据
                - proxy_name: 代理名称
                - proxy_type: 代理类型 (http/https/socks5)
                - host: 主机地址
                - port: 端口
                - username: 用户名（可选）
                - password: 密码（可选）
                - remark: 备注（可选）

        Returns:
            代理ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO proxies (
                    proxy_name, proxy_type, host, port,
                    username, password, remark, is_enabled
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                data['proxy_name'],
                data['proxy_type'],
                data['host'],
                data['port'],
                data.get('username'),
                data.get('password'),
                data.get('remark')
            ))

            proxy_id = cursor.lastrowid
            conn.commit()
            return proxy_id
        finally:
            conn.close()

    def update_proxy(self, proxy_id: int, data: Dict) -> bool:
        """
        更新代理信息

        Args:
            proxy_id: 代理ID
            data: 要更新的字段

        Returns:
            是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            updates = []
            params = []

            if 'proxy_name' in data:
                updates.append("proxy_name = ?")
                params.append(data['proxy_name'])

            if 'proxy_type' in data:
                updates.append("proxy_type = ?")
                params.append(data['proxy_type'])

            if 'host' in data:
                updates.append("host = ?")
                params.append(data['host'])

            if 'port' in data:
                updates.append("port = ?")
                params.append(data['port'])

            if 'username' in data:
                updates.append("username = ?")
                params.append(data['username'])

            if 'password' in data:
                updates.append("password = ?")
                params.append(data['password'])

            if 'remark' in data:
                updates.append("remark = ?")
                params.append(data['remark'])

            if 'is_enabled' in data:
                updates.append("is_enabled = ?")
                params.append(data['is_enabled'])

            if not updates:
                return False

            updates.append("update_time = CURRENT_TIMESTAMP")
            params.append(proxy_id)

            query = f"UPDATE proxies SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()

            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_proxy(self, proxy_id: int) -> bool:
        """删除代理"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM proxies WHERE id = ?", (proxy_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def batch_delete_proxies(self, proxy_ids: List[int]) -> int:
        """批量删除代理"""
        if not proxy_ids:
            return 0

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            placeholders = ','.join(['?'] * len(proxy_ids))
            cursor.execute(f"DELETE FROM proxies WHERE id IN ({placeholders})", proxy_ids)
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def get_proxy_by_account_id(self, account_id: int) -> Optional[Dict]:
        """通过账号ID获取关联的代理"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT p.* FROM proxies p
                INNER JOIN user_info u ON u.proxy_id = p.id
                WHERE u.id = ?
            """, (account_id,))

            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
