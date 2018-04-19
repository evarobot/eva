#!/usr/bin/env python
# encoding: utf-8
import copy
import logging
import pprint
import time
from datetime import datetime
from treelib.tree import NodeIDAbsentError

from vikicommon.timer import TimerReset
from vikidm.context import Context
from vikidm.biztree import (
    BizTree,
    Agent,
    BizUnit,
    Agency,
    AbnormalHandler,
    DefaultHandlerAgent,
    TargetAgency
)
from vikidm.util import cms_rpc
from vikidm.config import ConfigDM

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

    def new_session(self, sid):
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
        self.is_waiting = False

    def init_from_db(self, domain_name):
        json_tree = cms_rpc.get_json_biztree(domain_name)
        self._biz_tree.init_from_json(json_tree)
        self._init_context()
        node = self._biz_tree.get_node(self._biz_tree.root)
        node.set_state(BizUnit.STATUS_STACKWAIT)
        self._stack.push(node)

    def execute_focus_agent(self):
        event_id = None
        focus_unit = self._stack.top()
        while focus_unit.executable():
            if focus_unit.state in [BizUnit.STATUS_ABNORMAL, BizUnit.STATUS_TARGET_COMPLETED]:
                self._focus_bizunit_out(focus_unit)
                focus_unit = self._stack.top()
                continue

            self.debug_loop += 1
            #  TODO:  多态替代判断
            if isinstance(focus_unit, Agency):
                if focus_unit.state == BizUnit.STATUS_AGENCY_COMPLETED:
                    self._focus_bizunit_out(focus_unit)
                else:
                    log.debug("EXECUTE Agency({0})".format(focus_unit.tag))
                    focus_unit.execute(self._stack, self._biz_tree, self._context)

                    if focus_unit.state in [BizUnit.STATUS_DELAY_EXIST, BizUnit.STATUS_WAIT_TARGET]:
                        self._start_timer(focus_unit.tag, ConfigDM.input_timeout, self._inputwait_timeout)
                        log.debug("START_TIMER BizUnit({0})".format(focus_unit.tag))
                        break

            elif isinstance(focus_unit, Agent):
                if focus_unit.state == BizUnit.STATUS_TRIGGERED:
                    log.debug("EXECUTE Agent({0})".format(focus_unit.tag))
                    event_id = focus_unit.execute()
                    assert(focus_unit.state == BizUnit.STATUS_WAIT_ACTION_CONFIRM)
                    if focus_unit.timeout == 0:
                        # 默认的异常处理节点倒计时总是为0
                        focus_unit.set_state(BizUnit.STATUS_ACTION_COMPLETED)
                    else:
                        self._start_timer(focus_unit.tag, focus_unit.timeout, self._actionwait_timeout)
                        log.debug("START_TIMER BizUnit({0})".format(focus_unit.tag))

                elif focus_unit.state in [BizUnit.STATUS_TARGET_COMPLETED,
                                          BizUnit.STATUS_ACTION_COMPLETED]:
                    self._focus_bizunit_out(focus_unit)

            elif isinstance(focus_unit, AbnormalHandler):
                log.debug("EXECUTE AbnormalHandler({0})".format(focus_unit.handler.tag))
                focus_unit.execute(self._stack, self._biz_tree)
                # log.debug("HANDLE ABNORMAL: state --  %s" % focus_unit.state)
                if focus_unit.state == BizUnit.STATUS_ACTION_COMPLETED:
                    self._stack.pop()
                    focus_unit.set_state(BizUnit.STATUS_TREEWAIT)

            focus_unit = self._stack.top()


        return event_id

    def _actionwait_timeout(self):
        delta = (time.time() - self._start_time) / self.debug_timeunit
        focus_unit = self._stack.top()
        log.debug("ACTION_TIMEOUT BizUnit({0}) {1}".format(focus_unit.tag, delta))
        self._handle_abnormal(AbnormalHandler.ABNORMAL_ACTION_TIMEOUT)

    def _inputwait_timeout(self):
        delta = (time.time()- self._start_time) / self.debug_timeunit
        focus_unit = self._stack.top()
        log.debug("INPUT_TIMEOUT BizUnit({0}) {1}".format(focus_unit.tag, delta))
        self._handle_abnormal(AbnormalHandler.ABNORMAL_INPUT_TIMEOUT)

    def _handle_abnormal(self, abnormal_type):
        self._cancel_timer()
        log.debug("CANCEL_TIMER BizUnit({0})".format(self._timer.owner))
        abnormal = AbnormalHandler(self._stack.top(), abnormal_type)
        self._stack.push(abnormal)
        self.execute_focus_agent()
        self._session.end_session()

    def _focus_bizunit_out(self, _to_pop_unit):
        self._stack.pop()
        log.debug("POP_STACK: BizUnit({0}) \n{1}".format(_to_pop_unit.tag, self._stack))
        _to_pop_unit.set_state(BizUnit.STATUS_TREEWAIT)
        _to_pop_unit.reset_concepts(self._biz_tree, self._context)

        focus_unit = self._stack.top()
        try:
            parent = self._biz_tree.parent(_to_pop_unit.identifier)
        except NodeIDAbsentError:
            # abnormal node
            parent = None
        if parent and parent != focus_unit:
            self._switch_to_old_round()
        else:
            focus_unit.activate()

    def _switch_to_old_round(self):
        old_session_unit = self._stack.top()
        if isinstance(old_session_unit, Agent):
            log.debug("ROUND_RETURN BizUnit({0})".format(old_session_unit.tag))
            if old_session_unit.state == BizUnit.STATUS_WAIT_ACTION_CONFIRM:
                old_session_unit.set_state(BizUnit.STATUS_ACTION_COMPLETED)
            if old_session_unit.state == BizUnit.STATUS_WAIT_TARGET:
                raise NotImplementedError
        elif isinstance(old_session_unit, TargetAgency):
            log.debug("ROUND_RETURN BizUnit({0})".format(old_session_unit.tag))
            old_session_unit.restore_context(self._context)

    def _cancel_timer(self):
        self.is_waiting = False
        self._timer.cancel()

    def _start_timer(self, s_bizunit, seconds, function, *args, **kwargs):
        assert(self.is_waiting == False)
        self._timer = TimerReset(s_bizunit, seconds * self.debug_timeunit, function, *args, **kwargs)
        self._start_time = time.time()
        self.is_waiting = True
        self._timer.start()

    def process_concepts(self, sid, concepts):
        if self._session.new_session(sid) or self.is_waiting:
            # Agency.STATUS_WAIT_TARGET 下有可能引发切换session
            # could be a remote error or a round switch
            log.debug("IGNORE_OLD_SESSION")
            self._cancel_timer()
            log.debug("CANCEL_TIMER BizUnit({0})".format(self._timer.owner))

        self._session.begin_session(sid)
        self._update_concepts(concepts)
        self._mark_completed_bizunits()
        bizunits = self._get_triggered_bizunits()
        if bizunits:
            bizunits[0].set_state(BizUnit.STATUS_TRIGGERED)
            self._stack.push(bizunits[0])
        return self.execute_focus_agent()

    def _handle_success_confirm(self):
        focus_unit = self._stack.top()
        assert(isinstance(focus_unit, Agent))
        log.debug("CONFIRM: {0}".format(focus_unit.tag))
        self._cancel_timer()
        log.debug("CANCEL_TIMER BizUnit({0})".format(self._timer.owner))
        if focus_unit.type_ == Agent.TYPE_INPUT:
            assert(focus_unit.state == Agent.STATUS_WAIT_ACTION_CONFIRM)
            focus_unit.set_state(BizUnit.STATUS_WAIT_TARGET)
            log.debug("WAIT_INPUT Agent({0})".format(focus_unit.tag))
        elif focus_unit.type_ == Agent.TYPE_INFORM:
            focus_unit.set_state(BizUnit.STATUS_ACTION_COMPLETED)
        else:
            assert(False)
        self.execute_focus_agent()
        self._session.end_session()

    def process_confirm(self, data):
        ret = {
            'code': 0,
            'message': ''
        }
        if not self._session.valid_session(data['sid']):
            return ret
        if data['code'] != 0:
            self._handle_abnormal(AbnormalHandler.ABNORMAL_ACTION_FAILED)
        else:
            self._handle_success_confirm()
        return ret

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
        # 如果多个，都执行，就需要多个反馈，可能需要主动推送功能。
        # 目前只支持返回一个。
        for bizunit in self._biz_tree.all_nodes_itr():
            if isinstance(bizunit, Agent):
                trigger_satisified = all([self._context.satisfied(c) for c in bizunit.trigger_concepts])
                if not trigger_satisified:
                    continue
                if bizunit.type_ == Agent.TYPE_INPUT:
                    targets_completed = all([self._context.dirty(c) for c in bizunit.target_concepts])
                    if targets_completed:
                        continue
                if isinstance(bizunit, Agent) and bizunit.agency_entrance:
                    agency = self._biz_tree.parent(bizunit.identifier)
                    agency.trigger_child = bizunit
                    #if agency.state == BizUnit.STATUS_TREEWAIT:
                        #return []
                    return [agency]
                else:
                    return [bizunit]

    def _mark_completed_bizunits(self):
        for bizunit in self._biz_tree.all_nodes_itr():
            if isinstance(bizunit, Agent):
                completed = all([self._context.dirty(c) for c in bizunit.target_concepts])
                if bizunit.target_concepts and completed:
                    bizunit.target_completed = True
                    bizunit.set_state(BizUnit.STATUS_TARGET_COMPLETED)

    def debug_info(self):
        msg = '''
        {0}
        {1}
        {2}
        '''
        return msg.format(str(self._stack), str(self._context),
                          pprint.pformat(self._biz_tree.to_dict(with_data=True)))
