#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分组管理服务
负责账号分组的CRUD操作
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from conf import BASE_DIR


class GroupService:
    """分组管理服务"""
    
    def __init__(self):
        self.db_path = BASE_DIR / "db" / "database.db"
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_groups(self) -> List[Dict]:
        """获取所有分组"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT g.*, COUNT(u.id) as account_count
                FROM account_groups g
                LEFT JOIN user_info u ON u.group_id = g.id
                GROUP BY g.id
                ORDER BY g.create_time ASC
            """)
            
            rows = cursor.fetchall()
            groups = []
            for row in rows:
                group = dict(row)
                groups.append(group)
            
            return groups
        finally:
            conn.close()
    
    def get_group_by_id(self, group_id: int) -> Optional[Dict]:
        """获取单个分组详情"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT g.*, COUNT(u.id) as account_count
                FROM account_groups g
                LEFT JOIN user_info u ON u.group_id = g.id
                WHERE g.id = ?
                GROUP BY g.id
            """, (group_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def create_group(self, data: Dict) -> int:
        """
        创建分组
        
        Args:
            data: 分组数据
                - name: 分组名称（必填）
                - description: 分组描述（可选）
                - color: 分组颜色（可选）
        
        Returns:
            分组ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO account_groups (name, description, color)
                VALUES (?, ?, ?)
            """, (
                data['name'],
                data.get('description'),
                data.get('color', '#94a3b8')  # 默认灰色
            ))
            
            group_id = cursor.lastrowid
            conn.commit()
            return group_id
        finally:
            conn.close()
    
    def update_group(self, group_id: int, data: Dict) -> bool:
        """
        更新分组
        
        Args:
            group_id: 分组ID
            data: 要更新的字段
        
        Returns:
            是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            updates = []
            params = []
            
            if 'name' in data:
                updates.append("name = ?")
                params.append(data['name'])
            
            if 'description' in data:
                updates.append("description = ?")
                params.append(data['description'])
            
            if 'color' in data:
                updates.append("color = ?")
                params.append(data['color'])
            
            if not updates:
                return False
            
            updates.append("update_time = CURRENT_TIMESTAMP")
            params.append(group_id)
            
            query = f"UPDATE account_groups SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def delete_group(self, group_id: int) -> bool:
        """
        删除分组
        
        注意：删除分组时，会将关联的账号的 group_id 设置为 NULL
        
        Returns:
            是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 先检查是否有账号使用此分组
            cursor.execute("SELECT COUNT(*) FROM user_info WHERE group_id = ?", (group_id,))
            account_count = cursor.fetchone()[0]
            
            if account_count > 0:
                # 将关联账号的 group_id 设置为 NULL
                cursor.execute("UPDATE user_info SET group_id = NULL WHERE group_id = ?", (group_id,))
            
            # 删除分组
            cursor.execute("DELETE FROM account_groups WHERE id = ?", (group_id,))
            conn.commit()
            
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def assign_account_to_group(self, account_id: int, group_id: Optional[int]) -> bool:
        """
        分配账号到分组
        
        Args:
            account_id: 账号ID
            group_id: 分组ID（None 表示取消分组）
        
        Returns:
            是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE user_info
                SET group_id = ?, update_time = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (group_id, account_id))
            
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def batch_assign_accounts(self, account_ids: List[int], group_id: Optional[int]) -> int:
        """
        批量分配账号到分组
        
        Args:
            account_ids: 账号ID列表
            group_id: 分组ID（None 表示取消分组）
        
        Returns:
            成功分配的账号数量
        """
        if not account_ids:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            placeholders = ','.join(['?'] * len(account_ids))
            params = [group_id] + account_ids
            
            cursor.execute(f"""
                UPDATE user_info
                SET group_id = ?, update_time = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders})
            """, params)
            
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()


