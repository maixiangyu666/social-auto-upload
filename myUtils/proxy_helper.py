#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
代理辅助工具
用于获取账号关联的代理配置，并转换为 Playwright 可用的代理格式
"""
import sqlite3
from pathlib import Path
from typing import Optional, Dict
from conf import BASE_DIR


def get_proxy_by_id(proxy_id: int) -> Optional[Dict]:
    """
    通过代理ID获取代理配置

    Args:
        proxy_id: 代理ID

    Returns:
        代理配置字典，如果代理不存在或未启用则返回 None
        {
            'server': 'http://proxy.example.com:8080',
            'username': 'user',  # 可选
            'password': 'pass'   # 可选
        }
    """
    db_path = BASE_DIR / "db" / "database.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 直接查询代理
        cursor.execute("""
            SELECT * FROM proxies
            WHERE id = ? AND is_enabled = 1
        """, (proxy_id,))

        proxy_row = cursor.fetchone()

        if not proxy_row:
            print(f"[Proxy] Proxy {proxy_id} not found or disabled")
            return None

        proxy = dict(proxy_row)

        # 构建 Playwright 代理配置
        proxy_type = proxy['proxy_type']
        server = f"{proxy_type}://{proxy['host']}:{proxy['port']}"

        config = {
            'server': server
        }

        # 添加认证信息（如果有）
        if proxy.get('username') and proxy.get('password'):
            config['username'] = proxy['username']
            config['password'] = proxy['password']

        print(f"[Proxy] Using proxy by ID: {config}")
        return config

    finally:
        conn.close()


def get_proxy_by_account_id(account_id: int) -> Optional[Dict]:
    """
    通��账号ID获取代理配置

    Args:
        account_id: 账号ID

    Returns:
        代理配置字典，如果没有关联代理则返回 None
        {
            'server': 'http://proxy.example.com:8080',
            'username': 'user',  # 可选
            'password': 'pass'   # 可选
        }
    """
    db_path = BASE_DIR / "db" / "database.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 查询账号关联的代理
        cursor.execute("""
            SELECT p.* FROM proxies p
            INNER JOIN user_info u ON u.proxy_id = p.id
            WHERE u.id = ? AND p.is_enabled = 1
        """, (account_id,))

        proxy_row = cursor.fetchone()

        if not proxy_row:
            return None

        proxy = dict(proxy_row)

        # 构建 Playwright 代理配置
        proxy_type = proxy['proxy_type']
        server = f"{proxy_type}://{proxy['host']}:{proxy['port']}"
        
        config = {
            'server': server
        }

        # 添加认证信息（如果有）
        if proxy.get('username') and proxy.get('password'):
            config['username'] = proxy['username']
            config['password'] = proxy['password']
        return config

    finally:
        conn.close()


def get_proxy_config_dict(account_id: int) -> Optional[Dict]:
    """
    获取账号的代理配置（用于 browser.new_context 的 proxy 参数）

    Args:
        account_id: 账号ID

    Returns:
        代理配置字典或 None
    """
    return get_proxy_by_account_id(account_id)
