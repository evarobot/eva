#!/usr/bin/env python
# encoding: utf-8

from vikidm.units.bizunit import BizUnit
from vikidm.units.agent import TargetAgent, TriggerAgent
from vikidm.config import ConfigDM
from vikidm.context import Slot
import logging
log = logging.getLogger(__name__)


class Agency(BizUnit):
    """ Instance of Agency subclass usually represent a local logic controller.

    Agency instance always have children nodes.

    Attributes
    ----------
    api_slot_keys : [str], Slots update with APIs by module like
                                 recommendation system.
    children : [], Children BizUnit nodes.
    trigger_child : BizUnit, child that activate it.
    """
    TYPE_CLUSTER = "TYPE_CLUSTER"  # no delay exit
    TYPE_TARGET = "TYPE_TARGET"
    TYPE_SEQUENCE = "TYPE_SEQUENCE"
    TYPE_MIX = "TYPE_MIX"
    TYPE_ROOT = "TYPE_ROOT"

    def __init__(self, dm, tag, data):
        super(Agency, self).__init__(dm, data["id"], tag, data)
        self.type = data['type']
        self._handler_finished = False
        self._trigger_child = None
        self.api_slot_keys = []

    def __str__(self):
        return self.tag.encode('utf8')

    @classmethod
    def get_agency(self, dm, tag, data):
        """ A factory method, return required instance of Agency subclass.  """
        if data['type'] == Agency.TYPE_ROOT:
            return Agency(dm, tag, data)
        elif data['type'] == Agency.TYPE_CLUSTER:
            return ClusterAgency(dm, tag, data)
        elif data['type'] == Agency.TYPE_TARGET:
            return TargetAgency(dm, tag, data)
        elif data['type'] == Agency.TYPE_MIX:
            return MixAgency(dm, tag, data)
        else:
            log.error(data)
            assert(False)

    def restore_focus_after_child_done(self):
        """ Become focus again afater child node finishing executing.  """
        if not self.is_root() and self.state != BizUnit.STATUS_ABNORMAL:
            self.set_state(BizUnit.STATUS_TRIGGERED)

    def reset_slots(self):
        """
        Reset slots of descendant nodes, intent slot and API slots.

        Invoked when itself and parent is not in the stack.
        """
        if self.parent.is_root() or\
                self.parent.state == BizUnit.STATUS_TREEWAIT:
            for child in self.children:
                child.reset_slots()
        self._dm.context.reset_slot("intent")
        for key in self.api_slot_keys:
            self._dm.context.reset_slot(key)
            log.info("RESET remote slot {0}".format(key))
        self.api_slot_keys = []

    @property
    def trigger_child(self):
        """
        The child trigged the Agency instance.
        """
        return self._trigger_child

    @trigger_child.setter
    def trigger_child(self, v):
        self._trigger_child = v
        self._handler_finished = False

    @property
    def entrance(self):
        return self.data['entrance']

    @property
    def children(self):
        for child in self._dm.biz_tree.children(self.identifier):
            yield child


class ClusterAgency(Agency):
    """
    A local controller always with one child of type `TriggerAgent`.
    """
    def __init__(self, dm, tag, data):
        super(ClusterAgency, self).__init__(dm, tag, data)

    @property
    def trigger_child(self):
        return self._trigger_child

    @trigger_child.setter
    def trigger_child(self, v):
        self._trigger_child = v
        self._child_activated = False

    def _execute(self):
        if self._child_activated:
            self.set_state(BizUnit.STATUS_AGENCY_COMPLETED)
            return {}
        self.trigger_child.set_state(BizUnit.STATUS_TRIGGERED)
        self._dm.stack.push(self.trigger_child)
        self.trigger_child = None
        self._child_activated = True
        self.set_state(BizUnit.STATUS_STACKWAIT)


class TargetAgency(Agency):
    """
    A local controller with children of type `TargetAgent` and `TriggerAgent`.

    The `TargetAgent` children will require user inputs to fill target
    slots and the `TriggerAgent` give the desired response.

    Attributes
    ----------
    target_slots : [Slot]
    """
    def __init__(self, dm, tag, data):
        super(TargetAgency, self).__init__(dm, tag, data)
        self.event_id = ""
        self._timer = None
        self._target_slots = None

    @property
    def target_slots(self):
        """ Slots to filled by `TargetAgent` children.  """
        if self._target_slots:
            return self._target_slots
        slot_keys = set()
        for child in self.children:
            for c in child.target_slots:
                slot_keys.add(c.key)
        self._target_slots = set(
            [Slot(key, None) for key in slot_keys])
        return self._target_slots

    def restore_focus_after_child_done(self):
        """
        see :meth:`~vikidm.units.agency.Agency.restore_focus_after_child_done`
        """
        if self.state == BizUnit.STATUS_ABNORMAL:
            return
        if isinstance(self.active_child, TargetAgent):
                self.set_state(BizUnit.STATUS_TRIGGERED)
        elif isinstance(self.active_child, TriggerAgent):
            self.set_state(BizUnit.STATUS_DELAY_EXIST)
            self._execute_condition.add(BizUnit.STATUS_DELAY_EXIST)
        self.active_child = None

    def restore_topic_and_focus(self):
        """ see :meth:`~vikidm.units.bizunit.BizUnit.restore_topic_and_focus`

        """
        assert(self.state in [BizUnit.STATUS_WAIT_TARGET,
                              BizUnit.STATUS_DELAY_EXIST])
        self._execute_condition.add(self.state)

    def _execute(self):
        log.debug("EXECUTE TargetAgency({0})".format(self.tag))
        if self.state == BizUnit.STATUS_DELAY_EXIST:
            self._execute_condition.remove(BizUnit.STATUS_DELAY_EXIST)
            log.debug("START_DELAY_TIMER TargetAgency({0})".format(self.tag))
            self._dm.start_timer(self, ConfigDM.input_timeout,
                                 self._dm.on_delaywait_timeout)
            return {}

        self.active_child = self._plan()
        if self.active_child:
            self.active_child.set_state(BizUnit.STATUS_TRIGGERED)
            self._dm.stack.push(self.active_child)
            self.set_state(BizUnit.STATUS_STACKWAIT)
        else:
            #  TODO:  TEST
            # when swtiched back, context could be cleared by some unit share
            # same slots,  so none child could be triggered
            self.set_state(BizUnit.STATUS_DELAY_EXIST)
            self._execute_condition.add(BizUnit.STATUS_DELAY_EXIST)
            log.info(self._dm.stack)
            log.info(self._dm.context)
        return {}

    def _plan(self):
        for child in self.children:
            if isinstance(child, TriggerAgent) and child.satisfied():
                return child

        for child in self.children:
            if isinstance(child, TargetAgent) and\
                    len(child.target_slots) == len(self.target_slots) and\
                    child.target_clean():
                return child

        for child in self.children:
            if isinstance(child, TargetAgent) and\
                    len(child.target_slots) < len(self.target_slots) and\
                    not child.target_completed():
                # return first none complete target child
                return child
        return None


class MixAgency(Agency):
    """
    An local controller for scope control purpose.
    """
    def __init__(self, dm, tag, data):
        super(MixAgency, self).__init__(dm, tag, data)

    def restore_focus_after_child_done(self):
        """
        see :meth:`~vikidm.units.agency.Agency.restore_focus_after_child_done`
        """
        if self.state == BizUnit.STATUS_ABNORMAL:
            return
        self.set_state(BizUnit.STATUS_DELAY_EXIST)
        self._execute_condition.add(BizUnit.STATUS_DELAY_EXIST)

    def restore_topic_and_focus(self):
        """ see :meth:`~vikidm.units.bizunit.BizUnit.restore_topic_and_focus`

        """
        assert(self.state == BizUnit.STATUS_DELAY_EXIST)
        self._execute_condition.add(self.state)

    def _execute(self):
        log.debug("EXECUTE MixAgency({0})".format(self.tag))
        if self.state == BizUnit.STATUS_DELAY_EXIST:
            self._execute_condition.remove(BizUnit.STATUS_DELAY_EXIST)
            self._dm.start_timer(
                self, ConfigDM.input_timeout, self._dm.on_delaywait_timeout)
            log.debug("START_DELAY_TIMER MixAgency({0})".format(self.tag))
            return {}

        self.trigger_child.set_state(BizUnit.STATUS_TRIGGERED)
        self._dm.stack.push(self.trigger_child)

        self.trigger_child = None
        self.set_state(BizUnit.STATUS_STACKWAIT)
        return {}
