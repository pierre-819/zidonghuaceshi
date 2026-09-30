# encoding: utf-8
"""
登录弹窗元素。结构（真实探测结果）：

malltest 主文档
└── article[class*="dialog-"]                       登录弹窗
    ├── button[role=tab] 手机号登录 / YY号登录        tab 切换，aria-selected 标识当前
    ├── button[aria-label="请先阅读并同意协议"]        未勾选协议时盖在表单上的拦截层
    ├── button[role=checkbox]                       协议勾选，aria-checked 标识状态
    ├── iframe[title="YY号登录"]  ─┐
    │     └── iframe              ├─ UDB 登录页(lgn.yy.com)，账密输入框在最内层
    ├── iframe[title="手机号登录"] ─┘
    └── button[aria-label="百度账号登录"]

UDB 内层用的是 E_acct / E_passwd / E_login 这类约定 class，比外层哈希 class 稳定。
"""
from common.element import Element

# UDB 登录 iframe 链
YY_FRAME = ['iframe[title="YY号登录"]', 'iframe >> nth=0']
PHONE_FRAME = ['iframe[title="手机号登录"]', 'iframe >> nth=0']

# 账密登录提交的接口，用例里断言响应比断言 UDB 的瞬时提示稳
LOGIN_API = '**/lgn/oauth/x2/s/login_asyn.do'


class LoginPage(object):

    def __init__(self, device):
        self.d = device

        # 弹窗容器
        self.dialog_locator = {
            'pc': {'css': 'article[class*="dialog-"]'},
            'h5': {'css': '[class*="dialog-"]'}
        }
        self.dialog = Element(self.d, self.dialog_locator)

        # 关闭按钮
        self.close_btn_locator = {
            'pc': {'css': 'button[aria-label="关闭登录弹窗"]'}
        }
        self.close_btn = Element(self.d, self.close_btn_locator)

        # tab：手机号登录 / YY号登录
        self.tab_phone_locator = {'pc': {'role': ('tab', '手机号登录')}}
        self.tab_phone = Element(self.d, self.tab_phone_locator)

        self.tab_yy_locator = {'pc': {'role': ('tab', 'YY号登录')}}
        self.tab_yy = Element(self.d, self.tab_yy_locator)

        # 协议勾选框（自定义 button 实现，状态看 aria-checked）
        self.protocol_checkbox_locator = {
            'pc': {'css': 'button[role="checkbox"]'}
        }
        self.protocol_checkbox = Element(self.d, self.protocol_checkbox_locator)

        # 未勾选协议时的拦截层，勾选后消失
        self.protocol_blocker_locator = {
            'pc': {'css': 'button[aria-label="请先阅读并同意协议"]'}
        }
        self.protocol_blocker = Element(self.d, self.protocol_blocker_locator)

        # 协议文案与链接
        self.protocol_text_locator = {'pc': {'css': '[class*="termsText-"]'}}
        self.protocol_text = Element(self.d, self.protocol_text_locator)

        # 忘记密码 / 百度登录
        self.forgot_password_locator = {'pc': {'role': ('link', '忘记密码')}}
        self.forgot_password = Element(self.d, self.forgot_password_locator)

        self.baidu_login_locator = {'pc': {'css': 'button[aria-label="百度账号登录"]'}}
        self.baidu_login_btn = Element(self.d, self.baidu_login_locator)

        # ---------- YY号登录（UDB iframe 内） ----------
        self.account_input_locator = {
            'pc': {'frame': YY_FRAME, 'css': '.E_acct:visible'}
        }
        self.account_input = Element(self.d, self.account_input_locator)

        self.password_input_locator = {
            'pc': {'frame': YY_FRAME, 'css': '.E_passwd:visible'}
        }
        self.password_input = Element(self.d, self.password_input_locator)

        self.login_btn_locator = {
            'pc': {'frame': YY_FRAME, 'css': '.E_login:visible'}
        }
        self.login_btn = Element(self.d, self.login_btn_locator)

        # UDB 错误提示（瞬时展示，可能一闪而过；断言优先用接口响应）
        self.udb_error_tips_locator = {
            'pc': {'frame': YY_FRAME, 'css': '.error, .tips, [class*="err"]'}
        }
        self.udb_error_tips = Element(self.d, self.udb_error_tips_locator)

        # ---------- 手机号登录（UDB iframe 内） ----------
        self.phone_input_locator = {
            'pc': {'frame': PHONE_FRAME, 'css': 'input[name="tel"]'}
        }
        self.phone_input = Element(self.d, self.phone_input_locator)

        self.sms_code_input_locator = {
            'pc': {'frame': PHONE_FRAME, 'css': 'input[name="code"]'}
        }
        self.sms_code_input = Element(self.d, self.sms_code_input_locator)

        self.send_code_btn_locator = {
            'pc': {'frame': PHONE_FRAME, 'css': '#sendcode'}
        }
        self.send_code_btn = Element(self.d, self.send_code_btn_locator)

        self.phone_login_btn_locator = {
            'pc': {'frame': PHONE_FRAME, 'css': '.login-btn'}
        }
        self.phone_login_btn = Element(self.d, self.phone_login_btn_locator)
