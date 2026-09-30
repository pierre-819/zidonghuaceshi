import logging
import sys

LOGGER_NAME = "main"
LOG_LEVEL = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']


class MyLogger:
    """与 yyautomation 保持一致的日志封装"""

    def __init__(self, logger_name=LOGGER_NAME,
                 log_level: LOG_LEVEL = None,
                 log_formate="%(asctime)s - %(levelname)s:%(filename)s:%(lineno)d - %(message)s "):
        self.log_level = log_level
        self.logger_name = LOGGER_NAME
        self.formatter = logging.Formatter(log_formate)
        self.logger = logging.getLogger(logger_name)

        try:
            self.logger.setLevel(logging.DEBUG if not log_level else log_level)
        except Exception:
            raise ValueError('log等级必须属于LOG_LEVEL变量')

        self.logger.addHandler(self.get_console_handler())

    def get_logger(self, module_name):
        return logging.getLogger(self.logger_name).getChild(module_name)

    def get_console_handler(self):
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(self.formatter)
        self.logger.handlers.clear()
        return sh

    def info(self, msg, extra=None):
        self.logger.info(msg, extra=extra)

    def error(self, msg, extra=None):
        self.logger.error(str(msg), extra=extra)

    def debug(self, msg, extra=None):
        self.logger.debug(msg, extra=extra)

    def warning(self, msg, extra=None):
        self.logger.warning(msg, extra=extra)
