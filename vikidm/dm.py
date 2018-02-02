#!/usr/bin/env python
# encoding: utf-8
from datetime import datetime
from threading import Timer
import sched

from vikidm.biztree import BizTree
from vikicommon.log import gen_log as log


class Stack(object):
    """
     模拟栈
    """
    def __init__(self):
        self._items = []

    def is_empty(self):
        return self._items == []

    def push(self, item):
        self._items.append(item)

    def pop(self):
        if not self.is_empty():
            return self._items.pop()

    def peek(self):
        return self._items[len(self._items) - 1]

    def size(self):
        return len(self._items)


class DialogManager(object):
    def __init__(self):
        self._dlg_gate = None
        self._dlg_engine = None


class DialogInterface(object):
    """ 对话管理和NLU，终端的接口。"""
    def __init__(self):
        pass


class DialogEngine(object):
    """ 对话管理单元 """
    def __init__(self):
        self._biz_tree = BizTree()
        self._stack = Stack()
        #self._timer = Timer(1, self.print_time, ())
        self._timer = None
        self._datetime = datetime.now()

    def add_biz_from_json(self, json_data):
        self._biz_tree.add_subtree_from_json(json_data)

    def add_biz_from_json_file(self, fpath):
        self._biz_tree.add_subtree_from_json_file(fpath)

    def process_request(self, concepts):
        """
        :concepts: 概念集合
        """
        pass

    def execute(self):
        """
        """
        pass

    def process_confirm(self, data):
        """
        处理终端的执行确认信息。
        """
        pass

