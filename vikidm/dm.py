#!/usr/bin/env python
# encoding: utf-8
import copy
import json
import logging
import pprint
from datetime import datetime
from threading import Timer
from treelib.tree import NodeIDAbsentError
from vikidm.context import Concept, Context
from vikidm.biztree import BizTree, Agent, BizUnit, Agency, AbnormalHandler, DefaultFailedAgent
from vikidm.util import cms_rpc

log = logging.getLogger(__name__)


class Session(object):
    def __init__(self):
        self._sid = None

    def begin_session(self, sid):
        self._sid = sid

    def valid_session(self, sid):
        return sid >= self._sid

    def end_session(self):
        self._sid = None

    def switch_session(self, sid):
        return self._sid is not None and sid > self._sid


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
            assert(False and "root node always in stack")

    def top(self):
        try:
            return self._items[-1]
        except IndexError:
            assert(False and "root node always in stack")
            return None

    def item(self, index):
        return self._items[index]

    def __len__(self):
        return len(self._items)

    def __repr__(self):
        name = self.__class__.__name__
        items = "\n".join([c.tag for c in self._items])
        kwargs = [
            "items=[\n{0}\n]".format(items)
        ]
        return "%s(%s)" % (name, ", ".join(kwargs))


class DialogEngine(object):
    """ 对话管理单元 """
    def __init__(self):
        self._context = Context()
        self._biz_tree = BizTree()
        self._stack = Stack()
        self._timer = None
        self._datetime = datetime.now()
        self._session = Session()
        self.debug_loop = 0
        self.debug_timeunit = 1  # 为了测试的时候加速时间计数

    def init_from_db(self, domain_name):
        json_tree = cms_rpc.get_json_biztree(domain_name)
        self._biz_tree.init_from_json(json_tree)
        self._init_context()
        node = self._biz_tree.get_node('root')
        node.state = BizUnit.STATUS_STACKWAIT
        self._stack.push(node)
        # self.execute_focus_agent()

    def execute_focus_agent(self):
        event_id = None
        focus_unit = self._stack.top()
        while focus_unit.state in [BizUnit.STATUS_TRIGGERED, Agent.STATUS_TARGET_COMPLETED,
                                   BizUnit.STATUS_ACTION_COMPLETED, BizUnit.STATUS_ABNORMAL,
                                   BizUnit.STATUS_AGENCY_COMPLETED]:
            if focus_unit.state == BizUnit.STATUS_ABNORMAL:
                self._focus_bizunit_out(focus_unit)
                focus_unit = self._stack.top()
                continue

            self.debug_loop += 1
            if isinstance(focus_unit, Agency):
                if focus_unit.state == BizUnit.STATUS_AGENCY_COMPLETED:
                    self._focus_bizunit_out(focus_unit)
                else:
                    log.debug("EXECUTE Agency({0})".format(focus_unit.tag))
                    focus_unit.execute(self._stack)

            elif isinstance(focus_unit, Agent):
                if focus_unit.state == BizUnit.STATUS_TRIGGERED:
                    log.debug("EXECUTE Agent{0})".format(focus_unit.tag))
                    event_id = focus_unit.execute()
                    assert(focus_unit.state == BizUnit.STATUS_WAIT_ACTION_CONFIRM)
                    if focus_unit.timeout == 0:
                        # 默认的异常处理节点倒计时总是为0
                        focus_unit.state = BizUnit.STATUS_ACTION_COMPLETED
                    else:
                        self._countdown(focus_unit.timeout, self._wait_timeout)

                elif focus_unit.state in [BizUnit.STATUS_TARGET_COMPLETED,
                                          BizUnit.STATUS_ACTION_COMPLETED]:
                    self._focus_bizunit_out(focus_unit)

            elif isinstance(focus_unit, AbnormalHandler):
                log.debug("EXECUTE AbnormalHandler({0})".format(focus_unit.handler.tag))
                focus_unit.execute(self._stack, self._biz_tree)
                # log.debug("HANDLE ABNORMAL: state --  %s" % focus_unit.state)
                if focus_unit.state == BizUnit.STATUS_ACTION_COMPLETED:
                    self._stack.pop()

            focus_unit = self._stack.top()
        return event_id

    def _wait_timeout(self):
        focus_unit = self._stack.top()
        log.debug("TIMEOUT Agent({0})".format(focus_unit.tag))
        self._handle_abnormal()

    def _countdown(self, seconds, function, *args, **kwargs):
        self._timer = Timer(seconds * self.debug_timeunit, function, *args, **kwargs)
        self._timer.start()

    def _focus_bizunit_out(self, focus_unit):
        def trigger_parent():
            try:
                parent = self._biz_tree.parent(focus_unit.identifier)
            except NodeIDAbsentError:
                parent = focus_unit.parent
            if parent and parent.is_root() == False and parent.state != BizUnit.STATUS_ABNORMAL:
                parent.state = BizUnit.STATUS_TRIGGERED
                # log.debug("set parent {0} triggered".format(parent.tag))
        self._stack.pop()
        trigger_parent()
        if isinstance(focus_unit, Agent):
            self._reset_focus_concepts(focus_unit)

        old_focus_unit = self._stack.top()
        if old_focus_unit.state == BizUnit.STATUS_WAIT_ACTION_CONFIRM:
            old_focus_unit.state = BizUnit.STATUS_ACTION_COMPLETED

    def _reset_focus_concepts(self, focus_unit):
        for concept in focus_unit.trigger_concepts + focus_unit.target_concepts:
            if concept.life_type == Concept.LIFE_STACK:
                self._context.reset_concept(concept.key)
                log.debug("unit [{0}] reset concept [{1}]".format(focus_unit.tag, concept.key))

    def process_concepts(self, sid, concepts):
        if self._session.switch_session(sid):
            log.debug("SWITH_SESSION")
            self._timer.cancel()

        self._session.begin_session(sid)
        self._update_concepts(concepts)
        self._mark_completed_bizunits()
        bizunits = list(self._get_triggered_bizunits())
        if bizunits:
            assert(len(bizunits) == 1)
            bizunits[0].state = BizUnit.STATUS_TRIGGERED
            self._stack.push(bizunits[0])

        return self.execute_focus_agent()

    def _handle_abnormal(self):
        handler_agent = self._get_abnormal_handler(self._stack.top())
        abnormal = AbnormalHandler(handler_agent, AbnormalHandler.ABNORMAL_FAILED)
        handler_agent.parent = abnormal
        self._stack.push(abnormal)
        self.execute_focus_agent()
        self._session.end_session()
        self._timer.cancel()

    def _handle_success_confirm(self):
        focus_unit = self._stack.top()
        assert(isinstance(focus_unit, Agent))
        log.debug("CONFIRM: {0}".format(focus_unit.tag))
        if focus_unit.type_ == Agent.TYPE_INPUT:
            assert(focus_unit.state == Agent.STATUS_WAIT_ACTION_CONFIRM)
            focus_unit.state = BizUnit.STATUS_WAIT_TARGET
        elif focus_unit.type_ == Agent.TYPE_INFORM:
            focus_unit.state = BizUnit.STATUS_ACTION_COMPLETED
        else:
            assert(False)
        self.execute_focus_agent()
        self._session.end_session()
        self._timer.cancel()

    def process_confirm(self, data):
        if not self._session.valid_session(data['sid']):
            return {
                'code': 0,
                'message': ''
            }
        if data['code'] != 0:
            self._handle_abnormal()
            return
        self._handle_success_confirm()

    def _update_concepts(self, concepts):
        for concept in concepts:
            self._context.update_concept(concept.key, concept)

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
                        agency = self._biz_tree.parent(bizunit.identifier)
                        agency.trigger_child = bizunit
                        yield agency
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
                completed = all([self._context.dirty(c) for c in bizunit.target_concepts])
                if bizunit.target_concepts and completed:
                    bizunit.target_completed = True

    def debug_info(self):
        msg = '''
        {0}
        {1}
        {2}
        '''
        return msg.format(str(self._stack), str(self._context),
                          pprint.pformat(self._biz_tree.to_dict(with_data=True)))

    def _get_abnormal_handler(self, agent):
        return DefaultFailedAgent(agent)
