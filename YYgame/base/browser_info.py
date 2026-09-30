# encoding: utf-8
"""
浏览器实例信息，对应 yyautomation 的 DeviceInfo。
一个 BrowserInfo = 一个 playwright browser context + 一个 page
"""
from base.constant import CHROMIUM, PC


class BrowserInfo:

    def __init__(self, browser_type=CHROMIUM, platform=PC, headless=False,
                 base_url='', index=0):
        self.browser_type = browser_type  # chromium / firefox / webkit
        self.platform = platform  # pc / h5，page 里的定位器按这个 key 取值
        self.headless = headless
        self.base_url = base_url
        self.index = index

        self.browser = None  # playwright Browser
        self.context = None  # playwright BrowserContext
        self.page = None  # playwright Page，当前活动页
        self.serial = f'{browser_type}_{platform}_{index}'  # 日志/截图命名

    def bind(self, browser, context, page):
        self.browser = browser
        self.context = context
        self.page = page

    def set_page(self, page):
        """切换当前活动页（点击后开新标签时使用）"""
        self.page = page

    def __repr__(self):
        return f'<BrowserInfo {self.serial} headless={self.headless}>'
