# encoding: utf-8
"""
元素封装。方法名沿用 yyautomation 的习惯（exist / wait_exist / wait_and_click / input），
底层换成 playwright，自动等待由 playwright 负责，不再需要手写轮询和 js 兜底点击。
"""
from loguru import logger
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PWTimeoutError

from common.locator import Locator
from settings import ELEMENT_TIMEOUT


class Element(object):

    def __init__(self, device, locator):
        self.d = device
        self.locator = Locator(device, locator)

    # ---------------- 查找 ----------------
    def find(self, method='default'):
        """返回 playwright Locator（惰性，不触发查找）"""
        return self.locator.build(method)

    def first(self, method='default'):
        return self.find(method).first

    def count(self, method='default'):
        return self.find(method).count()

    # ---------------- 等待 / 判断 ----------------
    def wait_exist(self, timeout=ELEMENT_TIMEOUT, method='default'):
        """等待元素可见，返回 True/False；timeout 单位毫秒"""
        try:
            self.first(method).wait_for(state='visible', timeout=timeout)
            return True
        except (PWTimeoutError, PlaywrightError):
            logger.info(f'等待元素超时({timeout}ms): {self.locator}')
            return False

    def exist(self, method='default'):
        """立即判断是否可见，不等待"""
        try:
            return self.first(method).is_visible(timeout=1000)
        except (PWTimeoutError, PlaywrightError):
            return False

    def wait_until_disappear(self, timeout=ELEMENT_TIMEOUT, method='default'):
        try:
            self.first(method).wait_for(state='hidden', timeout=timeout)
            return True
        except (PWTimeoutError, PlaywrightError):
            return False

    def is_enabled(self, method='default'):
        return self.first(method).is_enabled()

    def is_checked(self, method='default'):
        return self.first(method).is_checked()

    def is_displayed(self, method='default'):
        return self.exist(method)

    # ---------------- 操作 ----------------
    def click(self, method='default', timeout=ELEMENT_TIMEOUT, is_raise=True, force=False):
        try:
            self.first(method).click(timeout=timeout, force=force)
            return True
        except (PWTimeoutError, PlaywrightError) as e:
            if is_raise:
                raise
            logger.info(f'点击失败({type(e).__name__}): {self.locator}')
            return False

    def wait_and_click(self, second=ELEMENT_TIMEOUT, method='default', is_raise=True):
        """语义与移动端框架一致：等出现再点。playwright 的 click 自带 actionability 等待"""
        if not self.wait_exist(second, method):
            if is_raise:
                raise AssertionError(f'元素未出现，无法点击: {self.locator}')
            return False
        return self.click(method, timeout=second, is_raise=is_raise)

    def double_click(self, method='default'):
        self.first(method).dblclick()

    def hover(self, method='default'):
        self.first(method).hover()

    def check(self, method='default'):
        """勾选（协议 checkbox 这类），已勾选则跳过"""
        target = self.first(method)
        try:
            target.check()
        except PlaywrightError:
            # 非标准 input 实现的自定义勾选框，退化为点击
            target.click()
        return True

    def clear(self, method='default'):
        self.first(method).fill('')

    def input(self, text, method='default', is_need_clear=True):
        target = self.first(method)
        if is_need_clear:
            target.fill('')
        target.fill(str(text))

    def type_slowly(self, text, delay=80, method='default'):
        """逐字输入，绕过部分前端只监听 keydown 的输入框"""
        self.first(method).press_sequentially(str(text), delay=delay)

    def press(self, key, method='default'):
        self.first(method).press(key)

    def upload_file(self, file_path, method='default'):
        self.first(method).set_input_files(file_path)

    def select_option(self, value, method='default'):
        self.first(method).select_option(value)

    def scroll_into_view(self, method='default'):
        self.first(method).scroll_into_view_if_needed()

    # ---------------- 取值 ----------------
    def text(self, method='default'):
        try:
            return (self.first(method).inner_text(timeout=ELEMENT_TIMEOUT) or '').strip()
        except (PWTimeoutError, PlaywrightError):
            return ''

    def texts(self, method='default'):
        return [t.strip() for t in self.find(method).all_inner_texts()]

    def input_value(self, method='default'):
        return self.first(method).input_value()

    def get_attribute(self, attribute, method='default'):
        return self.first(method).get_attribute(attribute)

    def contains(self, text, timeout=ELEMENT_TIMEOUT, method='default'):
        """等待元素文本包含 text"""
        try:
            self.first(method).filter(has_text=text).wait_for(state='visible', timeout=timeout)
            return True
        except (PWTimeoutError, PlaywrightError):
            logger.info(f'文本未包含 "{text}"，实际: {self.text(method)}')
            return False

    def text_equal(self, text, timeout=ELEMENT_TIMEOUT, method='default'):
        from playwright.sync_api import expect
        try:
            expect(self.first(method)).to_have_text(text, timeout=timeout)
            return True
        except AssertionError:
            return False
