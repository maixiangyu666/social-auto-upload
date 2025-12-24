import asyncio
import json

from playwright.async_api import async_playwright

from myUtils.auth import check_cookie
from utils.base_social_media import set_init_script
import uuid
from pathlib import Path
from conf import BASE_DIR, LOCAL_CHROME_HEADLESS

# 抖音登录
async def douyin_cookie_gen(id, status_queue):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()
    async with async_playwright() as playwright:
        options = {
            'headless': LOCAL_CHROME_HEADLESS
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://creator.douyin.com/")
        original_url = page.url
        img_locator = page.get_by_role("img", name="二维码")
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        print("✅ 图片地址:", src)
        status_queue.put(json.dumps({"event": "qrcode", "img": src, "msg": "请扫码登录"}, ensure_ascii=False))
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)
        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            status_queue.put(json.dumps({"event": "error", "code": 500, "msg": "登录超时"}, ensure_ascii=False))
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(3, f"{uuid_v1}.json")
        if not result:
            status_queue.put(json.dumps({"event": "error", "code": 500, "msg": "Cookie验证失败"}, ensure_ascii=False))
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()
        status_queue.put(json.dumps({"event": "success", "code": 200, "msg": "登录成功"}, ensure_ascii=False))
        status_queue.put("200")
        return f"{uuid_v1}.json"


# 视频号登录
async def get_tencent_cookie(id, status_queue):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': LOCAL_CHROME_HEADLESS,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        # Pause the page, and start recording manually.
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://channels.weixin.qq.com")
        original_url = page.url

        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        # 等待 iframe 出现（最多等 60 秒）
        iframe_locator = page.frame_locator("iframe").first

        # 获取 iframe 中的第一个 img 元素
        img_locator = iframe_locator.get_by_role("img").first

        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        print("✅ 图片地址:", src)
        status_queue.put(json.dumps({"event": "qrcode", "img": src, "msg": "请扫码登录"}, ensure_ascii=False))

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put(json.dumps({"event": "error", "code": 500, "msg": "登录超时"}, ensure_ascii=False))
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(2,f"{uuid_v1}.json")
        if not result:
            status_queue.put(json.dumps({"event": "error", "code": 500, "msg": "Cookie验证失败"}, ensure_ascii=False))
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()
        status_queue.put(json.dumps({"event": "success", "code": 200, "msg": "登录成功"}, ensure_ascii=False))
        status_queue.put("200")
        return f"{uuid_v1}.json"

# 快手登录
async def get_ks_cookie(id, status_queue):
    url_changed_event = asyncio.Event()
    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()
    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': LOCAL_CHROME_HEADLESS,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://cp.kuaishou.com")

        # 定位并点击“立即登录”按钮（类型为 link）
        await page.get_by_role("link", name="立即登录").click()
        await page.get_by_text("扫码登录").click()
        img_locator = page.get_by_role("img", name="qrcode")
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        original_url = page.url
        print("✅ 图片地址:", src)
        status_queue.put(json.dumps({"event": "qrcode", "img": src, "msg": "请扫码登录"}, ensure_ascii=False))
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put(json.dumps({"event": "error", "code": 500, "msg": "登录超时"}, ensure_ascii=False))
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(4, f"{uuid_v1}.json")
        if not result:
            status_queue.put(json.dumps({"event": "error", "code": 500, "msg": "Cookie验证失败"}, ensure_ascii=False))
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()
        status_queue.put(json.dumps({"event": "success", "code": 200, "msg": "登录成功"}, ensure_ascii=False))
        status_queue.put("200")
        return f"{uuid_v1}.json"

# 小红书登录
async def xiaohongshu_cookie_gen(id, status_queue):
    url_changed_event = asyncio.Event()

    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'args': [
                '--lang en-GB'
            ],
            'headless': LOCAL_CHROME_HEADLESS,  # Set headless option here
        }
        # Make sure to run headed.
        browser = await playwright.chromium.launch(**options)
        # Setup context however you like.
        context = await browser.new_context()  # Pass any options
        context = await set_init_script(context)
        # Pause the page, and start recording manually.
        page = await context.new_page()
        await page.goto("https://creator.xiaohongshu.com/")
        await page.locator('img.css-wemwzq').click()

        img_locator = page.get_by_role("img").nth(2)
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        original_url = page.url
        print("✅ 图片地址:", src)
        status_queue.put(json.dumps({"event": "qrcode", "img": src, "msg": "请扫码登录"}, ensure_ascii=False))
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put(json.dumps({"event": "error", "code": 500, "msg": "登录超时"}, ensure_ascii=False))
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")
        # 确保cookiesFile目录存在
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(1, f"{uuid_v1}.json")
        if not result:
            status_queue.put(json.dumps({"event": "error", "code": 500, "msg": "Cookie验证失败"}, ensure_ascii=False))
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()
        status_queue.put(json.dumps({"event": "success", "code": 200, "msg": "登录成功"}, ensure_ascii=False))
        status_queue.put("200")
        return f"{uuid_v1}.json"


# ============================
# 手动登录（SSE）
# ============================

async def baijiahao_cookie_gen_with_sse(account_name, status_queue, *, session_id: str, confirm_event, timeout_sec: int = 600):
    """
    百家号手动登录（SSE）
    - 打开登录页（headless=False）
    - 等待前端 confirm 再保存 cookie
    """
    async with async_playwright() as playwright:
        options = {
            'args': ['--lang', 'en-GB'],
            'headless': False,
        }
        browser = await playwright.chromium.launch(**options)
        context = await browser.new_context()
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://baijiahao.baidu.com/builder/theme/bjh/login")

        status_queue.put(json.dumps({"event": "manual", "session_id": session_id, "msg": "百家号：请在打开的浏览器中完成登录，然后点击“已完成登录”。"}, ensure_ascii=False))

        # 等待确认
        loop = asyncio.get_running_loop()
        ok = await loop.run_in_executor(None, lambda: confirm_event.wait(timeout_sec))
        if not ok:
            await context.close()
            await browser.close()
            status_queue.put(json.dumps({"event": "error", "code": 500, "msg": "等待确认超时"}, ensure_ascii=False))
            return None

        uuid_v1 = uuid.uuid1()
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")

        result = await check_cookie(6, f"{uuid_v1}.json")
        await context.close()
        await browser.close()

        if not result:
            status_queue.put(json.dumps({"event": "error", "code": 500, "msg": "Cookie验证失败"}, ensure_ascii=False))
            return None

        status_queue.put(json.dumps({"event": "success", "code": 200, "msg": "登录成功"}, ensure_ascii=False))
        status_queue.put("200")
        return f"{uuid_v1}.json"


async def tiktok_cookie_gen_with_sse(account_name, status_queue, *, session_id: str, confirm_event, timeout_sec: int = 600):
    """
    TikTok 手动登录（SSE）
    """
    async with async_playwright() as playwright:
        options = {
            'args': ['--lang', 'en-GB'],
            'headless': False,
        }
        browser = await playwright.chromium.launch(**options)
        context = await browser.new_context()
        context = await set_init_script(context)
        page = await context.new_page()
        await page.goto("https://www.tiktok.com/login?lang=en")

        status_queue.put(json.dumps({"event": "manual", "session_id": session_id, "msg": "TikTok：请在打开的浏览器中完成登录，然后点击“已完成登录”。"}, ensure_ascii=False))

        loop = asyncio.get_running_loop()
        ok = await loop.run_in_executor(None, lambda: confirm_event.wait(timeout_sec))
        if not ok:
            await context.close()
            await browser.close()
            status_queue.put(json.dumps({"event": "error", "code": 500, "msg": "等待确认超时"}, ensure_ascii=False))
            return None

        uuid_v1 = uuid.uuid1()
        cookies_dir = Path(BASE_DIR / "cookiesFile")
        cookies_dir.mkdir(exist_ok=True)
        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")

        result = await check_cookie(7, f"{uuid_v1}.json")
        await context.close()
        await browser.close()

        if not result:
            status_queue.put(json.dumps({"event": "error", "code": 500, "msg": "Cookie验证失败"}, ensure_ascii=False))
            return None

        status_queue.put(json.dumps({"event": "success", "code": 200, "msg": "登录成功"}, ensure_ascii=False))
        status_queue.put("200")
        return f"{uuid_v1}.json"

# a = asyncio.run(xiaohongshu_cookie_gen(4,None))
# print(a)
