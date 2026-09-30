# encoding: utf-8
"""
测试基类：定义用例可用的 User / Config，以及失败时的截图与控制台日志留证
"""
import os
import time

from loguru import logger

from base.config import Config
from base.user import User


class BaseTest(object):
    userA: User = None
    userB: User = None
    userC: User = None
    userD: User = None
    config: Config = None
    task_id = None
    round = 1
    is_test_env = True
    sub_task_id = None
    custom_screen_folders = []
    case_id = None

    @classmethod
    def screen_shot(cls, pic_path):
        """用例失败时逐个浏览器截图 + 存控制台日志，返回产物目录列表"""
        screen_folders = []
        for user in (cls.userA, cls.userB, cls.userC, cls.userD):
            if not user:
                continue
            try:
                pic_folder = f'{pic_path}_{user.device.serial}'
                os.makedirs(pic_folder, exist_ok=True)
                screen_folders.append(pic_folder)
                now_time = time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
                screen_file = os.path.join(pic_folder, f'screenshot_{user.role}_{now_time}.png')
                user.driver.screenshot(screen_file, full_page=True)
                logger.info(f'截图成功: {screen_file}')
                cls._save_console_log(user, pic_folder, now_time)
            except Exception as e:
                logger.info(f'screen_shot exception: {e}')
        return screen_folders

    @classmethod
    def _save_console_log(cls, user, folder, now_time):
        """conftest 建页时挂了 console 监听，这里把收集到的日志落盘"""
        logs = user.driver.console_logs()
        if not logs:
            return
        log_file = os.path.join(folder, f'console_{user.role}_{now_time}.log')
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(logs))

    def screen_shot_to_report(self, user: User, tag=''):
        """用例执行中主动留证"""
        try:
            pic_folder = os.path.join('captures',
                                      f'{self.sub_task_id}_{self.case_id}_{self.round}_{user.device.serial}')
            os.makedirs(pic_folder, exist_ok=True)
            if pic_folder not in self.custom_screen_folders:
                self.custom_screen_folders.append(pic_folder)
            now_time = time.strftime('%Y%m%d_%H%M%S', time.localtime(time.time()))
            screen_file = os.path.join(pic_folder, f'{tag or "custom"}_{now_time}.png')
            return user.driver.screenshot(screen_file)
        except Exception as e:
            logger.info(f'screen_shot_to_report exception: {e}')
            return None
