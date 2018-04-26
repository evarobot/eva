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
from vikidm.biztree import BizTree
from vikidm.units import (
    Agent,
    TargetAgent,
    BizUnit,
    MixAgency,
    AbnormalHandler
)
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

    def new_session(self, sid):
        return self._sid is not None and sid > self._sid


class Stack(object):
    """
     模拟栈
    """
    def __init__(self):
        self._items = []

    @property
    def items(self):
        return self._items

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

    def __str__(self):
        return "\n                ".join(["\n            Stack:"] + ["{0}({1})".format(c.tag, c.state) for c in self._items])

    def __repr__(self):
        name = self.__class__.__name__
        items = "\n".join([c.tag for c in self._items])
        kwargs = [
            "items=[\n{0}\n]".format(items)
        ]
        return "%s(%s)" % (name, ", ".join(kwargs))


class ExpectAgenda(object):
    def __init__(self, stack):
        self._candicates = None
        self._stack = stack

    def compute_candicate_units(self):
        candicates = self._tree_candicate_units()
        candicates.extend(self._context_candicae_units())

        self.valid_intents = set()
        valid_concepts = []
        for agent in candicates:
            valid_concepts.extend(agent.target_concepts)
            valid_concepts.extend(agent.trigger_concepts)
            for concept in agent.trigger_concepts:
                if concept.key == "intent":
                    self.valid_intents.add(concept.value)
        self.valid_slots = set([c.key for c in valid_concepts])
        self.candicate_agents = set(candicates)

    def _tree_candicate_units(self):
        if self._candicates:
            return self._candicates
        self._candicates = self._get_candicates(self._stack.items[0])
        return self._candicates

    def _get_candicates(self, bizunit):
        candicates = []
        def visit_tree(unit):
            # log.debug("visit %s" % unit.tag)
            if isinstance(unit, Agent):
                candicates.append(unit)
            elif isinstance(unit, MixAgency):
                for child in unit.children:
                    if child.entrance or unit in self._stack.items:
                        visit_tree(child)
            else:
                for child in unit.children:
                    visit_tree(child)
        visit_tree(bizunit)
        return candicates

    def _context_candicae_units(self):
        candicates = []
        for unit in self._stack.items[1:]:
            candicates.extend(self._get_candicates(unit))
        return candicates

    def __repr__(self):
        str_slots = "\n                ".join(["\n            ValidSlots:"] + ["{0}".format(c) for c in sorted(self.valid_slots)])
        str_intents = "\n                ".join(["\n            ValidIntents:"] + ["{0}".format(c) for c in sorted(self.valid_intents)])
        return str_intents + str_slots


class DialogEngine(object):
    """ 对话管理单元 """
    def __init__(self):
        self.context = Context()
        self.biz_tree = BizTree(self)
        self.stack = Stack()
        self._timer = None
        self._datetime = datetime.now()
        self._session = Session()
        self.debug_loop = 0
        self.debug_timeunit = 1  # 为了测试的时候加速时间计数
        self._timer_count = 0
        self._agenda = ExpectAgenda(self.stack)

    @property
    def is_waiting(self):
        return self._timer_count > 0

    def init_from_db(self, domain_name):
        json_tree = cms_rpc.get_json_biztree(domain_name)
        self.biz_tree.init_from_json(json_tree)
        self._init_context()
        node = self.biz_tree.get_node(self.biz_tree.root)
        node.set_state(BizUnit.STATUS_STACKWAIT)
        self.stack.push(node)

    def execute_focus_agent(self):
        event_id = None
        focus_unit = self.stack.top()
        while focus_unit.executable():
            event_id = focus_unit.execute()
            focus_unit = self.stack.top()
            self.debug_loop += 1
        return event_id

    def _actionwait_timeout(self):
        self._timer_count -= 1
        delta = (time.time() - self._start_time) / self.debug_timeunit
        focus_unit = self.stack.top()
        log.debug("ACTION_TIMEOUT {2}({0}) {1}".format(focus_unit.tag, delta,
                                                       focus_unit.__class__.__name__))
        self._handle_abnormal(AbnormalHandler.ABNORMAL_ACTION_TIMEOUT)

    def _inputwait_timeout(self):
        self._timer_count -= 1
        delta = (time.time()- self._start_time) / self.debug_timeunit
        focus_unit = self.stack.top()
        log.debug("INPUT_TIMEOUT {2}({0}) {1}".format(focus_unit.tag, delta,
                                                      focus_unit.__class__.__name__))
        self._handle_abnormal(AbnormalHandler.ABNORMAL_INPUT_TIMEOUT)

    def _delaywait_timeout(self):
        self._timer_count -= 1
        delta = (time.time()- self._start_time) / self.debug_timeunit
        focus_unit = self.stack.top()
        log.debug("DELAY_TIMEOUT {2}({0}) {1}".format(focus_unit.tag, delta,
                                                      focus_unit.__class__.__name__))
        focus_unit.set_state(BizUnit.STATUS_AGENCY_COMPLETED)
        self.execute_focus_agent()

    def _handle_abnormal(self, abnormal_type):
        abnormal = AbnormalHandler(self, self.stack.top(), abnormal_type)
        self.stack.push(abnormal)
        self.execute_focus_agent()
        self._session.end_session()

    def _focus_bizunit_out(self, _to_pop_unit):
        self.stack.pop()
        log.debug("POP_STACK: {0}({1})".format(_to_pop_unit.__class__.__name__, _to_pop_unit.tag))
        _to_pop_unit.pop_from_stack()
        focus_unit = self.stack.top()
        if _to_pop_unit.parent and _to_pop_unit.parent != focus_unit:
            log.debug("ROUND_RETURN BizUnit({0})".format(focus_unit.tag))
            focus_unit.round_back()
        else:
            focus_unit.re_enter_after_child_done()
        log.debug("STATUS: \n{0}\n{1}".format(self.stack, self.context))

    def _cancel_timer(self):
        self._timer_count -= 1
        self._timer.cancel()

    def _start_timer(self, bizunit, seconds, function, *args, **kwargs):
        assert(self._timer_count == 0)
        self._timer = TimerReset(bizunit, seconds * self.debug_timeunit, function, *args, **kwargs)
        self._start_time = time.time()
        self._timer_count += 1
        self._timer.start()

    def process_concepts(self, sid, concepts):
        log.info("-------- {0} -------------------".format(concepts))
        if self._session.new_session(sid) or self.is_waiting:
            if self._session.new_session(sid):
                # could be a remote error
                log.debug("IGNORE_OLD_SESSION")
            self._cancel_timer()
            log.debug("CANCEL_TIMER {0}({1})".format(self._timer.owner.__class__.__name__,
                                                     self._timer.owner.tag))
        self._session.begin_session(sid)
        self._agenda.compute_candicate_units()
        log.info(self._agenda)
        self._update_concepts(concepts)
        self._mark_completed_bizunits()
        self._trigger_bizunit()
        ret = self.execute_focus_agent()
        if ret is None:
            self._session.end_session()
        log.info(self.stack)
        log.info(self.context)
        return ret

    def _trigger_bizunit(self):
        # 如果多个，都执行，就需要多个反馈，可能需要主动推送功能。
        # 目前只支持返回一个。
        for bizunit in self._agenda.candicate_agents:
            if not isinstance(bizunit, Agent):
                continue
            if not bizunit.satisfied() or bizunit.target_completed:
                continue
            bizunit.hierarchy_trigger()
            log.debug("Triggered Stack:")
            log.debug(self.stack)
            break

    def _handle_success_confirm(self):
        focus_unit = self.stack.top()
        assert(isinstance(focus_unit, Agent))
        log.debug("CONFIRM: {0}".format(focus_unit.tag))
        self._cancel_timer()
        log.debug("CANCEL_TIMER {0}({1})".format(self._timer.owner.__class__.__name__,
                                                 self._timer.owner.tag))
        focus_unit.confirm()
        self.execute_focus_agent()
        self._session.end_session()

    def process_confirm(self, sid, data):
        log.info("========= {0} ===================".format(data))
        ret = {
            'code': 0,
            'message': ''
        }
        if not self._session.valid_session(sid):
            return ret
        if data['code'] != 0:
            self._handle_abnormal(AbnormalHandler.ABNORMAL_ACTION_FAILED)
            self._cancel_timer()
            log.debug("CANCEL_TIMER {0}({1})".format(self._timer.owner.__class__.__name__,
                                                    self._timer.owner.tag))
        else:
            self._handle_success_confirm()
        log.info(self.stack)
        log.info(self.context)
        return ret

    def _update_concepts(self, concepts):
        valid_concepts = []
        for agent in self._agenda.candicate_agents:
            valid_concepts.extend(agent.target_concepts)
            valid_concepts.extend(agent.trigger_concepts)
        valid_slots = set([c.key for c in valid_concepts])
        for concept in concepts:
            if concept.key in valid_slots:
                if (concept.key == "intent" and concept.value in self._agenda.valid_intents) or\
                        concept.key != "intent":
                    self.context.update_concept(concept.key, concept)

    def _init_context(self):
        for bizunit in self.biz_tree.all_nodes_itr():
            if isinstance(bizunit, Agent):
                for concept in bizunit.trigger_concepts:
                    concept = copy.deepcopy(concept)
                    self.context.add_concept(concept)



    def _mark_completed_bizunits(self):
        for bizunit in self.biz_tree.all_nodes_itr():
            if isinstance(bizunit, TargetAgent):
                completed = all([self.context.dirty(c) for c in bizunit.target_concepts])
                if completed:
                    bizunit.mark_target_completed()

    def debug_info(self):
        msg = '''
        {0}
        {1}
        {2}
        '''
        return msg.format(str(self.stack), str(self.context),
                          pprint.pformat(self.biz_tree.to_dict(with_data=True)))
