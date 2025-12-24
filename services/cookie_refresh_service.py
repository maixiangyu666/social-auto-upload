#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cookie刷新服务
负责自动刷新账号Cookie，避免过期
"""
import asyncio
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import List, Dict, Optional
from conf import BASE_DIR
from myUtils.auth import check_cookie
from services.account_service import AccountService
from services.login_service import LoginService


class CookieRefreshService:
    """Cookie刷新服务"""
    
    def __init__(self):
        self.account_service = AccountService()
        self.login_service = LoginService()
        self.db_path = BASE_DIR / "db" / "database.db"
    
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn
    
    def _log_refresh_result(self, account_id: int, platform_type: int, success: bool, 
                           error_message: str = None, duration_ms: int = None):
        """记录刷新结果到日志表"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO cookie_verification_log (
                    account_id, platform_type, verify_result, 
                    verify_method, error_message, duration_ms
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                account_id,
                platform_type,
                1 if success else 0,
                'auto_refresh',
                error_message,
                duration_ms
            ))
            conn.commit()
        finally:
            conn.close()
    
    async def refresh_account_cookie(self, account_id: int) -> Dict:
        """
        刷新单个账号Cookie
        
        Args:
            account_id: 账号ID
        
        Returns:
            刷新结果字典
                - success: 是否成功
                - message: 消息
                - new_file_path: 新的Cookie文件路径（如果成功）
        """
        account = self.account_service.get_account_by_id(account_id)
        if not account:
            return {
                'success': False,
                'message': '账号不存在'
            }
        
        platform_type = account['type']
        old_file_path = account['filePath']
        user_name = account['userName']
        
        start_time = datetime.now()
        status_queue = Queue()
        
        try:
            # 自动刷新：仅对扫码平台有意义（仍然需要扫码，通常用于“手动触发刷新”）
            if platform_type in (5, 6, 7):
                return {'success': False, 'message': '该平台需手动登录/上传Cookie，暂不支持自动刷新'}

            session_id = str(uuid.uuid4())
            result = await self.login_service.login_platform(
                int(platform_type),
                user_name,
                status_queue,
                account_id=account_id,
                session_id=session_id,
            )

            if not result.get('success'):
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                error_msg = result.get('message') or '登录超时或失败'
                self._log_refresh_result(account_id, platform_type, False, error_msg, duration_ms)
                return {'success': False, 'message': error_msg}

            new_file_path = result.get('filePath')
            if not new_file_path:
                return {'success': False, 'message': '无法获取新的Cookie文件路径'}

            # 再次验证（LoginService 已验证，这里做双保险）
            verify_result = await check_cookie(platform_type, new_file_path)
            if not verify_result:
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                error_msg = '新生成的Cookie验证失败'
                self._log_refresh_result(account_id, platform_type, False, error_msg, duration_ms)
                return {'success': False, 'message': error_msg}

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            self._log_refresh_result(account_id, platform_type, True, None, duration_ms)

            # 删除旧cookie文件（可选）
            old_file = BASE_DIR / "cookiesFile" / old_file_path
            if old_file.exists() and old_file_path != new_file_path:
                try:
                    old_file.unlink()
                except Exception:
                    pass

            return {'success': True, 'message': 'Cookie刷新成功', 'new_file_path': new_file_path}
        
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            error_msg = f'刷新过程出错: {str(e)}'
            self._log_refresh_result(account_id, platform_type, False, error_msg, duration_ms)
            return {
                'success': False,
                'message': error_msg
            }
    
    async def batch_refresh_cookies(self, account_ids: List[int]) -> Dict:
        """
        批量刷新Cookie
        
        Args:
            account_ids: 账号ID列表
        
        Returns:
            批量刷新结果
        """
        results = {
            'total': len(account_ids),
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        for account_id in account_ids:
            result = await self.refresh_account_cookie(account_id)
            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append({
                'account_id': account_id,
                **result
            })
        
        return results
    
    def get_accounts_need_refresh(self) -> List[Dict]:
        """
        获取需要刷新的账号列表（next_refresh_time <= NOW()）
        
        Returns:
            需要刷新的账号列表
        """
        return self.account_service.get_accounts_need_refresh()
    
    def schedule_refresh(self, account_id: int, interval_days: int = 7):
        """
        设置刷新计划
        
        Args:
            account_id: 账号ID
            interval_days: 刷新间隔（天）
        """
        self.account_service.update_account(account_id, {
            'auto_refresh_enabled': 1,
            'refresh_interval_days': interval_days
        })
        self.account_service.schedule_next_refresh(account_id)
    
    def cancel_refresh(self, account_id: int):
        """
        取消自动刷新
        
        Args:
            account_id: 账号ID
        """
        self.account_service.update_account(account_id, {
            'auto_refresh_enabled': 0,
            'next_refresh_time': None
        })

