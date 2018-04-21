#!/usr/bin/env python
# encoding: utf-8

from vikidm.units.bizunit import BizUnit
from vikidm.config import ConfigDM
from vikidm.context import Concept
import logging
log = logging.getLogger(__name__)


class Agency(BizUnit):
    TYPE_CLUSTER = "TYPE_CLUSTER"  # no delay exit
    TYPE_TARGET = "TYPE_TARGET"
    TYPE_SEQUENCE = "TYPE_SEQUENCE"
    TYPE_ROOT = "TYPE_ROOT"

    def __init__(self, dm, tag, data):
        super(Agency, self).__init__(dm, data["id"], tag, data)
        self.trigger_child = None
        self._type = data['type']
        self._handler_finished = False

    def __str__(self):
        return self.tag.encode('utf8')

    @classmethod
    def get_agency(self, dm, tag, data):
        if data['type'] == Agency.TYPE_ROOT:
            return Agency(dm, tag, data)
        elif data['type'] == Agency.TYPE_CLUSTER:
            return ClusterAgency(dm, tag, data)
        elif data['type'] == Agency.TYPE_TARGET:
            return TargetAgency(dm, tag, data)

    @property
    def state(self):
        return self.data['state']

    @property
    def children(self):
        for child in self._dm.biz_tree.children(self.identifier):
            yield child

    def set_state(self, value):
        self.data['state'] = value

    def reset_concepts(self):
        if self.parent.is_root() or self.parent.state == BizUnit.STATUS_TREEWAIT:
            for child in self.children:
                child.reset_concepts()


class ClusterAgency(Agency):
    """"""
    def __init__(self, dm, tag, data):
        super(ClusterAgency, self).__init__(dm, tag, data)

    def _execute(self):
        if self._handler_finished:
            self.set_state(BizUnit.STATUS_AGENCY_COMPLETED)
            return
        self.trigger_child.set_state(BizUnit.STATUS_TRIGGERED)
        self._dm.stack.push(self.trigger_child)
        self.trigger_child = None
        self.set_state(BizUnit.STATUS_STACKWAIT)
        self._handler_finished = True


class TargetAgency(Agency):
    """"""
    def __init__(self, dm, tag, data):
        super(TargetAgency, self).__init__(dm, tag, data)
        self.event_id = data['event_id']
        self._timer = None
        self._target_concepts = None

    @property
    def target_concepts(self):
        if self._target_concepts:
            return self._target_concepts
        concept_keys = set()
        for child in self.children:
            for c in child.target_concepts:
                concept_keys.add(c.key)
        self._target_concepts = set([Concept(key, None) for key in concept_keys])
        return self._target_concepts

    def executable(self):
        return self.state in self._execute_condition

    def activate(self):
        if self.state not in [BizUnit.STATUS_ABNORMAL, BizUnit.STATUS_WAIT_TARGET]:
            # activate by target child
            self.set_state(BizUnit.STATUS_TRIGGERED)

        if self._is_default_node(self.active_child):
            self.set_state(BizUnit.STATUS_WAIT_TARGET)
            self._execute_condition.add(BizUnit.STATUS_WAIT_TARGET)

        elif self._is_result_node(self.active_child):
            self.set_state(BizUnit.STATUS_DELAY_EXIST)
            self._execute_condition.add(BizUnit.STATUS_DELAY_EXIST)

        self.active_child = None

    def round_back(self):
        self.restore_context(self._dm.context)
        # recountdown
        self._execute_condition.add(BizUnit.STATUS_WAIT_TARGET)

    def restore_context(self, context):
        context.update_concept(self._intent.key, self._intent)

    def _execute(self):
        log.debug("EXECUTE TargetAgency({0})".format(self.tag))
        if self.state == BizUnit.STATUS_WAIT_TARGET:
            self._execute_condition.remove(BizUnit.STATUS_WAIT_TARGET)
            self._dm._start_timer(self, ConfigDM.input_timeout, self._dm._inputwait_timeout)
            log.debug("START_INPUT_TIMER TargetAgency({0})".format(self.tag))
            return
        elif self.state == BizUnit.STATUS_DELAY_EXIST:
            self._execute_condition.remove(BizUnit.STATUS_DELAY_EXIST)
            self._dm._start_timer(self, ConfigDM.input_timeout, self._dm._delaywait_timeout)
            log.debug("START_DELAY_TIMER TargetAgency({0})".format(self.tag))
            return

        self._intent = self._dm.context["intent"]  # for restore
        self.active_child = self._plan()
        self.active_child.set_state(BizUnit.STATUS_TRIGGERED)
        self._dm.stack.push(self.active_child)
        self.set_state(BizUnit.STATUS_STACKWAIT)

    def _plan(self):
        # log.debug(self._dm.context)
        targets_clean = all([not self._dm.context.dirty(c) for c in self.target_concepts])
        for child in self.children:
            if self._is_result_node(child):
                trigger_satisified = all([self._dm.context.satisfied(c) for c in child.trigger_concepts])
                if trigger_satisified:
                    return child
            elif self._is_default_node(child) and targets_clean:
                log.debug("WAIT_INPUT TargetAgency({0})".format(self.tag))
                return child
            elif self._is_target_node(child) and not child.target_completed:
                # return first none complete target child
                return child

    def _is_default_node(self, bizunit):
        return len(bizunit.target_concepts) == 0 and len(bizunit.trigger_concepts) == 1

    def _is_result_node(self, bizunit):
        return len(bizunit.trigger_concepts) > 1

    def _is_target_node(self, bizunit):
        return len(bizunit.target_concepts) != 0
