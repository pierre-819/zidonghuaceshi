# encoding: utf-8
"""
公共动作：与具体业务无关的通用步骤
"""
from loguru import logger

from common.driver import Driver
from page.yygame.home_page import HomePage


class BaseAction(object):

    def __init__(self, device):
        self.d = device
        self.driver = Driver(device)
        self.home_page = HomePage(device)

    def open_home(self):
        """打开首页并等首屏渲染完（站点是 SPA，domcontentloaded 后还要等 logo）"""
        self.driver.open('/')
        return self.home_page.logo.wait_exist(30000)

    def clear_login_state(self):
        """清 cookie + storage，回到未登录态"""
        self.driver.clear_cookies()
        self.driver.open('/')
        self.driver.clear_storage()
        self.driver.refresh()
        self.home_page.logo.wait_exist(30000)
        logger.info('已清理登录态')

    def close_popup_if_exist(self, element, timeout=3000):
        """存在弹窗就关掉，用于活动弹窗这种不稳定元素"""
        if element.wait_exist(timeout):
            element.click(is_raise=False)
            return True
        return False

    def scroll_and_load_all(self, list_element, max_scroll=5):
        """滚动加载懒加载列表，返回最终条目数"""
        last_count = list_element.count()
        for _ in range(max_scroll):
            self.driver.scroll_to_bottom()
            self.driver.sleep(1)
            current_count = list_element.count()
            if current_count == last_count:
                break
            last_count = current_count
        return last_count
