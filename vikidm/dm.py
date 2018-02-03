#!/usr/bin/env python
# encoding: utf-8
from datetime import datetime
import copy
import json

from vikidm.biztree import BizTree, Agent
from vikidm.context import Context


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
        self._context = Context()


class DialogInterface(object):
    """ 对话管理和NLU，终端的接口。"""
    def __init__(self):
        pass


class DialogEngine(object):
    """ 对话管理单元 """
    def __init__(self):
        self._context = Context()
        self._biz_tree = BizTree()
        self._stack = Stack()
        self._timer = None
        self._datetime = datetime.now()

    def init(self, domain, version):
        # self.add_biz_from_json()
        # self._init_context()
        pass

    def init_from_json_files(self, paths):
        for fpath in paths:
            with open(fpath, "r") as file_obj:
                json_data = json.load(file_obj)
                self._add_biz_from_json(json_data)
        self._init_context()
        # push root to stack

    def process_request(self, concepts):
        """
        :concepts: 概念集合
        """
        self._update_concepts(concepts)
        self._mark_completed_bizunits()
        bizunit = self._get_focus_bizunit()
        # push biz unit to stack
        # invoke stack.excute()

    def _update_concepts(self, concepts):
        for concept in concepts:
            self._context.update_concept(concept.key, concept)

    def process_confirm(self, data):
        """
        处理终端的执行确认信息。
        """
        pass

    def execute(self):
        """
        """
        pass

    def _add_biz_from_json(self, json_data):
        self._biz_tree.add_subtree_from_json(json_data)

    def _init_context(self):
        for bizunit in self._biz_tree.all_nodes_itr():
            if isinstance(bizunit, Agent):
                for concept in bizunit.trigger_concepts:
                    concept = copy.deepcopy(concept)
                    self._context.add_concept(concept)

    def _get_focus_bizunit(self):
        for bizunit in self._biz_tree.all_nodes_itr():
            if isinstance(bizunit, Agent):
                is_focus = all([self._context.satisfied(c) for c in bizunit.trigger_concepts])
                if is_focus:
                    yield bizunit

    def _mark_completed_bizunits(self):
        """
        :returns: list of completed bizunit
        """
        for bizunit in self._biz_tree.all_nodes_itr():
            if isinstance(bizunit, Agent):
                completed = all([self._context.is_dirty(c) for c in bizunit.target_concepts])
                if completed:
                    bizunit.is_complete = True
