# -*- coding: utf-8 -*-
from datetime import datetime
from pathlib import Path

from playwright.async_api import Playwright, async_playwright, Page
import os
import asyncio

from conf import LOCAL_CHROME_PATH, LOCAL_CHROME_HEADLESS
from utils.base_social_media import set_init_script
from utils.log import douyin_logger


async def cookie_auth(account_file):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=LOCAL_CHROME_HEADLESS)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        try:
            await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload", timeout=5000)
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


async def douyin_setup(account_file, handle=False):
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            # Todo alert message
            return False
        douyin_logger.info('[+] cookie文件不存在或已失效，即将自动打开浏览器，请扫码登录，登陆后会自动生成cookie文件')
        await douyin_cookie_gen(account_file)
    return True


async def douyin_cookie_gen(account_file):
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
        await page.pause()
        # 点击调试器的继续，保存cookie
        await context.storage_state(path=account_file)


class DouYinVideo(object):
    def __init__(self, title, file_path, tags, publish_date: datetime, account_file, thumbnail_path=None, productLink='', productTitle='', account_id=None):
        self.title = title  # 视频标题
        self.file_path = file_path
        self.tags = tags
        self.publish_date = publish_date
        self.account_file = account_file
        self.account_id = account_id
        self.date_format = '%Y年%m月%d日 %H:%M'
        self.local_executable_path = LOCAL_CHROME_PATH
        self.headless = LOCAL_CHROME_HEADLESS
        self.thumbnail_path = thumbnail_path
        self.productLink = productLink
        self.productTitle = productTitle

    async def set_schedule_time_douyin(self, page, publish_date):
        # 选择包含特定文本内容的 label 元素
        label_element = page.locator("[class^='radio']:has-text('定时发布')")
        # 在选中的 label 元素下点击 checkbox
        await label_element.click()
        await asyncio.sleep(1)
        publish_date_hour = publish_date.strftime("%Y-%m-%d %H:%M")

        await asyncio.sleep(1)
        await page.locator('.semi-input[placeholder="日期和时间"]').click()
        await page.keyboard.press("Control+KeyA")
        await page.keyboard.type(str(publish_date_hour))
        await page.keyboard.press("Enter")

        await asyncio.sleep(1)

    async def handle_upload_error(self, page):
        douyin_logger.info('视频出错了，重新上传中')
        await page.locator('div.progress-div [class^="upload-btn-input"]').set_input_files(self.file_path)

    async def upload(self, playwright: Playwright) -> None:
        # 使用 Chromium 浏览器启动一个浏览器实例
        if self.local_executable_path:
            browser = await playwright.chromium.launch(headless=self.headless, executable_path=self.local_executable_path)
        else:
            browser = await playwright.chromium.launch(headless=self.headless)

        # 确保 account_file 是绝对路径字符串
        account_file_path = str(Path(self.account_file).resolve())

        # 检查文件是否存在
        if not Path(account_file_path).exists():
            douyin_logger.error(f'[!] Cookie 文件不存在: {account_file_path}')
            await browser.close()
            raise FileNotFoundError(f'Cookie 文件不存在: {account_file_path}')

        douyin_logger.info(f'[+] 使用 Cookie 文件: {account_file_path}')

        # 获取代理配置（如果有关联的代理）
        proxy_config = None
        if self.account_id:
            from myUtils.proxy_helper import get_proxy_config_dict
            proxy_config = get_proxy_config_dict(self.account_id)

        # 创建浏览器上下文配置
        context_config = {"storage_state": account_file_path}
        if proxy_config:
            context_config["proxy"] = proxy_config
            print(f"[DouYin Upload] Using proxy: {proxy_config}")

        # 创建一个浏览器上下文，使用指定的 cookie 文件
        try:
            context = await browser.new_context(**context_config)
        except Exception as e:
            douyin_logger.error(f'[!] 加载 Cookie 文件失败: {e}')
            await browser.close()
            raise
        context = await set_init_script(context)

        # 创建一个新的页面
        page = await context.new_page()
        # 🔍 在这里添加 pause 来调试 cookie 加载
        # await page.pause()  # 会打开 Playwright Inspector

        douyin_logger.info(f'[+]正在上传-------{self.title}.mp4')
        douyin_logger.info(f'[-] 正在打开主页...')
        
        # 导航到目标 URL
        try:
            await page.goto("https://creator.douyin.com/creator-micro/content/upload", 
                          wait_until='domcontentloaded',
                          timeout=30000)
            douyin_logger.info('[+] 页面导航成功')
        except Exception as e:
            douyin_logger.error(f'[!] 页面导航失败: {e}')
            # 检查是否跳转到登录页
            current_url = page.url
            douyin_logger.error(f'[!] 当前 URL: {current_url}')
            if "login" in current_url.lower() or "passport" in current_url.lower():
                douyin_logger.error('[!] 检测到跳转到登录页面，Cookie 可能已失效')
                await page.screenshot(path="debug_login_redirect.png", full_page=True)
                raise Exception("Cookie 失效，需要重新登录")
            raise
        
        # 检查是否出现登录提示
        try:
            await asyncio.sleep(1)  # 等待页面渲染
            if await page.get_by_text('手机号登录').count() > 0 or await page.get_by_text('扫码登录').count() > 0:
                douyin_logger.error('[!] 检测到登录页面，Cookie 已失效')
                await page.screenshot(path="debug_login_detected.png", full_page=True)
                raise Exception("Cookie 失效，需要重新登录")
        except Exception as e:
            if "Cookie" in str(e):
                raise
            # 其他异常忽略，继续执行
        
        # 等待页面完全加载
        try:
            await page.wait_for_load_state('networkidle', timeout=10000)
        except Exception as e:
            douyin_logger.warning(f'[!] 等待 networkidle 超时，继续执行: {e}')
        
        await asyncio.sleep(1)  # 额外等待确保页面渲染完成
        
        # 尝试多种方式上传文件
        upload_success = False
        
        # 方式1: 通过按钮文本定位并使用文件选择器（推荐）
        try:
            upload_button = page.get_by_role("button", name="上传视频")
            if await upload_button.count() > 0:
                await upload_button.wait_for(state='visible', timeout=5000)
                douyin_logger.info('[+] 通过文本定位到上传按钮，准备上传文件...')
                
                async with page.expect_file_chooser(timeout=10000) as fc_info:
                    await upload_button.click()
                file_chooser = await fc_info.value
                await file_chooser.set_files(self.file_path)
                upload_success = True
                douyin_logger.info('[+] 文件上传成功（方式1：按钮+文件选择器）')
        except Exception as e:
            douyin_logger.warning(f'[!] 方式1失败: {e}')
        
        # 方式2: 通过类名定位按钮（兼容哈希变化）
        if not upload_success:
            try:
                upload_button = page.locator("button[class*='container-drag-btn']").first
                if await upload_button.count() > 0:
                    await upload_button.wait_for(state='visible', timeout=5000)
                    douyin_logger.info('[+] 通过类名定位到上传按钮，准备上传文件...')
                    
                    async with page.expect_file_chooser(timeout=10000) as fc_info:
                        await upload_button.click()
                    file_chooser = await fc_info.value
                    await file_chooser.set_files(self.file_path)
                    upload_success = True
                    douyin_logger.info('[+] 文件上传成功（方式2：类名+文件选择器）')
            except Exception as e:
                douyin_logger.warning(f'[!] 方式2失败: {e}')
        
        # 方式3: 通过文本内容定位按钮
        if not upload_success:
            try:
                upload_button = page.locator("button:has-text('上传视频')").first
                if await upload_button.count() > 0:
                    await upload_button.wait_for(state='visible', timeout=5000)
                    douyin_logger.info('[+] 通过文本内容定位到上传按钮，准备上传文件...')
                    
                    async with page.expect_file_chooser(timeout=10000) as fc_info:
                        await upload_button.click()
                    file_chooser = await fc_info.value
                    await file_chooser.set_files(self.file_path)
                    upload_success = True
                    douyin_logger.info('[+] 文件上传成功（方式3：文本内容+文件选择器）')
            except Exception as e:
                douyin_logger.warning(f'[!] 方式3失败: {e}')
        
        # 方式4: 直接查找隐藏的 input（兼容旧版本）
        if not upload_success:
            try:
                input_element = page.locator("div[class^='container'] input[type='file']")
                if await input_element.count() > 0:
                    await input_element.wait_for(state='attached', timeout=5000)
                    douyin_logger.info('[+] 找到隐藏的 input 元素，直接上传文件...')
                    await input_element.set_input_files(self.file_path)
                    upload_success = True
                    douyin_logger.info('[+] 文件上传成功（方式4：直接 input）')
            except Exception as e:
                douyin_logger.warning(f'[!] 方式4失败: {e}')
        
        # 方式5: 查找任何 file 类型的 input
        if not upload_success:
            try:
                input_element = page.locator("input[type='file']").first
                if await input_element.count() > 0:
                    await input_element.wait_for(state='attached', timeout=5000)
                    douyin_logger.info('[+] 找到 file input 元素，直接上传文件...')
                    await input_element.set_input_files(self.file_path)
                    upload_success = True
                    douyin_logger.info('[+] 文件上传成功（方式5：通用 file input）')
            except Exception as e:
                douyin_logger.warning(f'[!] 方式5失败: {e}')
        
        # 如果所有方式都失败，抛出异常
        if not upload_success:
            douyin_logger.error('[!] 所有上传方式都失败了！')
            # 调试：截图和打印页面信息
            await page.screenshot(path="debug_upload_failed.png", full_page=True)
            douyin_logger.error('已保存调试截图: debug_upload_failed.png')
            raise Exception("无法找到上传按钮或文件输入框，请检查页面结构是否发生变化")

        # 等待页面跳转到指定的 URL 2025.01.08修改在原有基础上兼容两种页面
        while True:
            try:
                # 尝试等待第一个 URL
                await page.wait_for_url(
                    "https://creator.douyin.com/creator-micro/content/publish?enter_from=publish_page", timeout=3000)
                douyin_logger.info("[+] 成功进入version_1发布页面!")
                break  # 成功进入页面后跳出循环
            except Exception:
                try:
                    # 如果第一个 URL 超时，再尝试等待第二个 URL
                    await page.wait_for_url(
                        "https://creator.douyin.com/creator-micro/content/post/video?enter_from=publish_page",
                        timeout=3000)
                    douyin_logger.info("[+] 成功进入version_2发布页面!")

                    break  # 成功进入页面后跳出循环
                except:
                    print("  [-] 超时未进入视频发布页面，重新尝试...")
                    await asyncio.sleep(0.5)  # 等待 0.5 秒后重新尝试
        # 填充标题和话题
        # 检查是否存在包含输入框的元素
        # 这里为了避免页面变化，故使用相对位置定位：作品标题父级右侧第一个元素的input子元素
        await asyncio.sleep(1)
        douyin_logger.info(f'  [-] 正在填充标题和话题...')
        title_container = page.get_by_text('作品标题').locator("..").locator("xpath=following-sibling::div[1]").locator("input")
        if await title_container.count():
            await title_container.fill(self.title[:30])
        else:
            titlecontainer = page.locator(".notranslate")
            await titlecontainer.click()
            await page.keyboard.press("Backspace")
            await page.keyboard.press("Control+KeyA")
            await page.keyboard.press("Delete")
            await page.keyboard.type(self.title)
            await page.keyboard.press("Enter")
        css_selector = ".zone-container"
        for index, tag in enumerate(self.tags, start=1):
            await page.type(css_selector, "#" + tag)
            await page.press(css_selector, "Space")
        douyin_logger.info(f'总共添加{len(self.tags)}个话题')
        while True:
            # 判断重新上传按钮是否存在，如果不存在，代表视频正在上传，则等待
            try:
                #  新版：定位重新上传
                number = await page.locator('[class^="long-card"] div:has-text("重新上传")').count()
                if number > 0:
                    douyin_logger.success("  [-]视频上传完毕")
                    break
                else:
                    douyin_logger.info("  [-] 正在上传视频中...")
                    await asyncio.sleep(2)

                    if await page.locator('div.progress-div > div:has-text("上传失败")').count():
                        douyin_logger.error("  [-] 发现上传出错了... 准备重试")
                        await self.handle_upload_error(page)
            except:
                douyin_logger.info("  [-] 正在上传视频中...")
                await asyncio.sleep(2)

        if self.productLink and self.productTitle:
            douyin_logger.info(f'  [-] 正在设置商品链接...')
            await self.set_product_link(page, self.productLink, self.productTitle)
            douyin_logger.info(f'  [+] 完成设置商品链接...')
        
        #上传视频封面
        await self.set_thumbnail(page, self.thumbnail_path)

        # 更换可见元素
        await self.set_location(page, "")


        # 頭條/西瓜
        third_part_element = '[class^="info"] > [class^="first-part"] div div.semi-switch'
        # 定位是否有第三方平台
        if await page.locator(third_part_element).count():
            # 检测是否是已选中状态
            if 'semi-switch-checked' not in await page.eval_on_selector(third_part_element, 'div => div.className'):
                await page.locator(third_part_element).locator('input.semi-switch-native-control').click()

        if self.publish_date != 0:
            await self.set_schedule_time_douyin(page, self.publish_date)

        # 判断视频是否发布成功
        while True:
            # 判断视频是否发布成功
            try:
                publish_button = page.get_by_role('button', name="发布", exact=True)
                if await publish_button.count():
                    await publish_button.click()
                await page.wait_for_url("https://creator.douyin.com/creator-micro/content/manage**",
                                        timeout=3000)  # 如果自动跳转到作品页面，则代表发布成功
                douyin_logger.success("  [-]视频发布成功")
                break
            except:
                # 尝试处理封面问题
                await self.handle_auto_video_cover(page)
                douyin_logger.info("  [-] 视频正在发布中...")
                await page.screenshot(full_page=True)
                await asyncio.sleep(0.5)

        await context.storage_state(path=account_file_path)  # 保存cookie
        douyin_logger.success('  [-]cookie更新完毕！')
        await asyncio.sleep(2)  # 这里延迟是为了方便眼睛直观的观看
        # 关闭浏览器上下文和浏览器实例
        await context.close()
        await browser.close()

    async def handle_auto_video_cover(self, page):
        """
        处理必须设置封面的情况，点击推荐封面的第一个
        """
        # 1. 判断是否出现 "请设置封面后再发布" 的提示
        # 必须确保提示是可见的 (is_visible)，因为 DOM 中可能存在隐藏的历史提示
        if await page.get_by_text("请设置封面后再发布").first.is_visible():
            print("  [-] 检测到需要设置封面提示...")

            # 2. 定位“智能推荐封面”区域下的第一个封面
            # 使用 class^= 前缀匹配，避免 hash 变化导致失效
            recommend_cover = page.locator('[class^="recommendCover-"]').first

            if await recommend_cover.count():
                print("  [-] 正在选择第一个推荐封面...")
                try:
                    await recommend_cover.click()
                    await asyncio.sleep(1)  # 等待选中生效

                    # 3. 处理可能的确认弹窗 "是否确认应用此封面？"
                    # 并不一定每次都会出现，健壮性判断：如果出现弹窗，则点击确定
                    confirm_text = "是否确认应用此封面？"
                    if await page.get_by_text(confirm_text).first.is_visible():
                        print(f"  [-] 检测到确认弹窗: {confirm_text}")
                        # 直接点击"确定"按钮，不依赖脆弱的 CSS 类名
                        await page.get_by_role("button", name="确定").click()
                        print("  [-] 已点击确认应用封面")
                        await asyncio.sleep(1)

                    # 4. 等待封面效果检测通过
                    print("  [-] 等待封面效果检测...")
                    try:
                        # 等待"封面效果检测通过"提示出现
                        await page.wait_for_selector('span:has-text("封面效果检测通过")', timeout=30000)
                        print("  [+] 封面效果检测通过！")
                    except Exception as e:
                        print(f"  [!] 等待封面检测超时或未找到提示: {e}")
                        # 如果超时，继续执行，避免卡住
                        print("  [!] 继续执行，但封面可能未完全检测完成")

                    print("  [-] 已完成封面选择流程")
                    return True
                except Exception as e:
                    print(f"  [-] 选择封面失败: {e}")
     
        return False

    async def set_thumbnail(self, page: Page, thumbnail_path: str):
        if thumbnail_path:
            douyin_logger.info('  [-] 正在设置视频封面...')
            await page.click('text="选择封面"')
            await page.wait_for_selector("div.dy-creator-content-modal")
            await page.click('text="设置竖封面"')
            await page.wait_for_timeout(2000)  # 等待2秒
            # 定位到上传区域并点击
            await page.locator("div[class^='semi-upload upload'] >> input.semi-upload-hidden-input").set_input_files(thumbnail_path)
            await page.wait_for_timeout(2000)  # 等待2秒
            await page.locator("div#tooltip-container button:visible:has-text('完成')").click()
            # finish_confirm_element = page.locator("div[class^='confirmBtn'] >> div:has-text('完成')")
            # if await finish_confirm_element.count():
            #     await finish_confirm_element.click()
            # await page.locator("div[class^='footer'] button:has-text('完成')").click()
            
            # 等待封面效果检测通过
            douyin_logger.info('  [-] 等待封面效果检测...')
            try:
                # 等待"封面效果检测通过"提示出现
                await page.wait_for_selector('span:has-text("封面效果检测通过")', timeout=30000)
                douyin_logger.info('  [+] 封面效果检测通过！')
            except Exception as e:
                douyin_logger.warning(f'  [!] 等待封面检测超时或未找到提示: {e}')
            
            douyin_logger.info('  [+] 视频封面设置完成！')
            # 等待封面设置对话框关闭
            await page.wait_for_selector("div.extractFooter", state='detached')
            

    async def set_location(self, page: Page, location: str = ""):
        if not location:
            return
        # todo supoort location later
        # await page.get_by_text('添加标签').locator("..").locator("..").locator("xpath=following-sibling::div").locator(
        #     "div.semi-select-single").nth(0).click()
        await page.locator('div.semi-select span:has-text("输入地理位置")').click()
        await page.keyboard.press("Backspace")
        await page.wait_for_timeout(2000)
        await page.keyboard.type(location)
        await page.wait_for_selector('div[role="listbox"] [role="option"]', timeout=5000)
        await page.locator('div[role="listbox"] [role="option"]').first.click()

    async def handle_product_dialog(self, page: Page, product_title: str):
        """处理商品编辑弹窗"""

        await page.wait_for_timeout(2000)
        await page.wait_for_selector('input[placeholder="请输入商品短标题"]', timeout=10000)
        short_title_input = page.locator('input[placeholder="请输入商品短标题"]')
        if not await short_title_input.count():
            douyin_logger.error("[-] 未找到商品短标题输入框")
            return False
        product_title = product_title[:10]
        await short_title_input.fill(product_title)
        # 等待一下让界面响应
        await page.wait_for_timeout(1000)

        finish_button = page.locator('button:has-text("完成编辑")')
        if 'disabled' not in await finish_button.get_attribute('class'):
            await finish_button.click()
            douyin_logger.debug("[+] 成功点击'完成编辑'按钮")
            
            # 等待对话框关闭
            await page.wait_for_selector('.semi-modal-content', state='hidden', timeout=5000)
            return True
        else:
            douyin_logger.error("[-] '完成编辑'按钮处于禁用状态，尝试直接关闭对话框")
            # 如果按钮禁用，尝试点击取消或关闭按钮
            cancel_button = page.locator('button:has-text("取消")')
            if await cancel_button.count():
                await cancel_button.click()
            else:
                # 点击右上角的关闭按钮
                close_button = page.locator('.semi-modal-close')
                await close_button.click()
            
            await page.wait_for_selector('.semi-modal-content', state='hidden', timeout=5000)
            return False
        
    async def set_product_link(self, page: Page, product_link: str, product_title: str):
        """设置商品链接功能"""
        await page.wait_for_timeout(2000)  # 等待2秒
        try:
            # 定位"添加标签"文本，然后向上导航到容器，再找到下拉框
            await page.wait_for_selector('text=添加标签', timeout=10000)
            dropdown = page.get_by_text('添加标签').locator("..").locator("..").locator("..").locator(".semi-select").first
            if not await dropdown.count():
                douyin_logger.error("[-] 未找到标签下拉框")
                return False
            douyin_logger.debug("[-] 找到标签下拉框，准备选择'购物车'")
            await dropdown.click()
            ## 等待下拉选项出现
            await page.wait_for_selector('[role="listbox"]', timeout=5000)
            ## 选择"购物车"选项
            await page.locator('[role="option"]:has-text("购物车")').click()
            douyin_logger.debug("[+] 成功选择'购物车'")
            
            # 输入商品链接
            ## 等待商品链接输入框出现
            await page.wait_for_selector('input[placeholder="粘贴商品链接"]', timeout=5000)
            # 输入
            input_field = page.locator('input[placeholder="粘贴商品链接"]')
            await input_field.fill(product_link)
            douyin_logger.debug(f"[+] 已输入商品链接: {product_link}")
            
            # 点击"添加链接"按钮
            add_button = page.locator('span:has-text("添加链接")')
            ## 检查按钮是否可用（没有disable类）
            button_class = await add_button.get_attribute('class')
            if 'disable' in button_class:
                douyin_logger.error("[-] '添加链接'按钮不可用")
                return False
            await add_button.click()
            douyin_logger.debug("[+] 成功点击'添加链接'按钮")
            ## 如果链接不可用
            await page.wait_for_timeout(2000)
            error_modal = page.locator('text=未搜索到对应商品')
            if await error_modal.count():
                confirm_button = page.locator('button:has-text("确定")')
                await confirm_button.click()
                # await page.wait_for_selector('.semi-modal-content', state='hidden', timeout=5000)
                douyin_logger.error("[-] 商品链接无效")
                return False

            # 填写商品短标题
            if not await self.handle_product_dialog(page, product_title):
                return False
            
            # 等待链接添加完成
            douyin_logger.debug("[+] 成功设置商品链接")
            return True
        except Exception as e:
            douyin_logger.error(f"[-] 设置商品链接时出错: {str(e)}")
            return False

    async def main(self):
        async with async_playwright() as playwright:
            await self.upload(playwright)


