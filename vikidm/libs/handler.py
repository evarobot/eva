#!/usr/bin/env python
# encoding: utf-8
import copy
import functools
import sys
import logging

from tornado.web import RequestHandler
from tornado.escape import json_decode, json_encode
log = logging.getLogger(__name__)

HTTP_METHOD = ["get", "post", "put", "delete", "head", "options"]


def exception_filter(func):
    "装饰器：处理handler异常"
    @functools.wraps(func)
    def _wrap(handler, *args, **kwargs):
        try:
            ret = func(handler, *args, **kwargs)
            return ret
        except HttpError as e:
            caller = sys._getframe().f_back.f_code.co_filename
            if "viki" in caller:  # 调用者是项目的代码，继续往上抛
                raise e
            handler.on_http_error(e.code, e.errname, e.errmsg)
    return _wrap


class HttpError(Exception):

    def __init__(self, code, errname, errmsg):
        self.code = code
        self.errname =errname
        self.errmsg = errmsg
        return super(Exception, self).__init__(errmsg)


class Versioned(object):
    """
        Decorator for different api version.

        Examples:

            from viki_qa.libs.handler import Versioned

            @Versioned.get('1.0')
            def get_v1(...):
                print 'GET method if version >= v1.0'

            @Versioned.post('1.0')
            def post_func(...):
                print 'POST  method if version >= v1.0'
    """

    @classmethod
    def new_decorator(cls, method):
        @classmethod
        def decorator(cls, version):
            def wrap(handler_func):
                @functools.wraps(handler_func)
                def _true_handler(*args, **kwargs):
                    return handler_func(*args, **kwargs)
                _true_handler._version_info = (method, version)
                return _true_handler
            return wrap
        setattr(cls, method, decorator)
        return decorator

    @classmethod
    def init_decorators(cls):
        for method in HTTP_METHOD:
            cls.new_decorator(method)

Versioned.init_decorators()


class VersionedHandlerMeta(type):
    def __new__(metacls, name, bases, dct):
        for method in HTTP_METHOD:
            dct.setdefault("_versioned_handlers", {}).setdefault(method, {})
        for k in copy.copy(dct):
            func = dct[k]
            if hasattr(func, "_version_info"):
                method, version = func._version_info
                dct["_versioned_handlers"][method][version] = func.__name__

            if callable(func):
                dct[k] = exception_filter(func)
        return super(VersionedHandlerMeta, metacls).__new__(metacls, name, bases, dct)


class VersionedHandler(RequestHandler):
    __metaclass__ = VersionedHandlerMeta

    def get_version(self):
        raise NotImplementedError

    def write_json(self, json_dict):
        self.set_header("Content-Type", "Application/json")
        self.write(json_encode(json_dict))
        self.finish()

    def __getattribute__(self, name):
        if name in HTTP_METHOD:
            handlers = self._versioned_handlers[name]
            version = self.get_version()
            if version in handlers:
                name = handlers[version]
        return super(VersionedHandler, self).__getattribute__(name)


class RobotAPIHandler(VersionedHandler):
    """发给机器人的API基类"""

    def set_default_headers(self):
        # COR
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

    def options(self):
        # no body
        self.set_status(204)
        self.finish()

    def prepare(self):
        data_raw = self.request.body
        try:
            data = json_decode(data_raw)
            self.data = data
        except:
            log.error('params are not valid json: %s' % data_raw)
            return self.write_json({ 'error': '参数错误'})

    def get_version(self):
        return str(self.data.get("version", ""))

    def get_current_user(self):
        return ""
