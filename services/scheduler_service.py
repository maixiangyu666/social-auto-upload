#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
定时任务服务
负责定期执行Cookie刷新等定时任务
"""
import threading
import time
import asyncio
import os
from datetime import datetime, timedelta
from typing import Optional
from services.cookie_refresh_service import CookieRefreshService
from services.account_service import AccountService


class SchedulerService:
    """定时任务服务"""
    
    def __init__(self):
        self.cookie_refresh_service = CookieRefreshService()
        self.account_service = AccountService()
        self._running = False
        self._refresh_thread: Optional[threading.Thread] = None
    
    def start_cookie_refresh_scheduler(self):
        """启动Cookie刷新定时任务"""
        if self._running:
            print("⚠️ Cookie刷新定时任务已在运行")
            return
        
        self._running = True
        self._refresh_thread = threading.Thread(
            target=self._refresh_scheduler_loop,
            daemon=True,
            name="CookieRefreshScheduler"
        )
        self._refresh_thread.start()
        print("✅ Cookie刷新定时任务已启动")
    
    def stop_cookie_refresh_scheduler(self):
        """停止Cookie刷新定时任务"""
        self._running = False
        if self._refresh_thread:
            self._refresh_thread.join(timeout=5)
        print("✅ Cookie刷新定时任务已停止")
    
    def _refresh_scheduler_loop(self):
        """Cookie刷新调度循环（可配置间隔）"""
        interval_seconds = int(os.environ.get("COOKIE_REFRESH_CHECK_INTERVAL_SECONDS", "600"))
        concurrency = int(os.environ.get("COOKIE_REFRESH_CONCURRENCY", "1"))
        while self._running:
            try:
                print(f"🔄 Cookie刷新检查开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (interval={interval_seconds}s, concurrency={concurrency})")
                self.refresh_expired_cookies(concurrency=concurrency)

                # 休眠到下一轮（支持提前停止）
                slept = 0
                while self._running and slept < interval_seconds:
                    time.sleep(min(1, interval_seconds - slept))
                    slept += 1
                
            except Exception as e:
                print(f"❌ Cookie刷新调度器出错: {e}")
                # 出错后等待一小段时间再继续，避免打爆日志
                time.sleep(30)
    
    def refresh_expired_cookies(self, concurrency: int = 1):
        """
        检查并刷新过期Cookie（每日执行）
        在定时任务中调用
        """
        try:
            # 获取需要刷新的账号列表
            accounts = self.cookie_refresh_service.get_accounts_need_refresh()
            
            if not accounts:
                print("✅ 没有需要刷新的账号")
                return
            
            print(f"📋 发现 {len(accounts)} 个账号需要刷新Cookie")
            
            # 使用asyncio运行异步刷新任务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def refresh_all():
                return await self.cookie_refresh_service.batch_refresh_cookies_background(
                    [acc['id'] for acc in accounts],
                    concurrency=concurrency,
                )
            
            results = loop.run_until_complete(refresh_all())
            loop.close()
            
            print(f"✅ Cookie刷新完成: 成功 {results['success']} 个, 失败 {results['failed']} 个")
            
        except Exception as e:
            print(f"❌ 刷新过期Cookie时出错: {e}")
    
    def notify_cookie_expiring(self):
        """
        通知即将过期的Cookie（提前1-2天）
        在定时任务中调用
        """
        try:
            # 查询 next_refresh_time <= NOW() + 2天 的账号
            conn = self.account_service._get_connection()
            cursor = conn.cursor()
            
            try:
                two_days_later = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("""
                    SELECT id, userName, platform_name, next_refresh_time
                    FROM user_info
                    WHERE auto_refresh_enabled = 1
                      AND next_refresh_time IS NOT NULL
                      AND next_refresh_time <= ?
                      AND next_refresh_time > datetime('now')
                    ORDER BY next_refresh_time ASC
                """, (two_days_later,))
                
                accounts = [dict(row) for row in cursor.fetchall()]
                
                if accounts:
                    print(f"⚠️ 发现 {len(accounts)} 个账号的Cookie即将过期（2天内）:")
                    for acc in accounts:
                        print(f"  - {acc['userName']} ({acc['platform_name']}): {acc['next_refresh_time']}")
                else:
                    print("✅ 没有即将过期的Cookie")
            
            finally:
                conn.close()
        
        except Exception as e:
            print(f"❌ 检查即将过期的Cookie时出错: {e}")

