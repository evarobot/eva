#!/usr/bin/env python
# encoding: utf-8

from vikidm.units.bizunit import BizUnit
from vikidm.units.agent import Agent
import logging
log = logging.getLogger(__name__)


class AbnormalHandler(BizUnit):
    ABNORMAL_ACTION_TIMEOUT = "ABNORMAL_ACTION_TIMEOUT"
    ABNORMAL_ACTION_FAILED = "ABNORMAL_ACTION_FAILED"
    ABNORMAL_INPUT_TIMEOUT = "ABNORMAL_INPUT_TIMEOUT"

    def __init__(self, dm, bizunit, type_):
        data = {
            'trigger_concepts': []
        }
        super(AbnormalHandler, self).__init__(dm, 'AbnormalHandler',
                                              'AbnormalHandler', data)
        self.set_state(BizUnit.STATUS_TRIGGERED)
        self.parent = None
        self.target_concepts = []
        self.trigger_concepts = []
        self._handler_finished = False
        self.handler = self._get_handler(bizunit, type_)
        self.handler.parent = self

    def reset_concepts(self):
        pass

    def _get_handler(self, bizunit, type_):
        if type_ == self.ABNORMAL_ACTION_FAILED:
            return ActionFailedAgent(self._dm, bizunit)
        elif type_ == self.ABNORMAL_ACTION_TIMEOUT:
            return ActionTimeoutAgent(self._dm, bizunit)
        elif type_ == self.ABNORMAL_INPUT_TIMEOUT:
            return InputTimeoutAgent(self._dm, bizunit)

    def is_root(self):
        return False

    def _execute(self):
        log.debug("EXECUTE AbnormalHandler({0})".format(self.handler.tag))
        if self._handler_finished:
            self._mark_abnormal_unit(self._dm.stack, self._dm.biz_tree, self._dm.stack._items[-2])
            self.state = BizUnit.STATUS_TREEWAIT
            self._dm.stack.pop()
            return self.state

        # push handler unit
        self.handler.set_state(Agent.STATUS_TRIGGERED)
        self.state = BizUnit.STATUS_STACKWAIT
        self._dm.stack.push(self.handler)
        self._handler_finished = True
        return self.state

    def _mark_abnormal_unit(self, stack, tree, abnormal_unit):
        parent = tree.parent(abnormal_unit.identifier)

        def is_abnormal(bizunit):
            is_agency_parent = bizunit == parent and not parent.is_root()
            if bizunit == abnormal_unit or is_agency_parent:
                return True
            return False

        for unit in reversed(stack._items[:-1]):
            if is_abnormal(unit):
                unit.set_state(BizUnit.STATUS_ABNORMAL)


class DefaultHandlerAgent(Agent):
    def __init__(self, dm, bizunit, data):
        data.update({
            'subject': '',
            'scope': '',
            'timeout': 0,
            'entrance': False,
            'trigger_concepts': {},
            'state': '',
            'target_concepts': [],
        })
        self._trigger_concepts = []
        self._target_concepts = []
        super(DefaultHandlerAgent, self).__init__(dm, data["event_id"], data)

    def _execute(self):
        if self.state == BizUnit.STATUS_TRIGGERED:
            if self.timeout == 0:
                # 默认的异常处理节点倒计时总是为0
                self.set_state(BizUnit.STATUS_ACTION_COMPLETED)
            else:
                self.set_state(BizUnit.STATUS_WAIT_ACTION_CONFIRM)
                self._dm._start_timer(self.tag, self.timeout, self._dm._actionwait_timeout)
                log.debug("START_TIMER BizUnit({0})".format(self.tag))
        return self.event_id

    def reset_concepts(self):
        pass


class ActionFailedAgent(DefaultHandlerAgent):
    def __init__(self, dm, bizunit):
        data = {
            'event_id': 'FAILED|' + bizunit.event_id,
            'tag': 'FAILED|' + bizunit.event_id,
        }
        super(ActionFailedAgent, self).__init__(dm, data["event_id"], data)


class InputTimeoutAgent(DefaultHandlerAgent):
    def __init__(self, dm, bizunit):
        data = {
            'event_id': 'INPUT_TIMEOUT|' + bizunit.event_id,
            'tag': 'INPUT_TIMEOUT|' + bizunit.event_id,
        }
        super(InputTimeoutAgent, self).__init__(dm, data["event_id"], data)


class ActionTimeoutAgent(DefaultHandlerAgent):
    def __init__(self, dm, bizunit):
        data = {
            'event_id': 'ACTION_TIMEOUT|' + bizunit.event_id,
            'tag': 'ACTION_TIMEOUT|' + bizunit.event_id,
        }
        super(ActionTimeoutAgent, self).__init__(dm, data["event_id"], data)
