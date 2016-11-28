# coding=utf-8
import sys
sys.path.append('..')
from response_code import RET
import functools


def required_login(func):
    @functools.wraps(func)
    def wrapper(request_handler_obj, *args, **kwargs):
        ret = request_handler_obj.get_current_user()
        if not ret:
            return request_handler_obj.write(dict(errorno=RET.SESSIONERR, errormsg=u'用户未登录'))
        else:
            func(request_handler_obj, *args, **kwargs)
    return wrapper
