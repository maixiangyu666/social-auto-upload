#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一登录服务
将各平台登录方式统一抽象，供 /login SSE、REST、Cookie刷新复用
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
import uuid
from dataclasses import dataclass
from queue import Queue
from typing import Dict, Optional, Tuple

from services.account_service import AccountService
from myUtils.auth import check_cookie
from myUtils.login import (
    douyin_cookie_gen,
    get_tencent_cookie,
    get_ks_cookie,
    xiaohongshu_cookie_gen,
    baijiahao_cookie_gen_with_sse,
    tiktok_cookie_gen_with_sse,
)


@dataclass
class ManualLoginSession:
    session_id: str
    event: threading.Event
    created_at: float


class LoginService:
    """
    统一登录服务
    - 支持 1-7 平台
    - SSE/REST 可复用同一套登录逻辑
    - 手动登录场景通过 session_id + confirm 接口继续执行
    """

    def __init__(self):
        self.account_service = AccountService()
        # session_id -> ManualLoginSession
        self._manual_sessions: Dict[str, ManualLoginSession] = {}
        self._lock = threading.Lock()

    # ---------------------------
    # Manual login session
    # ---------------------------
    def create_manual_session(self) -> ManualLoginSession:
        return self.create_manual_session_with_id(str(uuid.uuid4()))

    def create_manual_session_with_id(self, session_id: str) -> ManualLoginSession:
        sess = ManualLoginSession(session_id=session_id, event=threading.Event(), created_at=time.time())
        with self._lock:
            # 覆盖同名 session（以最后一次为准）
            self._manual_sessions[session_id] = sess
        return sess

    def confirm_manual_session(self, session_id: str) -> bool:
        with self._lock:
            sess = self._manual_sessions.get(session_id)
        if not sess:
            return False
        sess.event.set()
        return True

    def cleanup_manual_session(self, session_id: str):
        with self._lock:
            self._manual_sessions.pop(session_id, None)

    async def _wait_manual_confirm(self, evt: threading.Event, timeout_sec: int) -> bool:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: evt.wait(timeout_sec))

    # ---------------------------
    # Public API
    # ---------------------------
    async def login_platform(
        self,
        platform_type: int,
        account_name: str,
        status_queue: Queue,
        *,
        account_id: Optional[int] = None,
        session_id: Optional[str] = None,
    ) -> Dict:
        """
        统一登录入口

        Args:
            platform_type: 平台类型 (1-7)
            account_name: 账号名称（自定义）
            status_queue: SSE/状态队列
            account_id: 传入则更新该账号（刷新Cookie）
            session_id: 手动登录用会话ID（6/7），由外部生成并用于 confirm
        """

        def push(payload: Dict):
            # 统一以 JSON 字符串推送，前端可解析
            status_queue.put(json.dumps(payload, ensure_ascii=False))

        push({"event": "start", "platform_type": platform_type, "account_name": account_name, "session_id": session_id})

        cookie_file: Optional[str] = None
        manual_sess: Optional[ManualLoginSession] = None

        try:
            if platform_type in (1, 2, 3, 4):
                # 二维码扫码：登录函数会推送二维码信息到队列，并在成功后返回 cookie 文件名
                if platform_type == 1:
                    cookie_file = await xiaohongshu_cookie_gen(account_name, status_queue)
                elif platform_type == 2:
                    cookie_file = await get_tencent_cookie(account_name, status_queue)
                elif platform_type == 3:
                    cookie_file = await douyin_cookie_gen(account_name, status_queue)
                elif platform_type == 4:
                    cookie_file = await get_ks_cookie(account_name, status_queue)

            elif platform_type in (6, 7):
                # 手动登录：需要前端 confirm 才继续
                if not session_id:
                    manual_sess = self.create_manual_session()
                    session_id = manual_sess.session_id
                else:
                    manual_sess = self.create_manual_session_with_id(session_id)

                push(
                    {
                        "event": "manual_required",
                        "session_id": session_id,
                        "msg": "已打开浏览器，请手动完成登录，然后在前端点击“已完成登录”继续。",
                    }
                )

                if platform_type == 6:
                    cookie_file = await baijiahao_cookie_gen_with_sse(
                        account_name, status_queue, session_id=session_id, confirm_event=manual_sess.event
                    )
                else:
                    cookie_file = await tiktok_cookie_gen_with_sse(
                        account_name, status_queue, session_id=session_id, confirm_event=manual_sess.event
                    )

            elif platform_type == 5:
                # Cookie 上传：由 /uploadCookie 处理，这里只做兜底
                push({"event": "error", "msg": "Bilibili 请使用 Cookie 文件上传方式。", "code": 400})
                return {"success": False, "message": "cookie upload required"}

            else:
                push({"event": "error", "msg": f"不支持的平台类型: {platform_type}", "code": 400})
                return {"success": False, "message": "unsupported platform"}

            if not cookie_file:
                push({"event": "error", "msg": "登录失败/超时", "code": 500})
                return {"success": False, "message": "login failed"}

            # 校验 cookie
            ok = await check_cookie(platform_type, cookie_file)
            if not ok:
                push({"event": "error", "msg": "Cookie 验证失败", "code": 500})
                return {"success": False, "message": "cookie invalid"}

            # 写入/更新账号（统一走 AccountService）
            if account_id:
                self.account_service.update_account(account_id, {"filePath": cookie_file, "status": AccountService.STATUS_VALID})
                self.account_service.update_verify_time(account_id, True)
                self.account_service.schedule_next_refresh(account_id)
                push({"event": "success", "code": 200, "msg": "刷新 Cookie 成功", "account_id": account_id, "filePath": cookie_file})
                return {"success": True, "account_id": account_id, "filePath": cookie_file}

            new_id = self.account_service.create_account(
                {
                    "type": platform_type,
                    "filePath": cookie_file,
                    "userName": account_name,
                    "status": AccountService.STATUS_VALID,
                }
            )
            self.account_service.update_verify_time(new_id, True)
            self.account_service.schedule_next_refresh(new_id)
            push({"event": "success", "code": 200, "msg": "登录成功", "account_id": new_id, "filePath": cookie_file})
            return {"success": True, "account_id": new_id, "filePath": cookie_file}

        finally:
            if session_id:
                self.cleanup_manual_session(session_id)


