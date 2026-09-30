# encoding: utf-8
"""
页面级操作封装，用例里通过 self.userA.driver.xxx 调用
"""
import os

from loguru import logger
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PWTimeoutError

from settings import ELEMENT_TIMEOUT, NAVIGATION_TIMEOUT


class Driver(object):

    def __init__(self, device):
        self.d = device

    @property
    def page(self):
        return self.d.page

    @property
    def context(self):
        return self.d.context

    # ---------------- 导航 ----------------
    def open(self, url='/', wait_until='domcontentloaded'):
        """相对路径会拼 base_url（context 已设置 base_url）"""
        logger.info(f'打开页面: {url}')
        self.page.goto(url, wait_until=wait_until, timeout=NAVIGATION_TIMEOUT)
        return self.page.url

    def refresh(self):
        self.page.reload(wait_until='domcontentloaded')

    def back(self):
        self.page.go_back()

    def forward(self):
        self.page.go_forward()

    @property
    def current_url(self):
        return self.page.url

    @property
    def title(self):
        return self.page.title()

    def wait_url_contains(self, text, timeout=ELEMENT_TIMEOUT):
        try:
            self.page.wait_for_url(f'**{text}**', timeout=timeout)
            return True
        except (PWTimeoutError, PlaywrightError):
            logger.info(f'url 未包含 {text}, 当前: {self.page.url}')
            return False

    def wait_load_state(self, state='networkidle', timeout=NAVIGATION_TIMEOUT):
        try:
            self.page.wait_for_load_state(state, timeout=timeout)
            return True
        except (PWTimeoutError, PlaywrightError):
            return False

    def sleep(self, seconds):
        """仅用于确实需要等动画/轮播的场景，别拿它当万能等待"""
        self.page.wait_for_timeout(seconds * 1000)

    # ---------------- 标签页 ----------------
    def switch_to_latest_page(self):
        """切到最新打开的标签页，点外链后使用"""
        pages = self.context.pages
        self.d.set_page(pages[-1])
        self.d.page.bring_to_front()
        return self.d.page.url

    def switch_to_first_page(self):
        self.d.set_page(self.context.pages[0])
        return self.d.page.url

    def close_other_pages(self):
        """关闭除第一个之外的标签页并切回第一个"""
        pages = self.context.pages
        for page in pages[1:]:
            try:
                page.close()
            except PlaywrightError:
                pass
        self.d.set_page(self.context.pages[0])

    def page_count(self):
        return len(self.context.pages)

    def expect_new_page(self, action):
        """
        点击会开新标签时用：
            driver.expect_new_page(lambda: page_obj.some_btn.click())
        """
        with self.context.expect_page() as info:
            action()
        new_page = info.value
        new_page.wait_for_load_state('domcontentloaded')
        self.d.set_page(new_page)
        return new_page

    # ---------------- iframe ----------------
    def frame_locator(self, selector):
        """给 action 层直接操作 iframe 内元素用（登录走的是 UDB iframe）"""
        return self.page.frame_locator(selector)

    def frame_by_url(self, url_part, timeout=ELEMENT_TIMEOUT):
        """按 url 片段找 frame 对象，找不到返回 None"""
        deadline = timeout
        while deadline > 0:
            for frame in self.page.frames:
                if url_part in frame.url:
                    return frame
            self.page.wait_for_timeout(500)
            deadline -= 500
        return None

    # ---------------- 弹窗 / 网络 ----------------
    def accept_dialog(self):
        """注册一次性 alert/confirm 自动确认"""
        self.page.once('dialog', lambda dialog: dialog.accept())

    def dismiss_dialog(self):
        self.page.once('dialog', lambda dialog: dialog.dismiss())

    def mock_api(self, url_pattern, status=200, body=None, json_body=None):
        """mock 接口返回，用于构造异常态 UI"""
        def handler(route):
            if json_body is not None:
                route.fulfill(status=status, json=json_body)
            else:
                route.fulfill(status=status, body=body or '')
        self.page.route(url_pattern, handler)

    def abort_api(self, url_pattern):
        """让接口失败，验证降级/兜底文案"""
        self.page.route(url_pattern, lambda route: route.abort())

    def expect_response(self, url_pattern, action, timeout=NAVIGATION_TIMEOUT):
        """执行 action 并捕获匹配的响应，用于校验接口状态码/返回体"""
        with self.page.expect_response(url_pattern, timeout=timeout) as info:
            action()
        return info.value

    # ---------------- 登录态 / storage ----------------
    def save_storage_state(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.context.storage_state(path=path)
        logger.info(f'登录态已保存: {path}')
        return path

    def clear_cookies(self):
        self.context.clear_cookies()

    def clear_storage(self):
        self.page.evaluate('() => {localStorage.clear();sessionStorage.clear();}')

    def get_cookies(self):
        return self.context.cookies()

    # ---------------- js / 滚动 / 截图 ----------------
    def execute_js(self, script, arg=None):
        return self.page.evaluate(script, arg) if arg is not None else self.page.evaluate(script)

    def scroll_to_bottom(self):
        self.page.evaluate('() => window.scrollTo(0, document.body.scrollHeight)')

    def scroll_to_top(self):
        self.page.evaluate('() => window.scrollTo(0, 0)')

    def screenshot(self, file_path, full_page=False):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        self.page.screenshot(path=file_path, full_page=full_page)
        return file_path

    def console_logs(self):
        """返回本页收集到的控制台日志，由 conftest 在建页时挂的监听填充"""
        return getattr(self.page, '_console_logs', [])
