#!/usr/bin/env python
# encoding: utf-8
from datetime import datetime
import copy
import json

from vikidm.biztree import BizTree, Agent, BizUnit, Agency
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
        try:
            return self._items.pop()
        except IndexError:
            return None

    def top(self):
        try:
            return self._items[-1]
        except IndexError:
            return None

    def __len__(self):
        return len(self._items)

    def __str__(self):
        return "\n".join(["Stack:"] + [c.tag for c in self._items])


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
        self._sid = ""

    def init_from_db(self, domain, version):
        pass

    def init_from_json_files(self, paths):
        for fpath in paths:
            with open(fpath, "r") as file_obj:
                json_data = json.load(file_obj)
                self._add_biz_from_json(json_data)
        self._init_context()
        node = self._biz_tree.get_node('root')
        node.state = BizUnit.STATUS_STACKWAIT
        self._stack.push(node)
        self.execute_focus_agent()

    def execute_focus_agent(self):
        #  TODO: RESET CONCEPT #
        state = Agency.STATUS_CONTINUE
        while state in [Agency.STATUS_CONTINUE, Agent.STATUS_TARGET_COMPLETED]:
            focus_unit = self._stack.top()

            if isinstance(focus_unit, Agency):
                state, event_id = focus_unit.execute()
                # push child node
                # state = continue
                pass
            elif isinstance(focus_unit, Agent):
                if focus_unit.status == focus_unit.STATUS_TRIGGERED:
                    state, event_id = focus_unit.execute()
                    return event_id
                elif focus_unit.status == focus_unit.STATUS_TARGET_COMPLETED:
                    self._stack.pop()
            print state

    def process_concepts(self, sid, concepts):
        """
        :concepts: 概念集合
        """
        #  TODO: 看状态决定流程 #
        # input or inform
        #bizunit = self._stack.pop()
        #bizunit.type_
        self._sid = sid
        self._update_concepts(concepts)
        self._mark_completed_bizunits()

        bizunits = list(self._get_triggered_bizunits())
        if bizunits:
            assert(len(bizunits) == 1)
            bizunits[0].status = BizUnit.STATUS_TRIGGERED
            self._stack.push(bizunits[0])

        return self.execute_focus_agent()

    def process_confirm(self, data):
        if data['sid'] != self._sid:
            return {
                'error_code': 0,
                'error_msg': ''
            }

        if data['error_code'] != 0:
            # push exception
            pass
        else:
            focus_unit = self._stack.top()
            assert(isinstance(focus_unit, Agent))
            if focus_unit.type_ == Agent.TYPE_INPUT:
                focus_unit.status = BizUnit.STATUS_WAIT_TARGET
            elif focus_unit.type_ == BizUnit.TYPE_INFORM:
                focus_unit.status = BizUnit.STATUS_ACTION_COMPLETED
            else:
                assert(False)
        self.execute_focus_agent()



        pass

    def _update_concepts(self, concepts):
        for concept in concepts:
            self._context.update_concept(concept.key, concept)

    def _add_biz_from_json(self, json_data):
        self._biz_tree.add_subtree_from_json(json_data)

    def _init_context(self):
        for bizunit in self._biz_tree.all_nodes_itr():
            if isinstance(bizunit, Agent):
                for concept in bizunit.trigger_concepts:
                    concept = copy.deepcopy(concept)
                    self._context.add_concept(concept)

    def _get_triggered_bizunits(self):
        for bizunit in self._biz_tree.all_nodes_itr():
            if isinstance(bizunit, Agent):
                is_focus = all([self._context.satisfied(c) for c in bizunit.trigger_concepts])
                if is_focus:
                    if isinstance(bizunit, Agent) and bizunit.agency_entrance:
                        yield self._biz_tree.parent(bizunit.identifier)
                    else:
                        # 如果多个，都执行，就需要多个反馈，可能需要主动推送功能。
                        yield bizunit

    def _mark_completed_bizunits(self):
        """
        :returns: list of completed bizunit
        """
        #  TODO: unit test #
        for bizunit in self._biz_tree.all_nodes_itr():
            if isinstance(bizunit, Agent):
                completed = all([self._context.is_dirty(c) for c in bizunit.target_concepts])
                if bizunit.target_concepts and completed:
                    bizunit.target_completed = True
