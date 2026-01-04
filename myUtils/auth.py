import asyncio
import configparser
import os
import json

from playwright.async_api import async_playwright
from xhs import XhsClient

from conf import BASE_DIR, LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script
from utils.log import tencent_logger, kuaishou_logger, douyin_logger
from pathlib import Path
from uploader.xhs_uploader.main import sign_local
from uploader.baijiahao_uploader.main import cookie_auth as cookie_auth_baijiahao
from uploader.tk_uploader.main_chrome import cookie_auth as cookie_auth_tiktok


async def cookie_auth_douyin(account_file, account_id=None):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)

        # 获取代理配置（如果有关联的代理）
        proxy_config = None
        if account_id:
            from myUtils.proxy_helper import get_proxy_config_dict
            proxy_config = get_proxy_config_dict(account_id)

        context_config = {"storage_state": str(account_file)}
        if proxy_config:
            context_config["proxy"] = proxy_config
            print(f"[Douyin Auth] Using proxy: {proxy_config}")

        context = await browser.new_context(**context_config)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        try:
            await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload", timeout=5000)
            # 2024.06.17 抖音创作者中心改版
            # 判断
            # 等待“扫码登录”元素出现，超时 5 秒（如果 5 秒没出现，说明 cookie 有效）
            try:
                await page.get_by_text("扫码登录").wait_for(timeout=5000)
                douyin_logger.error("[+] cookie 失效，需要扫码登录")
                return False
            except:
                douyin_logger.success("[+]  cookie 有效")
                return True
        except:
            douyin_logger.error("[+] 等待5秒 cookie 失效")
            await context.close()
            await browser.close()
            return False


async def cookie_auth_tencent(account_file, account_id=None):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)

        # 获取代理配置（如果有关联的代理）
        proxy_config = None
        if account_id:
            from myUtils.proxy_helper import get_proxy_config_dict
            proxy_config = get_proxy_config_dict(account_id)

        context_config = {"storage_state": str(account_file)}
        if proxy_config:
            context_config["proxy"] = proxy_config
            print(f"[Tencent Auth] Using proxy: {proxy_config}")

        context = await browser.new_context(**context_config)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://channels.weixin.qq.com/platform/post/create")
        try:
            await page.wait_for_selector('div.title-name:has-text("微信小店")', timeout=5000)  # 等待5秒
            tencent_logger.error("[+] 等待5秒 cookie 失效")
            return False
        except:
            tencent_logger.success("[+] cookie 有效")
            return True


async def cookie_auth_ks(account_file, account_id=None):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)

        # 获取代理配置（如果有关联的代理）
        proxy_config = None
        if account_id:
            from myUtils.proxy_helper import get_proxy_config_dict
            proxy_config = get_proxy_config_dict(account_id)

        context_config = {"storage_state": str(account_file)}
        if proxy_config:
            context_config["proxy"] = proxy_config
            print(f"[Kuaishou Auth] Using proxy: {proxy_config}")

        context = await browser.new_context(**context_config)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://cp.kuaishou.com/article/publish/video")
        try:
            await page.wait_for_selector("div.names div.container div.name:text('机构服务')", timeout=5000)  # 等待5秒

            kuaishou_logger.info("[+] 等待5秒 cookie 失效")
            return False
        except:
            kuaishou_logger.success("[+] cookie 有效")
            return True


async def cookie_auth_xhs(account_file, account_id=None):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)

        # 获取代理配置（如果有关联的代理）
        proxy_config = None
        if account_id:
            from myUtils.proxy_helper import get_proxy_config_dict
            proxy_config = get_proxy_config_dict(account_id)

        context_config = {"storage_state": str(account_file)}
        if proxy_config:
            context_config["proxy"] = proxy_config
            print(f"[Xiaohongshu Auth] Using proxy: {proxy_config}")

        context = await browser.new_context(**context_config)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.xiaohongshu.com/publish/publish?from=menu&target=video")
        try:
            await page.wait_for_url("https://creator.xiaohongshu.com/publish/publish?from=menu&target=video", timeout=5000)
        except:
            print("[+] 等待5秒 cookie 失效")
            await context.close()
            await browser.close()
            return False
        # 2024.06.17 抖音创作者中心改版
        if await page.get_by_text('手机号登录').count() or await page.get_by_text('扫码登录').count():
            print("[+] 等待5秒 cookie 失效")
            return False
        else:
            print("[+] cookie 有效")
            return True


async def check_cookie(type, file_path, account_id=None):
    match type:
        # 小红书
        case 1:
            return await cookie_auth_xhs(Path(BASE_DIR / "cookiesFile" / file_path), account_id)
        # 视频号
        case 2:
            return await cookie_auth_tencent(Path(BASE_DIR / "cookiesFile" / file_path), account_id)
        # 抖音
        case 3:
            return await cookie_auth_douyin(Path(BASE_DIR / "cookiesFile" / file_path), account_id)
        # 快手
        case 4:
            return await cookie_auth_ks(Path(BASE_DIR / "cookiesFile" / file_path), account_id)
        # Bilibili（Cookie上传：做基本结构校验）
        case 5:
            try:
                p = Path(BASE_DIR / "cookiesFile" / file_path)
                data = json.loads(p.read_text(encoding="utf-8"))
                # 兼容两种常见格式：
                # 1) biliup 导出的 {"cookie_info": {"cookies":[{"name":"SESSDATA","value":"..."}, ...]}, ...}
                # 2) 简单 key-value dict {"SESSDATA":"...", ...}
                if isinstance(data, dict) and "SESSDATA" in data:
                    return True
                cookies = (data.get("cookie_info", {}) or {}).get("cookies", []) if isinstance(data, dict) else []
                if isinstance(cookies, list) and any(c.get("name") == "SESSDATA" and c.get("value") for c in cookies if isinstance(c, dict)):
                    return True
                return False
            except Exception:
                return False
        # 百家号
        case 6:
            try:
                return await cookie_auth_baijiahao(str(Path(BASE_DIR / "cookiesFile" / file_path)))
            except Exception:
                return False
        # TikTok
        case 7:
            try:
                return await cookie_auth_tiktok(str(Path(BASE_DIR / "cookiesFile" / file_path)))
            except Exception:
                return False
        case _:
            return False

# a = asyncio.run(check_cookie(1,"3a6cfdc0-3d51-11f0-8507-44e51723d63c.json"))
# print(a)
