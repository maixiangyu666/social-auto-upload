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
from conf import BASE_DIR, LOCAL_CHROME_HEADLESS, LOCAL_CHROME_PATH
from myUtils.auth import check_cookie
from playwright.async_api import async_playwright
from utils.base_social_media import set_init_script
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
    
    def _log_refresh_result(
        self,
        account_id: int,
        platform_type: int,
        success: bool,
        error_message: str = None,
        duration_ms: int = None,
        verify_method: str = 'auto_refresh',
    ):
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
                verify_method,
                error_message,
                duration_ms
            ))
            conn.commit()
        finally:
            conn.close()

    async def refresh_account_cookie_background(self, account_id: int) -> Dict:
        """
        后台无感刷新：基于已有 cookie(storage_state) 启动 Playwright，访问平台页面后导出最新 storage_state 覆盖保存。
        - 若 cookie 已彻底失效，此方法通常无法自动恢复登录态，会返回失败并落日志，提示人工介入。
        """
        account = self.account_service.get_account_by_id(account_id)
        if not account:
            return {'success': False, 'message': '账号不存在'}

        platform_type = int(account['type'])
        cookie_name = account['filePath']
        cookie_file = Path(BASE_DIR / "cookiesFile" / cookie_name)

        start_time = datetime.now()
        try:
            if platform_type not in (1, 2, 3, 4):
                return {'success': False, 'message': '该平台暂不支持后台无感刷新（仅支持 1-4）'}

            if not cookie_name or not cookie_file.exists():
                msg = 'Cookie文件不存在'
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                self._log_refresh_result(account_id, platform_type, False, msg, duration_ms, verify_method='auto_refresh_background')
                return {'success': False, 'message': msg}

            refresh_url_map = {
                1: "https://creator.xiaohongshu.com/",
                2: "https://channels.weixin.qq.com",
                3: "https://creator.douyin.com/",
                4: "https://cp.kuaishou.com",
            }
            url = refresh_url_map.get(platform_type)

            async with async_playwright() as playwright:
                options = {
                    # 后台刷新强制 headless，避免在服务器/后台环境弹窗
                    "headless": True,
                }
                # 如果配置了本地 Chromium 路径则优先使用
                if LOCAL_CHROME_PATH and Path(LOCAL_CHROME_PATH).exists():
                    options["executable_path"] = LOCAL_CHROME_PATH
                browser = await playwright.chromium.launch(**options)
                context = await browser.new_context(storage_state=str(cookie_file))
                context = await set_init_script(context)
                page = await context.new_page()

                await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                # 给平台一点时间做重定向/刷新 token
                await page.wait_for_timeout(5_000)

                # 覆盖导出最新 cookie
                await context.storage_state(path=str(cookie_file))

                await page.close()
                await context.close()
                await browser.close()

            # 校验刷新后的 cookie 是否可用
            ok = await check_cookie(platform_type, cookie_name)
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            if ok:
                self._log_refresh_result(account_id, platform_type, True, None, duration_ms, verify_method='auto_refresh_background')
                self.account_service.update_verify_time(account_id, True)
                self.account_service.schedule_next_refresh(account_id)
                return {'success': True, 'message': '后台刷新成功', 'new_file_path': cookie_name}
            else:
                msg = '后台刷新后Cookie验证失败（可能需要人工重新登录）'
                self._log_refresh_result(account_id, platform_type, False, msg, duration_ms, verify_method='auto_refresh_background')
                self.account_service.update_verify_time(account_id, False)
                return {'success': False, 'message': msg}

        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            msg = f'后台刷新异常: {str(e)}'
            self._log_refresh_result(account_id, platform_type, False, msg, duration_ms, verify_method='auto_refresh_background')
            return {'success': False, 'message': msg}
    
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

    async def batch_refresh_cookies_background(self, account_ids: List[int], concurrency: int = 1) -> Dict:
        """批量后台无感刷新（并发受控）"""
        results = {'total': len(account_ids), 'success': 0, 'failed': 0, 'details': []}
        sem = asyncio.Semaphore(max(1, int(concurrency or 1)))

        async def run_one(aid: int):
            async with sem:
                return await self.refresh_account_cookie_background(aid)

        tasks = [asyncio.create_task(run_one(aid)) for aid in account_ids]
        done = await asyncio.gather(*tasks, return_exceptions=True)
        for aid, r in zip(account_ids, done):
            if isinstance(r, Exception):
                results['failed'] += 1
                results['details'].append({'account_id': aid, 'success': False, 'message': f'后台刷新异常: {str(r)}'})
                continue
            if r.get('success'):
                results['success'] += 1
            else:
                results['failed'] += 1
            results['details'].append({'account_id': aid, **r})

        return results

    def get_refresh_logs(self, account_id: int, limit: int = 50, offset: int = 0) -> Dict:
        """分页获取单账号刷新/验证日志"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(1) as cnt FROM cookie_verification_log WHERE account_id = ?",
                (account_id,),
            )
            total = int(cursor.fetchone()['cnt'])

            cursor.execute(
                """
                SELECT *
                FROM cookie_verification_log
                WHERE account_id = ?
                ORDER BY verify_time DESC
                LIMIT ? OFFSET ?
                """,
                (account_id, limit, offset),
            )
            rows = [dict(r) for r in cursor.fetchall()]
            return {"items": rows, "total": total, "limit": limit, "offset": offset}
        finally:
            conn.close()
    
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

