#!/usr/bin/env python
# encoding: utf-8

import json
import logging
from vikicommon.util import escape_unicode
from vikidm.units.bizunit import BizUnit
from vikidm.context import Slot
from vikidm.config import ConfigDM
from .agency import MixAgency

log = logging.getLogger(__name__)


class Agent(BizUnit):
    """
    Any response of DM always related to an Agent.

    Attributes
    ----------
    subject : str, Deprecated.
    scope : str, Deprecated.
    event_id : str, Correspond to an resource and event with specific
                    arguments.
    timeout : float, Action time out.
    entrance : boolean, If the agent could trigger an ancestor node of
               type MixAgency.
    state : The state of agent.
    trigger_slots : dict, Slots that could trigger the agent.
    target_slots : list, Slots that the agent will fill.

    """

    def __init__(self, dm, tag, data):
        try:
            filtered_data = {   # 用于tree.to_json(), 方便调试。
                'subject': data['subject'],
                'scope': data['scope'],
                'event_id': data['event_id'],
                'timeout': float(data['timeout']),
                'entrance': data['entrance'],
                'state': BizUnit.STATUS_TREEWAIT,
                'trigger_slots': data['trigger_slots'],
                'target_slots': data['target_slots']
            }
        except KeyError as e:
            log.error(data)
            raise e
        self._trigger_slots = list(
            self._deserialize_trigger_slots(filtered_data))
        self._target_slots = list(
            self._deserialize_target_slots(filtered_data))
        self.children = []
        super(Agent, self).__init__(dm, data["id"], tag, filtered_data)

    def _deserialize_trigger_slots(self, data):
        for kv in data['trigger_slots']:
            split_index = kv.find('=')
            key = kv[0: split_index]
            value = kv[split_index + 1:]
            yield Slot(key, value)

    def _deserialize_target_slots(self, data):
        for key in data['target_slots']:
            yield Slot(key)

    @classmethod
    def get_agent(self, dm, tag, data):
        """ Create and return a instance of subclass of Agent.

        Parameters
        ----------
        dm : DialogEngine
        tag : str, Readable identifier of bizunit.
        data : dict.

        """
        if data["target_slots"] != []:
            return TargetAgent(dm, tag, data)
        elif data["trigger_slots"] != []:
            return TriggerAgent(dm, tag, data)
        assert(False)

    def on_confirm(self):
        """
        Deal with action confirm message from device.
        """
        self.set_state(BizUnit.STATUS_ACTION_COMPLETED)

    def reset_slots(self):
        """
        Reset slots when parent node(an Agency) is not in the stack.
        """
        if self.parent.is_root() or\
                self.parent.state == BizUnit.STATUS_TREEWAIT:
            for slot in self.trigger_slots + self.target_slots:
                if slot.life_type == Slot.LIFE_STACK:
                    self._dm.context.reset_slot(slot.key)
                    log.debug("RESET_CONCEPT [{0}]".format(slot.key))

    def satisfied(self):
        """
        Return if the trigger slots is satisfied.
        """
        return all(
            [self._dm.context.satisfied(c)for c in self.trigger_slots])

    @property
    def intent(self):
        if hasattr(self, "_intent"):
            return self._intent
        for slot in self.trigger_slots:
            if slot.key == "intent":
                self._intent = slot.value
                return self._intent
        import pdb
        pdb.set_trace()
        if self.trigger_slots:
            assert(False)
        #  TODO:  <14-08-18, yourname> #
        assert(False)

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
    def trigger_slots(self):
        return self._trigger_slots

    @property
    def target_slots(self):
        return self._target_slots

    def __str__(self):
        return json.dumps(escape_unicode(self.data))


class TargetAgent(Agent):
    def __init__(self, dm, tag, data):
        super(TargetAgent, self).__init__(dm, tag, data)
        assert(self._trigger_slots and self._target_slots)

    def target_completed(self):
        """
        If all target slots filled.
        """
        return all([self._dm.context.dirty(c.key)
                    for c in self.target_slots])

    def satisfied(self):
        """
        Return if the trigger slots is satisfied and
        all target slots filled.
        """
        return super(TargetAgent, self).satisfied() and self.target_completed()

    def restore_topic_and_focus(self):
        assert(self.state in [BizUnit.STATUS_WAIT_ACTION_CONFIRM,
                              BizUnit.STATUS_WAIT_TARGET])
        if self.state == BizUnit.STATUS_WAIT_ACTION_CONFIRM:
            # Confirmation waiting is meaningless after agent become focus
            # again.
            self.set_state(BizUnit.STATUS_ACTION_COMPLETED)
        elif self.state == BizUnit.STATUS_WAIT_TARGET:
            # waiting target again.
            self._execute_condition.add(BizUnit.STATUS_WAIT_TARGET)

    def _execute(self):
        log.debug("EXECUTE TargetAgent({0})".format(self.tag))
        if self.state == BizUnit.STATUS_TRIGGERED:
            log.debug("WAIT_CONFIRM TargetAgent(%s)" % self.tag)
            self.set_state(BizUnit.STATUS_WAIT_ACTION_CONFIRM)
            self._dm.start_timer(
                self, self.timeout, self._dm.on_actionwait_timeout)
            log.debug("START_ACTION_TIMER TargetAgent({0})".format(self.tag))

        elif self.state == BizUnit.STATUS_WAIT_TARGET:
            self._execute_condition.remove(BizUnit.STATUS_WAIT_TARGET)
            if self._dm.countdown_unit != self:
                self._dm.reset_countdown_round()
                log.debug(
                    "START_INPUT_COUNTDOWN TargetAgent({0})".format(self.tag))
            elif self._dm.round_out():
                self._dm.countdown_round += 1
                self._dm.on_inputwait_round_out()
        assert(len(self.target_slots) <= 1)
        return {
            'event_id': self.event_id,
            'target': [self.target_slots[0].key]
        }

    def on_confirm(self):
        assert(self.state == Agent.STATUS_WAIT_ACTION_CONFIRM)
        self.set_state(BizUnit.STATUS_WAIT_TARGET)
        log.debug("WAIT_INPUT Agent({0})".format(self.tag))
        self._execute_condition.add(BizUnit.STATUS_WAIT_TARGET)


class TriggerAgent(Agent):
    def __init__(self, dm, tag, data):
        super(TriggerAgent, self).__init__(dm, tag, data)
        assert(self._trigger_slots)

    def restore_topic_and_focus(self):
        assert(self.state == BizUnit.STATUS_WAIT_ACTION_CONFIRM)
        self.set_state(BizUnit.STATUS_ACTION_COMPLETED)

    def _execute(self):
        log.debug("EXECUTE TriggerAgent({0})".format(self.tag))
        if self.state == BizUnit.STATUS_TRIGGERED:
            log.debug("WAIT_CONFIRM Agent(%s)" % self.tag)
            self.set_state(BizUnit.STATUS_WAIT_ACTION_CONFIRM)
            self._dm.start_timer(
                self, self.timeout, self._dm.on_actionwait_timeout)
            log.debug("START_ACTION_TIMER TriggerAgent({0})".format(self.tag))
        return {'event_id': self.event_id, 'target': []}

    def reset_slots(self):
        super(TriggerAgent, self).reset_slots()
        if isinstance(self.parent, MixAgency):
            self._dm.context.reset_slot("intent")
