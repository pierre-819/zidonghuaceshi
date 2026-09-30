# encoding: utf-8
"""
浏览器初始化 / 回收，对应 yyautomation 的 base/init.py
"""
import os

from loguru import logger
from playwright.sync_api import sync_playwright

from base.browser_info import BrowserInfo
from base.constant import CHROMIUM, H5, H5_DEVICE_NAME, PC_VIEWPORT
from settings import ACTION_TIMEOUT, NAVIGATION_TIMEOUT, TRACE_DIR


class Init:
    """管理 playwright 生命周期：start -> launch -> context -> page"""

    def __init__(self, slow_mo=0):
        self.playwright = None
        self.slow_mo = slow_mo  # 每个操作之间放慢的毫秒数，调试/演示时用

    def set_local_browsers_config(self, num, browser_type=CHROMIUM, platform='pc',
                                  headless=False, base_url=''):
        return [BrowserInfo(browser_type=browser_type, platform=platform, headless=headless,
                            base_url=base_url, index=i) for i in range(num)]

    def init(self, browser_list, storage_state=None, trace=True):
        """
        启动浏览器
        :param storage_state: 已保存的登录态文件路径，传了就免密进入
        :param trace: 是否录 trace，失败用例可用 playwright show-trace 回放
        """
        self.playwright = sync_playwright().start()
        for browser_info in browser_list:
            browser = self._launch(browser_info)
            context = self._new_context(browser, browser_info, storage_state)
            context.set_default_timeout(ACTION_TIMEOUT)
            context.set_default_navigation_timeout(NAVIGATION_TIMEOUT)
            if trace:
                os.makedirs(TRACE_DIR, exist_ok=True)
                context.tracing.start(screenshots=True, snapshots=True, sources=True)
            page = context.new_page()
            browser_info.bind(browser, context, page)
            logger.info(f'启动浏览器成功: {browser_info}')
        return browser_list

    def _launch(self, browser_info: BrowserInfo):
        launcher = getattr(self.playwright, browser_info.browser_type, None)
        if launcher is None:
            raise ValueError(f'不支持的浏览器: {browser_info.browser_type}')
        return launcher.launch(headless=browser_info.headless,
                               slow_mo=self.slow_mo,
                               args=['--mute-audio', '--disable-notifications'])

    def _new_context(self, browser, browser_info: BrowserInfo, storage_state):
        kwargs = {'base_url': browser_info.base_url, 'locale': 'zh-CN',
                  'timezone_id': 'Asia/Shanghai'}
        if storage_state and os.path.exists(storage_state):
            kwargs['storage_state'] = storage_state
            logger.info(f'复用登录态: {storage_state}')
        if browser_info.platform == H5:
            kwargs.update(self.playwright.devices[H5_DEVICE_NAME])
        else:
            kwargs['viewport'] = PC_VIEWPORT
        return browser.new_context(**kwargs)

    def stop_trace(self, browser_info: BrowserInfo, trace_path):
        """把 trace 落盘，失败用例排查用"""
        try:
            os.makedirs(os.path.dirname(trace_path), exist_ok=True)
            browser_info.context.tracing.stop(path=trace_path)
            logger.info(f'trace 已保存: {trace_path}')
            return trace_path
        except Exception as e:
            logger.info(f'保存 trace 失败: {e}')
            return None

    def quit(self, browser_list):
        for browser_info in browser_list:
            for closer in (browser_info.context, browser_info.browser):
                try:
                    if closer:
                        closer.close()
                except Exception as e:
                    logger.error(f'关闭失败 {browser_info.serial}: {e}')
        try:
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.error(f'停止 playwright 失败: {e}')
