# encoding: utf-8
"""
YY游仓首页元素。定位器全部来自真实页面探测（malltest.yy.com）。

站点用 CSS Modules，class 带构建哈希（loginButton-DHd2v），发版会变，
所以这里优先用 role / text / aria-label / placeholder，class 只做前缀匹配兜底。
"""
from common.element import Element


class HomePage(object):

    def __init__(self, device):
        self.d = device

        # 顶部 logo（YY游仓）
        self.logo_locator = {
            'pc': {'css': 'a[class*="brand-"]'},
            'h5': {'css': '[class*="logo"]'}
        }
        self.logo = Element(self.d, self.logo_locator)

        # 搜索输入框
        self.search_input_locator = {
            'pc': {'placeholder': '请输入关键词搜索'},
            'h5': {'placeholder': '请输入关键词搜索'}
        }
        self.search_input = Element(self.d, self.search_input_locator)

        # 搜索按钮
        self.search_btn_locator = {
            'pc': {'role': ('button', '搜索')},
            'h5': {'role': ('button', '搜索')}
        }
        self.search_btn = Element(self.d, self.search_btn_locator)

        # 顶部“登录/注册”按钮（未登录态）
        self.login_entrance_locator = {
            'pc': {'role': ('button', '登录/注册'), 'index': 0},
            'h5': {'role': ('button', '登录/注册'), 'index': 0}
        }
        self.login_entrance = Element(self.d, self.login_entrance_locator)

        # 右侧个人面板里的“登录/注册”文案，登录后会变成昵称
        self.user_name_guest_locator = {
            'pc': {'css': '[class*="userNameGuest-"]'}
        }
        self.user_name_guest = Element(self.d, self.user_name_guest_locator)

        # 登录后的用户名/昵称区域
        self.user_name_locator = {
            'pc': {'css': '[class*="userName-"]'}
        }
        self.user_name = Element(self.d, self.user_name_locator)

        # 顶部导航（首页/我要买/我要卖/中介担保/账号回收/账号估值/个人中心）
        self.nav_tab_locator = {
            'pc': {'css': 'a[class*="tab-"]'}
        }
        self.nav_tab_group = Element(self.d, self.nav_tab_locator)

        # 个人中心入口
        self.person_center_locator = {
            'pc': {'role': ('link', '个人中心')}
        }
        self.person_center = Element(self.d, self.person_center_locator)

        # 下载APP / 商家入驻
        self.download_app_locator = {'pc': {'role': ('link', '下载APP')}}
        self.download_app = Element(self.d, self.download_app_locator)

        self.merchant_locator = {'pc': {'role': ('link', '商家入驻')}}
        self.merchant_entrance = Element(self.d, self.merchant_locator)

        # 商品卡片列表（游戏推荐下方）
        self.goods_card_locator = {
            'pc': {'css': '[class*="item-"][class*="jcQh"], [class*="card-"]'}
        }
        self.goods_card = Element(self.d, self.goods_card_locator)

        # 当前高亮的导航（class 里带 tabActive）
        self.active_nav_locator = {
            'pc': {'css': 'a[class*="tabActive"]'}
        }
        self.active_nav = Element(self.d, self.active_nav_locator)

        # 面包屑/页面主体区块，用来判断二级页有没有渲染出来
        self.page_section_locator = {
            'pc': {'css': '[class*="section-"], [class*="main-"], [class*="page-"]'}
        }
        self.page_section = Element(self.d, self.page_section_locator)

    def nav_tab(self, name):
        """
        按文案取导航 tab。导航是动态的一组同类元素，
        与其为每个 tab 声明一个属性，不如给一个按名字取的方法。
        """
        return Element(self.d, {
            'pc': {'role': ('link', name)},
            'h5': {'text': name}
        })

    def nav_tab_texts(self):
        """取顶部导航所有文案，用于校验导航项没被误删/改名"""
        return self.nav_tab_group.texts()
