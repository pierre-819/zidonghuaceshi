# -*- coding: utf-8 -*-
"""
User = 一个浏览器实例 + 一个账号 + 绑定好的 page / action
用例里通过 self.userA.xxx 使用，写法与 yyautomation 一致
"""
from action import *
from base.my_logger import MyLogger
from common.driver import Driver
from page import *


class User:
    def __init__(self, browser_info, uid, username, password, role):
        self.uid = uid
        self.username = username
        self.password = password
        self.role = role
        self.device = browser_info
        self.platform = browser_info.platform
        self.browser_type = browser_info.browser_type
        # 用例失败后需要保留的文件（截图/trace 等）
        self.fail_upload_file_list = []

        # 绑定 driver
        self.driver = Driver(browser_info)

        # 绑定 page
        self.home_page = HomePage(browser_info)
        self.login_page = LoginPage(browser_info)

        # 绑定 action
        self.base_action = BaseAction(browser_info)
        self.login_action = LoginAction(browser_info)
        self.nav_action = NavAction(browser_info)

        self.log = MyLogger()
        self.log.info(f'{role} account={username}, browser={browser_info.serial}')
