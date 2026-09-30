# encoding: utf-8
"""
登录业务动作。站点登录形态：弹窗 + UDB 嵌套 iframe，
手机号登录要短信码（自动化不可控），所以自动化只走 YY号账密。
"""
from loguru import logger

from action.yygame.base_action import BaseAction
from page.yygame.login_page import LOGIN_API, LoginPage
from settings import STORAGE_STATE_FILE


class LoginAction(BaseAction):

    def __init__(self, device):
        super().__init__(device)
        self.login_page = LoginPage(device)

    # ---------------- 弹窗 ----------------
    def open_login_dialog(self):
        """从首页打开登录弹窗，已打开则直接返回"""
        if self.login_page.dialog.exist():
            return True
        self.home_page.login_entrance.wait_and_click(20000)
        return self.login_page.dialog.wait_exist(20000)

    def close_login_dialog(self):
        self.login_page.close_btn.wait_and_click(10000)
        return self.login_page.dialog.wait_until_disappear(10000)

    def switch_to_yy_tab(self):
        """切到 YY号登录，返回该 tab 是否处于选中态"""
        self.login_page.tab_yy.wait_and_click(10000)
        return self.login_page.tab_yy.get_attribute('aria-selected') == 'true'

    def switch_to_phone_tab(self):
        self.login_page.tab_phone.wait_and_click(10000)
        return self.login_page.tab_phone.get_attribute('aria-selected') == 'true'

    def current_tab(self):
        """返回当前选中的 tab 名"""
        if self.login_page.tab_yy.get_attribute('aria-selected') == 'true':
            return 'YY号登录'
        if self.login_page.tab_phone.get_attribute('aria-selected') == 'true':
            return '手机号登录'
        return ''

    # ---------------- 协议 ----------------
    def is_protocol_checked(self):
        return self.login_page.protocol_checkbox.get_attribute('aria-checked') == 'true'

    def agree_protocol(self):
        """勾选协议，勾上后表单拦截层会消失"""
        if not self.is_protocol_checked():
            self.login_page.protocol_checkbox.click()
        assert self.is_protocol_checked(), '协议勾选失败'
        return self.login_page.protocol_blocker.wait_until_disappear(5000)

    # ---------------- 登录 ----------------
    def fill_yy_account(self, account, password):
        """只填表单不提交，供“未勾协议被拦截”这类用例使用"""
        self.login_page.account_input.input(account)
        self.login_page.password_input.input(password)

    def login_by_yy_account(self, account, password, check=True):
        """
        YY号账密登录
        :param check: True 则断言登录成功
        :return: 登录接口的 response 对象，可用来看状态码/返回体
        """
        logger.info(f'YY号登录: {account}')
        self.open_login_dialog()
        self.switch_to_yy_tab()
        self.agree_protocol()
        self.fill_yy_account(account, password)

        response = self.driver.expect_response(
            LOGIN_API, lambda: self.login_page.login_btn.click())
        logger.info(f'登录接口: {response.status} {response.url}')

        if check:
            assert self.is_logged_in(), '登录后顶部仍是未登录态'
        return response

    def is_logged_in(self, timeout=20000):
        """判断已登录：顶部“登录/注册”按钮消失"""
        return self.home_page.login_entrance.wait_until_disappear(timeout)

    def logout(self):
        """站点退出入口在个人中心，自动化里用清态方式回到未登录，更稳"""
        self.clear_login_state()
        return self.home_page.login_entrance.wait_exist(20000)

    # ---------------- 登录态复用 ----------------
    def save_login_state(self, path=STORAGE_STATE_FILE):
        """登录成功后保存 storage_state，其它用例可免密复用"""
        return self.driver.save_storage_state(path)
