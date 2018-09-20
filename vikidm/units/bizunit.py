#!/usr/bin/env python
# encoding: utf-8

import treelib
import logging

log = logging.getLogger(__name__)


class BizUnit(treelib.Node):
    """
    Base class of all business dealing unit.

    Attributes
    -----------

    """
    STATUS_STACKWAIT = "STATUS_STACKWAIT"  # 栈中等待状态
    STATUS_TREEWAIT = "STATUS_TREEWAIT"
    STATUS_CANDICATE = "STATUS_CANDICATE"
    STATUS_TRIGGERED = "STATUS_TRIGGERED"
    STATUS_ACTION_COMPLETED = "STATUS_ACTION_COMPLETED"
    STATUS_ABNORMAL = "STATUS_ABNORMAL"
    STATUS_WAIT_ACTION_CONFIRM = "STATUS_WAIT_ACTION_CONFIRM"
    STATUS_WAIT_TARGET = "STATUS_WAIT_TARGET"
    STATUS_TARGET_COMPLETED = "STATUS_TARGET_COMPLETED"
    STATUS_AGENCY_COMPLETED = "STATUS_AGENCY_COMPLETED"
    STATUS_DELAY_EXIST = "STATUS_DELAY_EXIST"

    def __init__(self, dm, identifier, tag, data):
        super(BizUnit, self).__init__(tag, identifier, data=data)
        self.parent = None
        self.set_state(self.STATUS_TREEWAIT)
        self._dm = dm
        self._execute_condition = set([
            BizUnit.STATUS_TRIGGERED,
            BizUnit.STATUS_TARGET_COMPLETED,
            BizUnit.STATUS_ACTION_COMPLETED,
            BizUnit.STATUS_ABNORMAL,
            BizUnit.STATUS_AGENCY_COMPLETED
        ])

        self._pop_condition = set([
            BizUnit.STATUS_ACTION_COMPLETED,
            BizUnit.STATUS_AGENCY_COMPLETED,
            BizUnit.STATUS_TARGET_COMPLETED
        ])

    def transferable(self):
        """ If the node is in a trasferable state.

        The main routine of DM will call it's `execute` function if it's in
        a transferable focus state.
        """
        return self.state in self._execute_condition

    def is_completed(self):
        """ If the node finish executing, should pop out from stack.  """
        return self.state in self._pop_condition

    def is_abnormal(self):
        """ If the unit in the ABNORMAL state.  """
        return self.state == BizUnit.STATUS_ABNORMAL

    def execute(self):
        """
        Execute the main routine of bizunit.

        Instance of Agent will always return a vlaue.
        Instance of Agency will always return `{}`.
        """
        return self._execute()

    def restore_topic_and_focus(self):
        """ Invoked when the agent become focus **again**, and it's not in the
        same hierarchy path with previous focus.
        """
        raise NotImplementedError

    @property
    def state(self):
        return self.data['state']

    def set_state(self, value):
        """ Set unit state. """
        self.data['state'] = value

    def hierarchy_trigger(self):
        """ Activate and return the top ancestor node in the stack.

        It will push `trigger_child` node to stack.
        """
        if self.parent.is_root():
            self._trigger()
            return self

        unit = self
        while not unit.parent.is_root():
            unit.parent.trigger_child = unit
            unit = unit.parent

        if unit.parent.is_root():
            # push to stack and triggered
            if unit.state == BizUnit.STATUS_TREEWAIT:
                self._dm.stack.push(unit)
            unit.set_state(BizUnit.STATUS_TRIGGERED)
            return unit
        else:
            unit.parent.set_state(BizUnit.STATUS_TRIGGERED)
            unit.parent.trigger_child = unit
            return unit.parent

    def _trigger(self):
        if self.state == BizUnit.STATUS_TREEWAIT:
            self._dm.stack.push(self)
        self.set_state(BizUnit.STATUS_TRIGGERED)


class Topic(object):
    """"""
    def __init__(self):
        self._dm = None

    def ancestor_in_stack(self):
        unit = self  # inlcude itself
        while unit.parent is not None:
            if unit in self._dm.stack._items:
                return True
            unit = unit.parent
        return False

    def is_ancestor_of(self, bizunit):
        #  TODO: test #
        unit = bizunit.parent
        while unit is not None:
            if unit == self:
                return True
            unit = unit.parent
        return False

    def is_family(self, bizunit):
        #  TODO: test #
        # share a none root ancestor node node
        unit = self
        while unit.parent.is_root() == False:
            unit = unit.parent
        return unit.is_ancestor_of(bizunit)

    def notify_switch_topic(self):
        # self.reset_slots()
        pass
