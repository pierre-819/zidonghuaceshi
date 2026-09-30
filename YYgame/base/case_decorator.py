# encoding: utf-8
import functools
import threading
import time

from base.constant import PC


def user_num(num):
    """
    用于class的装饰器，声明该class需要的浏览器/用户数
    """
    def decorator(cls):
        cls.user_num = num
        return cls
    return decorator


def case(id, name, user_num=1, creator='测试开发', platform=[PC], stage=0):
    """
    用例信息装饰器
    id:用例ID
    name:用例中文名
    creator:用例创建人
    platform:用例支持的端 pc/h5
    """
    def decorator(func):

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            self.case_id = id
            return func(self, *args, **kwargs)

        wrapper.case_func_name = func.__name__  # 用例函数名
        wrapper.case_id = id  # 用例ID
        wrapper.case_cn_name = name  # 用例中文名
        wrapper.case_creator = creator  # 用例创建人
        wrapper.user_num = user_num  # 浏览器实例数
        wrapper.case_platform = platform  # 用例所支持的端
        wrapper.stage = stage  # 用例阶段
        return wrapper

    return decorator


class MyThread(threading.Thread):
    def __init__(self, func, args, kwargs):
        super(MyThread, self).__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.result = None

    def run(self):
        try:
            self.result = self.func(*self.args, **self.kwargs)
        except Exception:
            pass

    def get_result(self):
        return self.result


def timeout_retry(max_retries=3, seconds=10):
    """超时重试装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                thread = MyThread(func, args=args, kwargs=kwargs)
                thread.daemon = True
                thread.start()

                start_time = time.time()
                while time.time() - start_time <= seconds:
                    result = thread.get_result()
                    if result is not None:
                        return result
                    time.sleep(1)
                retries += 1
            raise TimeoutError(f"Function {func.__name__} timed out {seconds} s after {max_retries} retries.")

        return wrapper
    return decorator
