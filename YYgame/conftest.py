# -*- coding: utf-8 -*-
"""
pytest 配置文件，跑用例会自动走到这里
职责：解析参数 -> 启动 playwright 浏览器 -> 绑定 User -> 失败截图/trace -> 结束回收
"""
import locale
import os
import sys

import pytest
from loguru import logger
from py.xml import html

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './')))

from base.config import Config
from base.constant import H5, PC
from base.init import Init
from base.user import User
from settings import BASE_URL, DEFAULT_BROWSER, DEFAULT_PLATFORM, REPORT_DIR, TRACE_DIR

PROJECT_DIR = os.path.dirname(__file__)


def _setup_utf8_logging():
    """
    Windows 控制台默认 GBK，loguru 往 stderr 写中文会变成 ??????，
    报告里“Captured stderr”也就跟着乱码。这里把输出流切成 utf-8 并重建日志 sink。
    """
    if sys.platform == 'win32':
        # 控制台输出页也切到 UTF-8，否则终端里看 utf-8 日志同样是乱码
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass

    for stream_name in ('stdout', 'stderr'):
        stream = getattr(sys, stream_name, None)
        try:
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
        except Exception:
            pass  # pytest 的捕获流可能不支持 reconfigure，忽略即可

    # pytest-html 用系统默认编码写报告，GBK 遇到 ¦ 之类字符会直接抛 UnicodeEncodeError。
    # 把默认编码兜成 utf-8，报告和其它默认编码的文件写入就都安全了。
    locale.getpreferredencoding = lambda do_setlocale=True: 'utf-8'


    log_format = ('{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <7} | '
                  '{name}:{function}:{line} - {message}')
    logger.remove()
    logger.add(sys.stderr, format=log_format, level='INFO', enqueue=False)
    # 再落一份 utf-8 日志文件，控制台编码怎么变都不影响归档
    os.makedirs(REPORT_DIR, exist_ok=True)
    logger.add(os.path.join(REPORT_DIR, 'run.log'), format=log_format, level='INFO',
               encoding='utf-8', rotation='10 MB', retention=3)


_setup_utf8_logging()

case_result = ''
case_names = {}  # nodeid -> 用例中文名，供报告 Description 列使用
config: Config = None
initializer: Init = None
browser_list = []
user_list = []
max_user_num = 1
cls_name = None
task_id = '0'
round = '1'
base_url = ''
browser_name = ''
platform = ''
headless = False
config_file = ''
storage_state = ''
slow_mo = 0
current_case_id = ''


def pytest_addoption(parser):
    parser.addoption("--browser_type", action="store", default="", help="chromium/firefox/webkit")
    parser.addoption("--platform_type", action="store", default="", help="pc 或 h5")
    parser.addoption("--base_url", action="store", default="", help="被测站点地址")
    parser.addoption("--headless", action="store", default="", help="True 则无头运行")
    parser.addoption("--config_file", action="store", default="", help="configs 下的配置文件名")
    parser.addoption("--storage_state", action="store", default="", help="登录态文件，传了则免密启动")
    parser.addoption("--slow_mo", action="store", default="0", help="每步放慢的毫秒数，演示/调试用")
    parser.addoption("--taskId", action="store", default="0", help="平台任务id")
    parser.addoption("--round", action="store", default="1", help="重试轮次")


def pytest_configure(config):
    global task_id, round, base_url, browser_name, platform, headless, config_file, storage_state
    task_id = config.getoption("--taskId")
    round = config.getoption("--round")
    base_url = config.getoption("--base_url")
    browser_name = config.getoption("--browser_type")
    platform = config.getoption("--platform_type")
    headless = config.getoption("--headless") == str(True)
    config_file = config.getoption("--config_file")
    storage_state = config.getoption("--storage_state")
    global slow_mo
    slow_mo = int(config.getoption("--slow_mo") or 0)


@pytest.hookimpl(hookwrapper=True)
def pytest_collection(session):
    """取本次 session 需要的最大浏览器数"""
    yield
    global max_user_num
    case_user_num = [item.function.user_num for item in session.items if hasattr(item.function, 'user_num')]
    max_user_num = max(case_user_num) if case_user_num else max_user_num


def pytest_collection_modifyitems(items):
    """按用例支持的端自动打 marker，同时记录用例中文名供报告展示"""
    for item in items:
        platform_list = getattr(item.function, 'case_platform', [])
        if PC in platform_list:
            item.add_marker(pytest.mark.pc)
        if H5 in platform_list:
            item.add_marker(pytest.mark.h5)
        case_id = getattr(item.function, 'case_id', '')
        case_cn_name = getattr(item.function, 'case_cn_name', '')
        case_names[item.nodeid] = f'{case_id} {case_cn_name}'.strip()


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    global case_result
    result = yield
    report = result.get_result()

    if report.failed and item.cls:
        logger.info('用例失败，开始截图留证')
        case_id = getattr(item.function, 'case_id', item.name)
        item.cls.screen_shot(os.path.join('captures', f'{task_id}_{case_id}_{round}'))

    case_result = report.outcome if report.outcome == 'failed' else 'pass'


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_header(cells):
    cells.insert(1, html.th('用例名称'))


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_row(report, cells):
    """每行都插一格，保证与表头对齐；中文名取自 collection 阶段的映射"""
    cells.insert(1, html.td(case_names.get(report.nodeid, '')))


# ====================== setup / teardown ======================

@pytest.fixture(scope='session')
def init_config():
    global config
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'configs'))
    config = Config(config_path=config_path, config_file=config_file or None)
    return config


@pytest.fixture(scope='session', autouse=True)
def session_setup(init_config, request):
    """session 级：配置 -> 浏览器 -> 用户"""
    request.addfinalizer(lambda: session_teardown(request))

    global config, user_list, browser_list, initializer
    if len(user_list) >= max_user_num:  # 失败重跑时可能重复进入
        return

    config = init_config
    run_browser = browser_name or config.get_browser() or DEFAULT_BROWSER
    run_platform = platform or config.get_platform() or DEFAULT_PLATFORM
    run_url = base_url or config.get_base_url() or BASE_URL
    run_headless = headless or config.get_headless()

    initializer = Init(slow_mo=slow_mo)
    browser_list = initializer.set_local_browsers_config(max_user_num, browser_type=run_browser,
                                                         platform=run_platform, headless=run_headless,
                                                         base_url=run_url)
    initializer.init(browser_list, storage_state=storage_state or None)
    for browser_info in browser_list:
        _attach_console_listener(browser_info)

    uid_list = config.get_user_uid_list()
    username_list = config.get_user_username_list()
    password_list = config.get_user_password_list()
    for i in range(max_user_num):
        user_list.append(User(browser_list[i], uid_list[i], username_list[i],
                              password_list[i], _get_role_by_index(i)))
    logger.info(f'session setup 完成: 浏览器={run_browser}, 端={run_platform}, 站点={run_url}')


def _attach_console_listener(browser_info):
    """把控制台日志挂到 page 上，失败时由 BaseTest 落盘"""
    def bind(page):
        page._console_logs = []
        page.on('console', lambda msg: page._console_logs.append(f'{msg.type}: {msg.text}'[:500]))
        page.on('pageerror', lambda err: page._console_logs.append(f'pageerror: {err}'[:500]))
    bind(browser_info.page)
    browser_info.context.on('page', bind)


def session_teardown(request):
    """保存 trace 并回收浏览器"""
    global user_list
    for browser_info in browser_list:
        trace_path = os.path.join(TRACE_DIR, f'{task_id}_{browser_info.serial}_{round}.zip')
        initializer.stop_trace(browser_info, trace_path)
    if initializer:
        initializer.quit(browser_list)
    user_list = []
    logger.info('\n-----------session teardown-------------\n')


@pytest.fixture(scope='class', autouse=True)
def class_setup(request):
    """class 级：把 user / config 绑到用例类上"""
    request.addfinalizer(lambda: class_teardown(request))
    request.cls.userA = user_list[0] if len(user_list) > 0 else None
    request.cls.userB = user_list[1] if len(user_list) > 1 else None
    request.cls.userC = user_list[2] if len(user_list) > 2 else None
    request.cls.userD = user_list[3] if len(user_list) > 3 else None
    request.cls.config = config
    request.cls.task_id = task_id
    request.cls.sub_task_id = task_id
    request.cls.round = round
    global cls_name
    cls_name = request.cls.__name__


def class_teardown(request):
    logger.info(f'\n--------------------class teardown:{request.cls.__name__} : {case_result}--------------------\n')


@pytest.fixture(scope='function', autouse=True)
def case_setup(request):
    """用例级：校验 @case 信息并打印起止"""
    assert hasattr(request.function, 'case_cn_name'), '请使用@case(id,name)设置用例id和中文名称'
    assert request.function.case_cn_name.strip(), '@case(id,name)中文名称不能为空'
    global current_case_id
    current_case_id = request.function.case_id
    logger.info(f'--------------------case setup:{request.function.case_id} '
                f'{request.function.case_func_name}--------------------')
    request.addfinalizer(lambda: case_teardown(request))


def case_teardown(request):
    logger.info(f'\n--------------------case teardown:{request.function.case_id} '
                f'{request.function.case_func_name} : {case_result}--------------------\n')


def _get_role_by_index(i):
    return ['userA', 'userB', 'userC', 'userD'][i]


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session):
    """
    pytest-html 3.x 写报告用的是系统默认编码（Windows 上是 GBK），
    但它生成的 HTML 里声明的是 charset=utf-8，于是中文在浏览器里全是乱码。
    这里在它写完之后统一转成真正的 UTF-8。
    """
    html_path = getattr(session.config.option, 'htmlpath', None)
    if not html_path or not os.path.exists(html_path):
        return
    with open(html_path, 'rb') as f:
        raw = f.read()
    try:
        raw.decode('utf-8')
        return  # 已经是 utf-8，不用动
    except UnicodeDecodeError:
        pass
    text = raw.decode(locale.getpreferredencoding(False), errors='replace')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(text)
    logger.info(f'报告已转为 UTF-8: {html_path}')

