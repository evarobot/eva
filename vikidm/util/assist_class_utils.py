# coding=utf-8
# Copyright (C) 2017 AXMTEC.
# https://axm.ai/
"""
定义一些其他类的辅助类
"""


class ReturnResultAssist(object):
    """
    封装返回结果的辅助类
    """
    def __init__(self, reason_desc, from_which_agency):
        """
        @type reason_desc: sting
        @param reason_desc: 返回值, 原因描述
        @param from_which_agency: 来自哪个agency
        """
        self.name = reason_desc
        self.from_which_agency = from_which_agency

    def get_data(self):
        return self
