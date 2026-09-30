# encoding: utf-8
"""
定位器解析：把 page 里声明的 dict 转成 playwright 的 Locator

被测站点用的是 CSS Modules，class 名带构建哈希（如 loginButton-DHd2v），
发版就会变，所以定位优先级刻意排成：testid > role > text > placeholder > css > xpath，
css 也建议写成前缀匹配 [class*="loginButton-"]。

支持的 key：
    testid      : 'login-btn'                     -> get_by_test_id
    role        : ('button', '登录/注册')          -> get_by_role(role, name=...)
    text        : '登录/注册'                      -> get_by_text(..., exact=False)
    exact_text  : '登录'                          -> get_by_text(..., exact=True)
    placeholder : '请输入关键词搜索'                -> get_by_placeholder
    css / xpath : 常规选择器
额外 key：
    frame       : ['iframe[src*="udb-frame-pc"]', 'iframe#lgn']  嵌套 iframe 链
    index       : 2   命中多个时取第几个（默认 0）
"""
PRIORITY = ['testid', 'role', 'text', 'exact_text', 'placeholder', 'css', 'xpath']


class Locator:

    def __init__(self, device, locator: dict):
        self.d = device
        self.locator = locator or {}

    def get_platform_locator(self):
        """取当前端(pc/h5)的定位配置，当前端没配则回退到另一端"""
        platform_locator = self.locator.get(self.d.platform)
        if platform_locator:
            return platform_locator
        for value in self.locator.values():
            if value:
                return value
        raise ValueError(f'定位器为空或未配置 {self.d.platform}: {self.locator}')

    def get_root(self, config):
        """有 frame 链则逐层进 frame_locator，否则返回 page"""
        root = self.d.page
        for frame_selector in config.get('frame', []):
            root = root.frame_locator(frame_selector)
        return root

    def build(self, method='default'):
        """返回 playwright Locator 对象"""
        config = self.get_platform_locator()
        root = self.get_root(config)
        key = method if method != 'default' else self._first_key(config)
        value = config[key]

        if key == 'testid':
            locator = root.get_by_test_id(value)
        elif key == 'role':
            role, name = value if isinstance(value, (tuple, list)) else (value, None)
            locator = root.get_by_role(role, name=name) if name else root.get_by_role(role)
        elif key == 'text':
            locator = root.get_by_text(value, exact=False)
        elif key == 'exact_text':
            locator = root.get_by_text(value, exact=True)
        elif key == 'placeholder':
            locator = root.get_by_placeholder(value)
        elif key == 'css':
            locator = root.locator(value)
        elif key == 'xpath':
            locator = root.locator(f'xpath={value}')
        else:
            raise ValueError(f'不支持的定位方式: {key}')

        index = config.get('index')
        return locator.nth(index) if index is not None else locator

    def _first_key(self, config):
        for key in PRIORITY:
            if key in config:
                return key
        raise ValueError(f'定位器缺少可用的定位方式: {config}')

    def __repr__(self):
        try:
            config = self.get_platform_locator()
            key = self._first_key(config)
            return f'{key}={config[key]}'
        except Exception:
            return str(self.locator)
