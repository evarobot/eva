#!/usr/bin/env python
# encoding: utf-8
import json
import logging
from vikicommon.util import escape_unicode
from vikidm.units.bizunit import BizUnit
from vikidm.context import Concept
from vikidm.config import ConfigDM

log = logging.getLogger(__name__)


class Agent(BizUnit):

    def __init__(self, dm, tag, data):
        filtered_data = {   # 用于tree.to_json(), 方便调试。
            'subject': data['subject'],
            'scope': data['scope'],
            'event_id': data['event_id'],
            'timeout': float(data['timeout']),
            'entrance': data['entrance'],
            'trigger_concepts': data['trigger_concepts'],
            'state': BizUnit.STATUS_TREEWAIT,
            'target_concepts': data['target_concepts']
        }
        self._trigger_concepts = list(self._deserialize_trigger_concepts(filtered_data))
        self._target_concepts = list(self._deserialize_target_concepts(filtered_data))
        self.target_completed = False
        self.children = []
        if "id" not in data:
            import pdb
            pdb.set_trace()
        super(Agent, self).__init__(dm, data["id"], tag, filtered_data)

    @classmethod
    def get_agent(self, dm, tag, data):
        if data["target_concepts"] != []:
            return TargetAgent(dm, tag, data)
        elif data["trigger_concepts"] != []:
            return TriggerAgent(dm, tag, data)
        assert(False)

    @property
    def intent(self):
        for concept in self.trigger_concepts:
            if concept.key == "intent":
                return concept.value
        #  TODO:  <28-04-18, yourname> #
        if self.trigger_concepts:
            assert(False)

    def activate(self):
        if self.state not in [BizUnit.STATUS_ACTION_COMPLETED, BizUnit.STATUS_ABNORMAL]:
            self.set_state(BizUnit.STATUS_TRIGGERED)

    def round_back(self):
        raise NotImplementedError

    def confirm(self):
        self.set_state(BizUnit.STATUS_ACTION_COMPLETED)

    def reset_concepts(self):
        if self.parent.is_root() or self.parent.state == BizUnit.STATUS_TREEWAIT:
            for concept in self.trigger_concepts + self.target_concepts:
                if concept.life_type == Concept.LIFE_STACK and self._dm.context.dirty(concept):
                    self._dm.context.reset_concept(concept.key)
                    self.target_completed = False
                    log.debug("RESET_CONCEPT [{0}]".format(concept.key))
        if not isinstance(self, TargetAgent):
            self._dm.context.reset_concept("intent")

    def satisfied(self):
        return all([self._dm.context.satisfied(c) for c in self.trigger_concepts]) and\
            self.trigger_concepts != []

    @property
    def subject(self):
        return self.data['subject']

    @subject.setter
    def subject(self, value):
        self.data['subject'] = value

    @property
    def scope(self):
        return self.data['scope']

    @scope.setter
    def scope(self, value):
        self.data['scope'] = value

    @property
    def event_id(self):
        return self.data['event_id']

    @event_id.setter
    def event_id(self, value):
        self.data['event_id'] = value

    @property
    def timeout(self):
        return self.data['timeout']

    @timeout.setter
    def timeout(self, value):
        self.data['timeout'] = value

    @property
    def entrance(self):
        return self.data['entrance']

    @property
    def trigger_concepts(self):
        return self._trigger_concepts

    @property
    def target_concepts(self):
        return self._target_concepts

    @property
    def state(self):
        return self.data['state']

    def set_state(self, value):
        self.data['state'] = value

    def _deserialize_trigger_concepts(self, data):
        for kv in data['trigger_concepts']:
            split_index = kv.find('=')
            key = kv[0: split_index]
            value = kv[split_index + 1:]
            yield Concept(key, value)

    def _deserialize_target_concepts(self, data):
        for key in data['target_concepts']:
            yield Concept(key)

    def __str__(self):
        return json.dumps(escape_unicode(self.data))


class TargetAgent(Agent):
    def __init__(self, dm, tag, data):
        super(TargetAgent, self).__init__(dm, tag, data)
        self.target_completed = False

    def round_back(self):
        if self.state == BizUnit.STATUS_WAIT_ACTION_CONFIRM:
            self.set_state(BizUnit.STATUS_ACTION_COMPLETED)
        elif self.state == BizUnit.STATUS_WAIT_TARGET:
            self._execute_condition.add(BizUnit.STATUS_WAIT_TARGET)

    def mark_target_completed(self):
        self.target_completed = True
        self.set_state(self.STATUS_TARGET_COMPLETED)

    def _execute(self):
        log.debug("EXECUTE TargetAgent({0})".format(self.tag))
        if self.state == BizUnit.STATUS_TRIGGERED:
            log.debug("WAIT_CONFIRM TargetAgent(%s)" % self.tag)
            self.set_state(BizUnit.STATUS_WAIT_ACTION_CONFIRM)
            #if self.timeout == 0:
                # 默认的异常处理节点倒计时总是为0
                # self.set_state(BizUnit.STATUS_ABNORMAL)
            # else:
            self._dm._start_timer(self, self.timeout, self._dm._actionwait_timeout)
            log.debug("START_ACTION_TIMER TargetAgent({0})".format(self.tag))

        elif self.state == BizUnit.STATUS_WAIT_TARGET:
            # start timer
            self._dm._start_timer(self, ConfigDM.input_timeout, self._dm._inputwait_timeout)
            log.debug("START_INPUT_TIMER TargetAgent({0})".format(self.tag))
            self._execute_condition.remove(BizUnit.STATUS_WAIT_TARGET)

        return self.event_id

    def confirm(self):
        assert(self.state == Agent.STATUS_WAIT_ACTION_CONFIRM)
        self.set_state(BizUnit.STATUS_WAIT_TARGET)
        log.debug("WAIT_INPUT Agent({0})".format(self.tag))
        self._execute_condition.add(BizUnit.STATUS_WAIT_TARGET)


class TriggerAgent(Agent):
    def __init__(self, dm, tag, data):
        super(TriggerAgent, self).__init__(dm, tag, data)

    def round_back(self):
        if self.state == BizUnit.STATUS_WAIT_ACTION_CONFIRM:
            self.set_state(BizUnit.STATUS_ACTION_COMPLETED)

    def _execute(self):
        log.debug("EXECUTE TriggerAgent({0})".format(self.tag))
        if self.state == BizUnit.STATUS_TRIGGERED:
            log.debug("WAIT_CONFIRM Agent(%s)" % self.tag)
            self.set_state(BizUnit.STATUS_WAIT_ACTION_CONFIRM)

            if self.timeout == 0:
                # 默认的异常处理节点倒计时总是为0
                self.set_state(BizUnit.STATUS_ACTION_COMPLETED)
            else:
                self._dm._start_timer(self, self.timeout, self._dm._actionwait_timeout)
                log.debug("START_ACTION_TIMER TriggerAgent({0})".format(self.tag))

        return self.event_id
