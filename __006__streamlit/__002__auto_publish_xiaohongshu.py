import os
import re
from playwright.sync_api import sync_playwright

from tools.path_utils import resolve_from_project_root


class XiaohongshuUploader:
    COOKIE_DIR_PATH = resolve_from_project_root("cookie_dir/")
    PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish?from=homepage&target=image&source=official"
    LOGIN_URL_PREFIX = "https://creator.xiaohongshu.com/login"

    def __init__(self, user_id, image_paths, title="", content="", headless=True):
        self.user_id = user_id
        self.cookie_path = os.path.join(self.COOKIE_DIR_PATH, f"{self.user_id}.json")
        self.image_paths = image_paths if isinstance(image_paths, list) else [image_paths]
        self.title = title
        self.content = content
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.headless = headless

    def launch(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)

        if os.path.exists(self.cookie_path):
            print("[√] 加载已保存的登录状态...")
            self.context = self.browser.new_context(
                storage_state=self.cookie_path,
                permissions=["geolocation"],
                geolocation={"latitude": 31.2304, "longitude": 121.4737}
            )
        else:
            print("[!] 未检测到登录状态，创建新上下文...")
            self.context = self.browser.new_context(
                permissions=["geolocation"],
                geolocation={"latitude": 31.2304, "longitude": 121.4737}
            )

        self.page = self.context.new_page()
        self.page.goto(self.PUBLISH_URL)

    def switch_to_image_post(self):
        """切换到【上传图文】Tab，排除隐藏元素，并在必要时重试多种选择器。"""
        print("🔀 尝试切换到【上传图文】...")

        # 1) 首选：使用 XPath，过滤掉隐藏在屏幕外的 Tab
        try:
            tab = self.page.locator(
                '//div[contains(@class,"creator-tab")][.//span[contains(@class,"title") and normalize-space(text())="上传图文"]]'
                '[not(contains(@style,"left: -9999px"))]'
            ).first
            tab.wait_for(state="visible", timeout=5000)
            tab.click()
            print("[√] 已切换到【上传图文】（XPath 命中）")
        except Exception as e1:
            print(f"[!] XPath 方式未命中，原因：{e1}")

            # 2) 退路：用 has 定位可见的 creator-tab
            try:
                tab2 = self.page.locator('div.creator-tab').filter(
                    has=self.page.locator('span.title', has_text="上传图文")
                ).first
                tab2.wait_for(state="visible", timeout=5000)
                tab2.click()
                print("[√] 已切换到【上传图文】（has 过滤命中）")
            except Exception as e2:
                print(f"[!] has 过滤方式未命中，原因：{e2}")

                # 3) 最后退路：直接点文本（Playwright 会优先点可见元素）
                try:
                    self.page.get_by_text("上传图文", exact=True).first.click()
                    print("[√] 已切换到【上传图文】（文本匹配命中）")
                except Exception as e3:
                    print(f"[X] 切换到【上传图文】失败：{e3}")

        # 等待图文上传区域的图片文件选择器出现（避免还停留在“上传视频”）
        try:
            # 图文面板一般会出现一个接收图片的 input[type=file]；为稳妥，这里只校验出现任意文件 input
            self.page.wait_for_selector('input[type="file"]', timeout=8000)
            print("[√] 图文上传区域已就绪")
        except:
            print("[!] 未检测到图文上传的文件输入框，稍后上传可能失败")

    def upload_images(self):
        print("📤 正在上传图片...")

        self.page.wait_for_selector('input[type="file"]', timeout=10000)
        file_inputs = self.page.query_selector_all('input[type="file"]')
        if file_inputs:
            file_inputs[0].set_input_files(self.image_paths)
            print(f"[√] 已上传 {len(self.image_paths)} 张图片")
        else:
            print("[x] 未找到文件上传输入框")

    def fill_title_and_content(self):
        print("📝 正在填写标题和正文...")

        # 填写标题
        try:
            title_input = self.page.wait_for_selector('input.d-text[placeholder*="填写标题"]', timeout=10000)
            title_input.fill(self.title)
            print(f"[√] 标题已填写：{self.title}")
        except:
            print("[x] 未找到标题输入框")

        # 填写正文
        try:
            editor = self.page.wait_for_selector(".editor-content > div > div[contenteditable='true']", timeout=10000)
            editor.click()
            editor.type(self.content)
            print(f"[√] 正文已填写：{self.content}")
        except:
            print("[x] 未找到正文编辑器")

    def submit_post(self):
        self.wait_seconds(3)
        print("🚀 正在尝试点击发布按钮...")

        try:
            # 等待“发布”按钮出现并可点击
            self.page.wait_for_selector('button:has-text("发布")', timeout=10000)
            publish_button = self.page.query_selector('button:has-text("发布")')

            if publish_button:
                publish_button.click()
                print("[√] 发布按钮已点击")
            else:
                print("[!] 未找到发布按钮")
        except Exception as e:
            print(f"[X] 发布失败: {e}")

    def wait_for_login_page(self) -> bool:
        """
        显式等待是否进入登录页。
        返回 True 表示当前已到登录页；False 表示在超时内没有到登录页。
        """
        print("[…] 正在等待是否会跳转到登录页...")
        try:
            # 先等 URL 模式
            self.page.wait_for_url(re.compile(r"https://creator\.xiaohongshu\.com/login.*"), timeout=2000)
            print("[!] 已到达登录页（URL + DOM 双重确认）")
            return True
        except Exception as e:
            print(f"[warn] 检测登录页时出现异常：{e}")
            return False

    def wait_for_publish_page(self) -> bool:
        """
        显式等待是否进入上传文件页。
        返回 True 表示当前已到登录页；False 表示在超时内没有到登录页。
        """
        print("[…] 正在等待是否会跳转到上传文件页...")
        try:
            # 先等 URL 模式
            self.page.wait_for_url(re.compile(r"https://creator\.xiaohongshu\.com/publish.*"), timeout=1000 * 60 * 3)
            print("[!] 已到达上传文件页（URL + DOM 双重确认）")
            return True
        except Exception as e:
            print(f"[warn] 检测上传文件时出现异常：{e}")
            return False

    def save_login_sate(self):
        # 保存登录状态
        self.context.storage_state(path=self.cookie_path)

    def close(self):
        # 等待4秒
        self.wait_seconds(4)
        self.browser.close()
        self.playwright.stop()

    def wait_seconds(self, seconds):
        print(f"⏳ 等待 {seconds} 秒...")
        self.page.wait_for_timeout(seconds * 1000)


def auto_publish_xiaohongshu(user_id, images, title, content, headless=False, is_test=False):
    print("🚀 开始上传小红书...")
    xhs = XiaohongshuUploader(user_id, images, title, content, headless=False if is_test else headless)
    xhs.launch()
    # 等待登陆页面
    if xhs.wait_for_login_page():
        print("进入登陆页面，请手动完成登陆")
        if headless:
            xhs.close()
            auto_publish_xiaohongshu(user_id, images, title, content, headless=False if is_test else not headless)
            return
        else:
            # 需要等待进入发布页面
            if xhs.wait_for_publish_page():
                # 保存登录状态
                xhs.save_login_sate()
                if not headless:
                    # 重新启动
                    xhs.close()
                    # 无头模式启动
                    auto_publish_xiaohongshu(user_id, images, title, content,
                                             headless=False if is_test else not headless)
                    return

    xhs.switch_to_image_post()
    xhs.upload_images()
    xhs.fill_title_and_content()
    # 最后点击发布
    xhs.submit_post()

    xhs.close()


if __name__ == "__main__":
    images = [
        "/Users/duyi/duyi7/HeiMa/Project/XiaoHongShuProject/output.png"
    ]
    title = "自动化上传测试"
    content = "这是使用 Playwright 自动发布的内容 😊"
    is_test = False
    auto_publish_xiaohongshu("user_01", images, title, content, headless=True, is_test=is_test)
