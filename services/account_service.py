#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
账号管理服务
负责账号的CRUD操作、统计、分组管理等
"""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from conf import BASE_DIR


class AccountService:
    """账号管理服务"""
    
    # 账号状态常量
    STATUS_INVALID = 0      # 无效
    STATUS_VALID = 1        # 有效
    STATUS_VERIFYING = 2    # 验证中
    
    def __init__(self):
        self.db_path = BASE_DIR / "db" / "database.db"
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_accounts(self, filters: Optional[Dict] = None) -> List[Dict]:
        """
        获取账号列表
        
        Args:
            filters: 筛选条件
                - platform_type: 平台类型
                - status: 状态
                - group_id: 分组ID
                - keyword: 关键词搜索（账号名、文件路径）
        
        Returns:
            账号列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            query = "SELECT * FROM user_info WHERE 1=1"
            params = []
            
            if filters:
                if filters.get('platform_type'):
                    query += " AND type = ?"
                    params.append(filters['platform_type'])
                
                if filters.get('status') is not None:
                    query += " AND status = ?"
                    params.append(filters['status'])
                
                if filters.get('group_id') is not None:
                    if filters['group_id'] == 0:  # 0 表示未分组
                        query += " AND (group_id IS NULL OR group_id = 0)"
                    else:
                        query += " AND group_id = ?"
                        params.append(filters['group_id'])
                
                if filters.get('keyword'):
                    keyword = f"%{filters['keyword']}%"
                    query += " AND (userName LIKE ? OR filePath LIKE ?)"
                    params.extend([keyword, keyword])
            
            query += " ORDER BY create_time DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            accounts = []
            for row in rows:
                account = dict(row)
                # 解析 tags JSON
                if account.get('tags'):
                    try:
                        account['tags'] = json.loads(account['tags'])
                    except:
                        account['tags'] = []
                else:
                    account['tags'] = []
                
                accounts.append(account)
            
            return accounts
        finally:
            conn.close()

    def count_accounts(self, filters: Optional[Dict] = None) -> int:
        """统计账号数量（与 get_accounts 同筛选条件）"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            query = "SELECT COUNT(1) as cnt FROM user_info WHERE 1=1"
            params = []

            if filters:
                if filters.get('platform_type'):
                    query += " AND type = ?"
                    params.append(filters['platform_type'])

                if filters.get('status') is not None:
                    query += " AND status = ?"
                    params.append(filters['status'])

                if filters.get('group_id') is not None:
                    if filters['group_id'] == 0:
                        query += " AND (group_id IS NULL OR group_id = 0)"
                    else:
                        query += " AND group_id = ?"
                        params.append(filters['group_id'])

                if filters.get('keyword'):
                    keyword = f"%{filters['keyword']}%"
                    query += " AND (userName LIKE ? OR filePath LIKE ?)"
                    params.extend([keyword, keyword])

            cursor.execute(query, params)
            row = cursor.fetchone()
            return int(row['cnt'] if row else 0)
        finally:
            conn.close()

    def get_accounts_paginated(self, filters: Optional[Dict] = None, limit: int = 50, offset: int = 0) -> Dict:
        """分页获取账号列表，返回 {items,total,limit,offset}"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            base = "FROM user_info WHERE 1=1"
            where = ""
            params = []

            if filters:
                if filters.get('platform_type'):
                    where += " AND type = ?"
                    params.append(filters['platform_type'])

                if filters.get('status') is not None:
                    where += " AND status = ?"
                    params.append(filters['status'])

                if filters.get('group_id') is not None:
                    if filters['group_id'] == 0:
                        where += " AND (group_id IS NULL OR group_id = 0)"
                    else:
                        where += " AND group_id = ?"
                        params.append(filters['group_id'])

                if filters.get('keyword'):
                    keyword = f"%{filters['keyword']}%"
                    where += " AND (userName LIKE ? OR filePath LIKE ?)"
                    params.extend([keyword, keyword])

            cursor.execute(f"SELECT COUNT(1) as cnt {base} {where}", params)
            total = int(cursor.fetchone()['cnt'])

            cursor.execute(
                f"SELECT * {base} {where} ORDER BY create_time DESC LIMIT ? OFFSET ?",
                params + [limit, offset],
            )
            rows = cursor.fetchall()

            items = []
            for row in rows:
                account = dict(row)
                if account.get('tags'):
                    try:
                        account['tags'] = json.loads(account['tags'])
                    except Exception:
                        account['tags'] = []
                else:
                    account['tags'] = []
                items.append(account)

            return {"items": items, "total": total, "limit": limit, "offset": offset}
        finally:
            conn.close()
    
    def get_account_by_id(self, account_id: int) -> Optional[Dict]:
        """获取单个账号详情"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM user_info WHERE id = ?", (account_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            account = dict(row)
            # 解析 tags JSON
            if account.get('tags'):
                try:
                    account['tags'] = json.loads(account['tags'])
                except:
                    account['tags'] = []
            else:
                account['tags'] = []
            
            return account
        finally:
            conn.close()
    
    def create_account(self, data: Dict) -> int:
        """
        创建账号
        
        Args:
            data: 账号数据
                - type: 平台类型
                - filePath: Cookie文件路径
                - userName: 账号名称
                - group_id: 分组ID（可选）
                - tags: 标签列表（可选）
                - auto_refresh_enabled: 是否启用自动刷新（默认1）
                - refresh_interval_days: 刷新间隔天数（默认7）
        
        Returns:
            账号ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 计算下次刷新时间
            next_refresh_time = None
            if data.get('auto_refresh_enabled', 1):
                interval_days = data.get('refresh_interval_days', 7)
                next_refresh_time = datetime.now() + timedelta(days=interval_days)
            
            # 处理 tags
            tags_json = json.dumps(data.get('tags', [])) if data.get('tags') else None
            
            cursor.execute("""
                INSERT INTO user_info (
                    type, filePath, userName, status,
                    group_id, tags,
                    auto_refresh_enabled, refresh_interval_days, next_refresh_time,
                    publish_count, success_count, fail_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['type'],
                data['filePath'],
                data['userName'],
                data.get('status', self.STATUS_INVALID),
                data.get('group_id'),
                tags_json,
                data.get('auto_refresh_enabled', 1),
                data.get('refresh_interval_days', 7),
                next_refresh_time.strftime('%Y-%m-%d %H:%M:%S') if next_refresh_time else None,
                0, 0, 0
            ))
            
            account_id = cursor.lastrowid
            conn.commit()
            return account_id
        finally:
            conn.close()
    
    def update_account(self, account_id: int, data: Dict) -> bool:
        """
        更新账号信息
        
        Args:
            account_id: 账号ID
            data: 要更新的字段
        
        Returns:
            是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 构建更新语句
            updates = []
            params = []
            
            if 'type' in data:
                updates.append("type = ?")
                params.append(data['type'])
            
            if 'filePath' in data:
                updates.append("filePath = ?")
                params.append(data['filePath'])
            
            if 'userName' in data:
                updates.append("userName = ?")
                params.append(data['userName'])
            
            if 'status' in data:
                updates.append("status = ?")
                params.append(data['status'])
            
            if 'group_id' in data:
                updates.append("group_id = ?")
                params.append(data['group_id'])
            
            if 'tags' in data:
                tags_json = json.dumps(data['tags']) if data['tags'] else None
                updates.append("tags = ?")
                params.append(tags_json)
            
            if 'auto_refresh_enabled' in data:
                updates.append("auto_refresh_enabled = ?")
                params.append(data['auto_refresh_enabled'])
                
                # 如果启用自动刷新，更新下次刷新时间
                if data['auto_refresh_enabled']:
                    interval_days = data.get('refresh_interval_days', 7)
                    next_refresh_time = datetime.now() + timedelta(days=interval_days)
                    updates.append("next_refresh_time = ?")
                    params.append(next_refresh_time.strftime('%Y-%m-%d %H:%M:%S'))
            
            if 'refresh_interval_days' in data:
                updates.append("refresh_interval_days = ?")
                params.append(data['refresh_interval_days'])
                
                # 如果已启用自动刷新，更新下次刷新时间
                cursor.execute("SELECT auto_refresh_enabled FROM user_info WHERE id = ?", (account_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    next_refresh_time = datetime.now() + timedelta(days=data['refresh_interval_days'])
                    updates.append("next_refresh_time = ?")
                    params.append(next_refresh_time.strftime('%Y-%m-%d %H:%M:%S'))
            
            if 'remark' in data:
                updates.append("remark = ?")
                params.append(data['remark'])
            
            if not updates:
                return False
            
            updates.append("update_time = CURRENT_TIMESTAMP")
            params.append(account_id)
            
            query = f"UPDATE user_info SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def delete_account(self, account_id: int) -> bool:
        """删除账号"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM user_info WHERE id = ?", (account_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def batch_delete_accounts(self, account_ids: List[int]) -> int:
        """批量删除账号"""
        if not account_ids:
            return 0
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            placeholders = ','.join(['?'] * len(account_ids))
            cursor.execute(f"DELETE FROM user_info WHERE id IN ({placeholders})", account_ids)
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
    
    def get_account_statistics(self, account_id: int) -> Dict:
        """
        获取账号统计信息
        
        Returns:
            统计信息字典
        """
        account = self.get_account_by_id(account_id)
        if not account:
            return {}
        
        # 从账号记录中获取统计
        publish_count = account.get('publish_count', 0)
        success_count = account.get('success_count', 0)
        fail_count = account.get('fail_count', 0)
        
        # 计算成功率
        success_rate = 0
        if publish_count > 0:
            success_rate = round((success_count / publish_count) * 100, 2)
        
        # 从发布历史表获取最近的使用记录
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 最近5次发布记录
            cursor.execute("""
                SELECT status, publish_time, error_message
                FROM publish_history
                WHERE account_id = ?
                ORDER BY publish_time DESC
                LIMIT 5
            """, (account_id,))
            recent_history = [dict(row) for row in cursor.fetchall()]
            
            # Cookie验证历史
            cursor.execute("""
                SELECT verify_result, verify_time, verify_method, error_message
                FROM cookie_verification_log
                WHERE account_id = ?
                ORDER BY verify_time DESC
                LIMIT 5
            """, (account_id,))
            verify_history = [dict(row) for row in cursor.fetchall()]
            
            return {
                'publish_count': publish_count,
                'success_count': success_count,
                'fail_count': fail_count,
                'success_rate': success_rate,
                'last_used_time': account.get('last_used_time'),
                'last_verify_time': account.get('last_verify_time'),
                'next_refresh_time': account.get('next_refresh_time'),
                'recent_history': recent_history,
                'verify_history': verify_history
            }
        finally:
            conn.close()
    
    def update_account_usage(self, account_id: int, success: bool):
        """
        更新账号使用统计（发布任务成功/失败时调用）
        
        Args:
            account_id: 账号ID
            success: 是否成功
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if success:
                cursor.execute("""
                    UPDATE user_info
                    SET publish_count = publish_count + 1,
                        success_count = success_count + 1,
                        last_used_time = ?,
                        update_time = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (now, account_id))
            else:
                cursor.execute("""
                    UPDATE user_info
                    SET publish_count = publish_count + 1,
                        fail_count = fail_count + 1,
                        last_used_time = ?,
                        update_time = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (now, account_id))
            
            conn.commit()
        finally:
            conn.close()
    
    def update_verify_time(self, account_id: int, verify_result: bool):
        """
        更新验证时间
        
        Args:
            account_id: 账号ID
            verify_result: 验证结果
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            status = self.STATUS_VALID if verify_result else self.STATUS_INVALID
            
            cursor.execute("""
                UPDATE user_info
                SET status = ?,
                    last_verify_time = ?,
                    verify_count = verify_count + 1,
                    update_time = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, now, account_id))
            
            conn.commit()
        finally:
            conn.close()
    
    def get_accounts_need_refresh(self) -> List[Dict]:
        """
        获取需要刷新的账号列表（next_refresh_time <= NOW()）
        
        Returns:
            需要刷新的账号列表
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                SELECT * FROM user_info
                WHERE auto_refresh_enabled = 1
                  AND next_refresh_time IS NOT NULL
                  AND next_refresh_time <= ?
                ORDER BY next_refresh_time ASC
            """, (now,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def schedule_next_refresh(self, account_id: int):
        """
        安排下次刷新时间（刷新完成后调用）
        
        Args:
            account_id: 账号ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 获取刷新间隔
            cursor.execute("SELECT refresh_interval_days FROM user_info WHERE id = ?", (account_id,))
            row = cursor.fetchone()
            
            if row and row[0]:
                interval_days = row[0]
                next_refresh_time = datetime.now() + timedelta(days=interval_days)
                
                cursor.execute("""
                    UPDATE user_info
                    SET next_refresh_time = ?,
                        update_time = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (next_refresh_time.strftime('%Y-%m-%d %H:%M:%S'), account_id))
                
                conn.commit()
        finally:
            conn.close()


