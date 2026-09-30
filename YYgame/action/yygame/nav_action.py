# encoding: utf-8
"""
导航相关动作：点顶部 tab、判断页面是否正常渲染。

“页面正常显示”不能只看截图，要拆成可断言的信号：
1. URL 变成预期的路由
2. 顶部导航高亮切到了对应 tab
3. 页面主体区块渲染出来了，且有非空文案
4. 没有 JS 报错（pageerror）
"""
from loguru import logger

from action.yygame.base_action import BaseAction
from common.element import Element
from page.yygame.login_page import LoginPage

# 测试环境的既有噪声，不作为“页面异常”的判据。新增噪声往这里加，别去放宽断言。
IGNORED_ERRORS = [
    'CORS policy',                 # 测试域被判为 local address space
    'ERR_CONNECTION_REFUSED',      # 图片/服务在测环境没起
    'ERR_FAILED',
    'image load failed',           # 商品图 CDN 在测试环境不稳
    'publess-web',                 # 配置中心拉取失败
    'mlog.bigda.com',              # 埋点上报
    'j.gif',
]


class NavAction(BaseAction):

    def __init__(self, device):
        super().__init__(device)
        self.login_page = LoginPage(device)

    def click_nav_tab(self, name):
        """点顶部导航；若点击后开了新标签页，自动切过去"""
        logger.info(f'点击导航: {name}')
        before = self.driver.page_count()
        self.home_page.nav_tab(name).wait_and_click(15000)
        self.driver.sleep(2)  # SPA 路由切换 + 首屏渲染
        if self.driver.page_count() > before:
            self.driver.switch_to_latest_page()
        return self.driver.current_url

    def active_tab_name(self):
        """当前高亮的导航文案"""
        return self.home_page.active_nav.text()

    def is_page_rendered(self, keyword='', timeout=15000):
        """
        页面是否渲染正常：主体区块出现 + 页面上能等到关键词。

        注意这里等关键词用的是 Element.wait_exist（会轮询到超时），
        而不是取一次 document.innerText 就判断——首屏懒加载慢一点就会误报失败。
        """
        if not self.home_page.page_section.wait_exist(timeout):
            logger.info('页面主体区块未渲染')
            return False
        if not keyword:
            return True
        keyword_element = Element(self.d, {'pc': {'text': keyword}, 'h5': {'text': keyword}})
        if not keyword_element.wait_exist(timeout):
            body_text = self.driver.execute_js('() => document.body.innerText')
            logger.info(f'页面未出现关键词「{keyword}」，实际开头: {body_text[:80]}')
            return False
        return True

    def is_login_dialog_popped(self, timeout=8000):
        """未登录点需要登录的入口时，是否弹出登录弹窗"""
        return self.login_page.dialog.wait_exist(timeout)

    def js_errors(self, ignore=None):
        """
        返回页面里“值得关心”的 JS 报错。

        测试环境本身噪声很大（跨域被拒、图片 CDN 连不上、埋点上报失败），
        这些不代表页面坏了，所以默认过滤掉。想看全部就传 ignore=[]。
        """
        ignore = IGNORED_ERRORS if ignore is None else ignore
        errors = [log for log in self.driver.console_logs() if log.startswith(('pageerror', 'error'))]
        return [e for e in errors if not any(noise in e for noise in ignore)]
