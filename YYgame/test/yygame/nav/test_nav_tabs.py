# encoding: utf-8
"""
顶部导航 tab 用例：点每个 tab，校验页面正常显示。

未登录态下这 7 个 tab 分三类（实测结论）：
- 免登录可访问：首页 #/、我要买 #/shop/filter、账号回收 #/sell/recycle
- 需要登录：中介担保、账号估值、个人中心 —— 点击后弹登录弹窗
- 待确认：我要卖 —— 未登录点了既不跳转也不弹窗，先只做“不崩”校验
"""
import pytest

from base.base_test_class import BaseTest
from base.case_decorator import case, user_num
from base.constant import PC

# (tab 文案, 期望的 url 片段, 页面上应出现的关键词)
# 关键词尽量选“区块标题”这类结构性文案，别选运营位文案。
# 教训：首页原来断言的是左侧入口「账号选购」，站点把它改成「我要买」之后用例就红了。
FREE_TABS = [
    ('首页', '#/', '游戏推荐'),
    ('我要买', '#/shop/filter', '选择游戏'),
    ('账号回收', '#/sell/recycle', '游戏账号回收'),
]

# 未登录点击后应弹登录弹窗的 tab
LOGIN_REQUIRED_TABS = ['中介担保', '账号估值', '个人中心']


@user_num(1)
class TestNavTabs(BaseTest):

    def setup_method(self):
        self.userA.base_action.open_home()

    @pytest.mark.parametrize('tab_name, url_part, keyword', FREE_TABS,
                             ids=[t[0] for t in FREE_TABS])
    @case(id="YYGAME-101", name="免登录导航tab点击后页面正常显示", user_num=1,
          creator="liaolibing", platform=[PC])
    @pytest.mark.bvt
    def test_free_tab_render(self, tab_name, url_part, keyword):
        url = self.userA.nav_action.click_nav_tab(tab_name)

        assert url_part in url, f'点「{tab_name}」后 url 不对，期望含 {url_part}，实际 {url}'
        assert self.userA.nav_action.active_tab_name() == tab_name, \
            f'点「{tab_name}」后导航高亮是「{self.userA.nav_action.active_tab_name()}」'
        assert self.userA.nav_action.is_page_rendered(keyword), \
            f'「{tab_name}」页面未渲染出关键内容「{keyword}」'
        assert not self.userA.nav_action.js_errors(), \
            f'「{tab_name}」页面有JS报错: {self.userA.nav_action.js_errors()[:2]}'

    @pytest.mark.parametrize('tab_name', LOGIN_REQUIRED_TABS)
    @case(id="YYGAME-102", name="未登录点击需登录的导航tab应弹登录弹窗", user_num=1,
          creator="liaolibing", platform=[PC])
    def test_login_required_tab(self, tab_name):
        self.userA.nav_action.click_nav_tab(tab_name)
        assert self.userA.nav_action.is_login_dialog_popped(), \
            f'未登录点「{tab_name}」没有弹出登录弹窗'

    @case(id="YYGAME-103", name="导航tab数量与文案符合预期", user_num=1,
          creator="liaolibing", platform=[PC])
    def test_nav_tab_list(self):
        expected = ['首页', '我要买', '我要卖', '中介担保', '账号回收', '账号估值', '个人中心']
        actual = [t.strip() for t in self.userA.home_page.nav_tab_texts() if t.strip()]
        assert actual == expected, f'导航文案变了，期望 {expected}，实际 {actual}'

    def teardown_method(self):
        self.userA.driver.close_other_pages()
