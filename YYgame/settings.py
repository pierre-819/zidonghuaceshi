# encoding: utf-8
import os

PROJECT_DIR = os.path.dirname(__file__)

# 被测站点：YY游仓（游戏账号交易平台）测试环境
BASE_URL = 'https://malltest.yy.com'

# chromium / firefox / webkit
DEFAULT_BROWSER = 'chromium'

# pc / h5，决定 page 里取哪一套定位器
DEFAULT_PLATFORM = 'pc'

# 超时（毫秒，playwright 单位）
ACTION_TIMEOUT = 15000  # 元素操作默认超时
NAVIGATION_TIMEOUT = 60000  # 页面跳转超时
ELEMENT_TIMEOUT = 15000  # Element 等待默认超时

# 产物目录
CAPTURE_DIR = os.path.join(PROJECT_DIR, 'captures')
TRACE_DIR = os.path.join(PROJECT_DIR, 'captures', 'trace')
REPORT_DIR = os.path.join(PROJECT_DIR, 'report')

# 登录态文件：登录一次后保存，其它用例免密复用
STORAGE_STATE_DIR = os.path.join(PROJECT_DIR, 'configs', 'storage')
STORAGE_STATE_FILE = os.path.join(STORAGE_STATE_DIR, 'storage_state.json')
