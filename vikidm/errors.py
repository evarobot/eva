#!/usr/bin/env python
# encoding: utf-8


class DMError(Exception):
    msg = None

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.message = str(self)

    def __str__(self):
        msg = self.msg.format(**self.kwargs)
        return msg

    __unicode__ = __str__
    __repr__ = __str__


class RPCError(DMError):
    msg = "RPC远程调用失败"
