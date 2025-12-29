import playwright
from playwright.async_api import Playwright, async_playwright, Page
import os
import asyncio

from conf import LOCAL_CHROME_PATH, LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script
from utils.log import douyin_logger

browser =  playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)
context =  browser.new_context(storage_state=account_file)
context =  set_init_script(context)
# 创建一个新的页面
page =  context.new_page()
# 访问指定的 URL
 page.goto("https://creator.douyin.com/creator-micro/content/upload")