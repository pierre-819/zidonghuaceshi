# encoding: utf-8
"""
YY游仓 PC 站登录用例
账号在 configs/config_yygame.xml 的 UserA 配置，未配置时相关用例自动 skip
"""
import pytest

from base.base_test_class import BaseTest
from base.case_decorator import case, user_num
from base.constant import PC

PLACEHOLDER = ('', None, 'test_account_a', '待填写')


@user_num(1)
class TestLogin(BaseTest):

    def setup_method(self):
        self.userA.base_action.clear_login_state()

    def _require_account(self):
        """没配真实账号就 skip，避免报一堆无效失败"""
        if self.userA.username in PLACEHOLDER or self.userA.password in PLACEHOLDER:
            pytest.skip('未配置真实测试账号，请填 configs/config_yygame.xml 的 UserA')

    @case(id="YYGAME-001", name="登录弹窗展示且可在手机号/YY号登录间切换", user_num=1,
          creator="liaolibing", platform=[PC])
    @pytest.mark.bvt
    def test_login_dialog_and_tab_switch(self):
        assert self.userA.login_action.open_login_dialog(), '点登录/注册后弹窗未出现'
        assert self.userA.login_page.tab_phone.wait_exist(), '缺少手机号登录 tab'
        assert self.userA.login_page.tab_yy.wait_exist(), '缺少YY号登录 tab'

        assert self.userA.login_action.switch_to_yy_tab(), 'YY号登录 tab 未切为选中态'
        assert self.userA.login_page.account_input.wait_exist(), 'YY号登录未展示账号输入框'
        assert self.userA.login_page.password_input.wait_exist(), 'YY号登录未展示密码输入框'

        assert self.userA.login_action.switch_to_phone_tab(), '手机号登录 tab 未切为选中态'
        assert self.userA.login_page.phone_input.wait_exist(), '手机号登录未展示手机号输入框'
        assert self.userA.login_page.send_code_btn.wait_exist(), '手机号登录未展示获取验证码按钮'

    @case(id="YYGAME-002", name="未勾选协议时登录表单被拦截，勾选后放开", user_num=1,
          creator="liaolibing", platform=[PC])
    @pytest.mark.bvt
    def test_protocol_block_before_agree(self):
        self.userA.login_action.open_login_dialog()
        self.userA.login_action.switch_to_yy_tab()

        assert self.userA.login_action.is_protocol_checked() is False, '协议默认应为未勾选'
        assert self.userA.login_page.protocol_blocker.wait_exist(5000), '未勾选协议时应有拦截层'

        assert self.userA.login_action.agree_protocol(), '勾选协议后拦截层未消失'
        assert self.userA.login_action.is_protocol_checked(), '协议勾选状态未更新'

    @case(id="YYGAME-003", name="YY号账密登录成功", user_num=1, creator="liaolibing", platform=[PC])
    @pytest.mark.bvt
    def test_login_success(self):
        self._require_account()
        response = self.userA.login_action.login_by_yy_account(self.userA.username, self.userA.password)
        assert response.status == 200, f'登录接口返回异常: {response.status}'
        assert self.userA.login_action.is_logged_in(), '登录后顶部仍显示登录/注册'
        # 登录成功后存一份登录态，其它用例可以 --storage_state 免密启动
        self.userA.login_action.save_login_state()

    @case(id="YYGAME-004", name="密码错误时登录失败且停留在登录弹窗", user_num=1,
          creator="liaolibing", platform=[PC])
    def test_login_wrong_password(self):
        self._require_account()
        self.userA.login_action.login_by_yy_account(self.userA.username, 'wrong_pwd_9527', check=False)
        assert self.userA.login_page.dialog.wait_exist(5000), '密码错误后登录弹窗不应关闭'
        assert self.userA.home_page.login_entrance.wait_exist(5000), '密码错误竟然登录成功了'

    @case(id="YYGAME-005", name="退出登录后回到未登录态", user_num=1, creator="liaolibing", platform=[PC])
    def test_logout(self):
        self._require_account()
        self.userA.login_action.login_by_yy_account(self.userA.username, self.userA.password)
        assert self.userA.login_action.logout(), '退出后顶部未恢复登录/注册'

    @case(id="YYGAME-006", name="登录后刷新页面登录态保持", user_num=1, creator="liaolibing", platform=[PC])
    def test_login_state_kept_after_refresh(self):
        self._require_account()
        self.userA.login_action.login_by_yy_account(self.userA.username, self.userA.password)
        self.userA.driver.refresh()
        self.userA.home_page.logo.wait_exist(30000)
        assert self.userA.login_action.is_logged_in(), '刷新后登录态丢失'

    def teardown_method(self):
        self.userA.driver.close_other_pages()
