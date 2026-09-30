# encoding=utf-8

import glob
import os

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


class Config:
    """读取 configs 目录下的 config*.xml，用法与 yyautomation 一致"""

    def __init__(self, config_path="configs", config_file=None):
        self.config_path = config_path
        self.config_file = config_file

        if not config_file:
            config_files = glob.glob(os.path.join(self.config_path, 'config*.xml'))
            assert len(config_files) > 0, '{}目录中不存在配置文件'.format(self.config_path)
            self.config_file = config_files[0]

    # ---------------- 环境 ----------------
    def get_project_name(self):
        project_name = self.getXml('ProjectName')
        return project_name if project_name is not None else 'yygame'

    def get_base_url(self):
        base_url = self.getXml('Env/baseUrl')
        return base_url if base_url is not None else ''

    def get_browser(self):
        browser = self.getXml('Env/browser')
        return browser if browser is not None else ''

    def get_platform(self):
        platform = self.getXml('Env/platform')
        return platform if platform is not None else ''

    def get_headless(self):
        headless = self.getXml('Env/headless')
        return str(headless).lower() == 'true'

    def get_window_size(self):
        """返回 (width, height)，未配置返回 None 表示最大化"""
        size = self.getXml('Env/windowSize')
        if not size or 'x' not in size.lower():
            return None
        width, height = size.lower().split('x')
        return int(width), int(height)

    # ---------------- 账号 ----------------
    def get_user_username_list(self):
        return [self.getXml('UserA/userName'), self.getXml('UserB/userName'),
                self.getXml('UserC/userName'), self.getXml('UserD/userName')]

    def get_user_password_list(self):
        return [self.getXml('UserA/userPassword'), self.getXml('UserB/userPassword'),
                self.getXml('UserC/userPassword'), self.getXml('UserD/userPassword')]

    def get_user_uid_list(self):
        return [self.getXml('UserA/UID'), self.getXml('UserB/UID'),
                self.getXml('UserC/UID'), self.getXml('UserD/UID')]

    def get_userA_username(self):
        return self.getXml('UserA/userName')

    def get_userA_password(self):
        return self.getXml('UserA/userPassword')

    # ---------------- 业务数据 ----------------
    def get_search_keyword(self):
        return self.getXml('Data/searchKeyword')

    def get_game_name(self):
        return self.getXml('Data/gameName')

    def getXml(self, node):
        return self._get_xml_node_value(node)

    def _get_xml_node_value(self, node):
        tree = ET.ElementTree(file=os.path.join(self.config_path, self.config_file))
        element = None
        for elem in tree.iterfind(node):
            element = elem
            break
        return element.text if element is not None else None
