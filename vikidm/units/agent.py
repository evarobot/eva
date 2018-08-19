#!/usr/bin/env python
# encoding: utf-8

import json
import logging
from vikicommon.util import escape_unicode
from vikidm.units.bizunit import BizUnit
from vikidm.context import Concept
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
    trigger_concepts : dict, Concepts that could trigger the agent.
    target_concepts : list, Concepts that the agent will fill.

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
                'trigger_concepts': data['trigger_concepts'],
                'target_concepts': data['target_concepts']
            }
        except KeyError as e:
            log.error(data)
            raise e
        self._trigger_concepts = list(
            self._deserialize_trigger_concepts(filtered_data))
        self._target_concepts = list(
            self._deserialize_target_concepts(filtered_data))
        self.children = []
        super(Agent, self).__init__(dm, data["id"], tag, filtered_data)

    def _deserialize_trigger_concepts(self, data):
        for kv in data['trigger_concepts']:
            split_index = kv.find('=')
            key = kv[0: split_index]
            value = kv[split_index + 1:]
            yield Concept(key, value)

    def _deserialize_target_concepts(self, data):
        for key in data['target_concepts']:
            yield Concept(key)

    @classmethod
    def get_agent(self, dm, tag, data):
        """ Create and return a instance of subclass of Agent.

        Parameters
        ----------
        dm : DialogEngine
        tag : str, Readable identifier of bizunit.
        data : dict.

        """
        if data["target_concepts"] != []:
            return TargetAgent(dm, tag, data)
        elif data["trigger_concepts"] != []:
            return TriggerAgent(dm, tag, data)
        assert(False)

    def on_confirm(self):
        """
        Deal with action confirm message from device.
        """
        self.set_state(BizUnit.STATUS_ACTION_COMPLETED)

    def reset_concepts(self):
        """
        Reset concepts when parent node(an Agency) is not in the stack.
        """
        if self.parent.is_root() or\
                self.parent.state == BizUnit.STATUS_TREEWAIT:
            for concept in self.trigger_concepts + self.target_concepts:
                if concept.life_type == Concept.LIFE_STACK:
                    self._dm.context.reset_concept(concept.key)
                    log.debug("RESET_CONCEPT [{0}]".format(concept.key))

    def satisfied(self):
        """
        Return if the trigger concepts is satisfied.
        """
        return all(
            [self._dm.context.satisfied(c)for c in self.trigger_concepts])

    @property
    def intent(self):
        if hasattr(self, "_intent"):
            return self._intent
        for concept in self.trigger_concepts:
            if concept.key == "intent":
                self._intent = concept.value
                return self._intent
        if self.trigger_concepts:
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
    def trigger_concepts(self):
        return self._trigger_concepts

    @property
    def target_concepts(self):
        return self._target_concepts

    def __str__(self):
        return json.dumps(escape_unicode(self.data))


class TargetAgent(Agent):
    def __init__(self, dm, tag, data):
        super(TargetAgent, self).__init__(dm, tag, data)
        assert(self._trigger_concepts and self._target_concepts)

    def target_completed(self):
        """
        If all target concepts filled.
        """
        return all([self._dm.context.dirty(c.key)
                    for c in self.target_concepts])

    def satisfied(self):
        """
        Return if the trigger concepts is satisfied and
        all target concepts filled.
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
            # start timer
            self._dm.start_timer(
                self, ConfigDM.input_timeout, self._dm.on_inputwait_timeout)
            log.debug("START_INPUT_TIMER TargetAgent({0})".format(self.tag))
            self._execute_condition.remove(BizUnit.STATUS_WAIT_TARGET)
        assert(len(self.target_concepts) <= 1)
        return {
            'event_id': self.event_id,
            'target': [self.target_concepts[0].key]
        }

    def on_confirm(self):
        assert(self.state == Agent.STATUS_WAIT_ACTION_CONFIRM)
        self.set_state(BizUnit.STATUS_WAIT_TARGET)
        log.debug("WAIT_INPUT Agent({0})".format(self.tag))
        self._execute_condition.add(BizUnit.STATUS_WAIT_TARGET)


class TriggerAgent(Agent):
    def __init__(self, dm, tag, data):
        super(TriggerAgent, self).__init__(dm, tag, data)
        assert(self._trigger_concepts)

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

    def reset_concepts(self):
        super(TriggerAgent, self).reset_concepts()
        if isinstance(self.parent, MixAgency):
            self._dm.context.reset_concept("intent")
