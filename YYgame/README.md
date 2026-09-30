# YYgame Web 自动化测试框架

被测站点：**YY游仓**（游戏账号交易平台）测试环境 https://malltest.yy.com

分层沿用 `yyautomation`（移动端 Appium 框架）的约定，驱动层换成 **Playwright**：
**page 只放定位器，action 放业务步骤，test 只做步骤调用 + 断言**。

## 目录结构

```
YYgame/
├── conftest.py            # 参数解析、浏览器启停、失败截图、trace 落盘
├── pytest.ini             # marker、重跑、报告参数
├── settings.py            # 站点、超时、产物目录、登录态文件路径
├── base/
│   ├── base_test_class.py # BaseTest：userA~userD / config / 失败截图 + console 日志
│   ├── browser_info.py    # 一个浏览器实例 = browser + context + page
│   ├── case_decorator.py  # @case / @user_num / @timeout_retry
│   ├── config.py          # 读 configs/config*.xml
│   ├── constant.py        # pc/h5、chromium/firefox/webkit
│   ├── init.py            # playwright 启动/回收、H5 设备模拟、trace
│   └── user.py            # User：浏览器 + 账号 + 绑定 page/action
├── common/
│   ├── driver.py          # 页面级：open/标签页/iframe/mock接口/登录态/截图
│   ├── element.py         # 元素级：exist/wait_exist/click/input/text...
│   └── locator.py         # 定位器解析：testid>role>text>placeholder>css>xpath
├── configs/config_yygame.xml
├── page/yygame/           # home_page.py、login_page.py
├── action/yygame/         # base_action.py、login_action.py
├── test/yygame/login/     # test_login.py（6 条登录用例）
├── captures/              # 失败截图、console 日志、trace
└── report/
```

## 为什么定位器不用 class

站点是 CSS Modules，class 带构建哈希（`loginButton-DHd2v`、`dialog-PLimT`），**发一次版就变**。
所以定位优先级刻意排成 `testid > role > text > placeholder > css > xpath`，实际用的是：

```python
self.login_entrance_locator = {'pc': {'role': ('button', '登录/注册')}}          # role + 名称
self.protocol_blocker_locator = {'pc': {'css': 'button[aria-label="请先阅读并同意协议"]'}}  # aria-label
self.search_input_locator = {'pc': {'placeholder': '请输入关键词搜索'}}           # placeholder
self.logo_locator = {'pc': {'css': 'a[class*="brand-"]'}}                       # class 前缀兜底
```

## 登录结构（已实测）

```
malltest 主文档
└── article[class*="dialog-"]                    登录弹窗
    ├── button[role=tab] 手机号登录 / YY号登录     aria-selected 标识当前
    ├── button[aria-label="请先阅读并同意协议"]     未勾协议时盖在表单上的拦截层
    ├── button[role=checkbox]                    协议勾选，aria-checked 标识状态
    ├── iframe[title="YY号登录"] → iframe         UDB 页(lgn.yy.com)，账密框在最内层
    │      .E_acct / .E_passwd / .E_login
    └── iframe[title="手机号登录"] → iframe
           input[name=tel] / input[name=code] / #sendcode
```

- 手机号登录要短信码，自动化不可控，**自动化只走 YY号账密**。
- 登录提交接口 `**/lgn/oauth/x2/s/login_asyn.do`，用例断言接口响应，比断 UDB 那个一闪而过的错误提示稳。

## 快速开始

```powershell
cd C:\Users\liaolibing\Desktop\pierre\自动化测试\YYgame
pip install -r requirements.txt
python -m playwright install chromium   # 已装过可跳过

python -m pytest                       # 全量
python -m pytest -m bvt                # 冒烟
python -m pytest --headless=True       # 无头
python -m pytest --html=report/report.html --self-contained-html
```

常用参数：`--browser_type=chromium|firefox|webkit`、`--platform_type=pc|h5`、`--base_url=...`、
`--storage_state=configs/storage/storage_state.json`（免密启动）、`--taskId`、`--round`。

## 跑之前必须填的

`configs/config_yygame.xml` 的 `UserA` 里填 **YY号 + 密码**（需要是免图形验证码的自动化账号）。
没填时依赖账号的 4 条用例会自动 skip，不会误报失败。

## 用例现状（本地实测，2026-08-28）

`configs/config_yygame.xml` 已填真实账号，6 条全部通过（`6 passed in 40s`）：

- `YYGAME-001` 登录弹窗展示且可在手机号/YY号登录间切换
- `YYGAME-002` 未勾选协议时登录表单被拦截，勾选后放开
- `YYGAME-003` YY号账密登录成功
- `YYGAME-004` 密码错误时登录失败且停留在登录弹窗
- `YYGAME-005` 退出登录后回到未登录态
- `YYGAME-006` 登录后刷新页面登录态保持

## 报告与日志的中文编码

Windows 上有两处会把中文变成乱码，框架里都处理了：

- **loguru 写 stderr**：控制台默认 GBK，pytest 抓日志时按 UTF-8 解码 → `??????`。
  `conftest.py` 的 `_setup_utf8_logging()` 把 stdout/stderr 切成 UTF-8，并把控制台输出页设成 65001。
- **pytest-html 写文件**：它用系统默认编码写，但 HTML 里声明的是 `charset=utf-8` → 整页中文乱码。
  `pytest_sessionfinish` 在它写完后统一转成真正的 UTF-8。

另外日志会同时落一份 `report/run.log`（显式 UTF-8，10MB 轮转，留 3 份），控制台编码怎么变都不影响归档。
报告里的「用例名称」列显示的是 `@case` 的用例号 + 中文名，不是函数名。


## 排查失败用例

失败自动落在 `captures/{taskId}_{caseId}_{round}_{浏览器}/`：整页截图 + `console_*.log`（含 pageerror）。
每个 session 结束还会存一份 trace：

```powershell
python -m playwright show-trace captures/trace/0_chromium_pc_0_1.zip
```

trace 可以逐步回放 DOM 快照、网络请求、控制台，定位"哪一步开始不对"比看截图快得多。
用例中想主动留证：`self.screen_shot_to_report(self.userA, tag='点登录前')`。

## 加新用例

1. `page/yygame/xxx_page.py` 加定位器（优先 role/text/aria-label）
2. `action/yygame/xxx_action.py` 组装步骤，继承 `BaseAction`，可用 `self.driver` / `self.home_page`
3. `base/user.py` 里绑定新的 page / action
4. `test/yygame/<模块>/test_xxx.py` 写用例，必须加 `@case`：

```python
@case(id="YYGAME-010", name="搜索商品", user_num=1, creator="liaolibing", platform=[PC])
def test_search(self):
    ...
```

`@case` 缺失或中文名为空会在 setup 阶段直接失败——这是刻意保留 `yyautomation` 的卡点。

## H5 端

`base/init.py` 已接 Playwright 设备模拟（`iPhone 15`），`--platform_type=h5` 即可切换，
page 里补一套 `'h5': {...}` 定位器就能复用同一批 action。当前未写 H5 用例。
