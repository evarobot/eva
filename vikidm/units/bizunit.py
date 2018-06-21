#!/usr/bin/env python
# encoding: utf-8

import treelib
import logging

log = logging.getLogger(__name__)


class BizUnit(treelib.Node):
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
        self._dm = dm
        self.set_state(self.STATUS_TREEWAIT)
        self._execute_condition = set([BizUnit.STATUS_TRIGGERED, BizUnit.STATUS_TARGET_COMPLETED,
                                       BizUnit.STATUS_ACTION_COMPLETED, BizUnit.STATUS_ABNORMAL,
                                       BizUnit.STATUS_AGENCY_COMPLETED])
        self.parent = None
        self._trigger_child = None

    @property
    def trigger_child(self):
        return self._trigger_child

    @trigger_child.setter
    def trigger_child(self, v):
        self._trigger_child = v
        self._handler_finished = False

    def execute(self):
        if self.state in [BizUnit.STATUS_ACTION_COMPLETED,
                          BizUnit.STATUS_AGENCY_COMPLETED,
                          BizUnit.STATUS_ABNORMAL,
                          BizUnit.STATUS_TARGET_COMPLETED]:
            self._dm._focus_bizunit_out(self)
            return None
        return self._execute()


    def re_enter_after_child_done(self):
        if not self.is_root() and self.state != BizUnit.STATUS_ABNORMAL:
            self.set_state(BizUnit.STATUS_TRIGGERED)

    def set_state(self, value):
        self.state = value

    def executable(self):
        return self.state in self._execute_condition

    def pop_from_stack(self, reset=True):
        #  TODO: 改名 #
        self.set_state(BizUnit.STATUS_TREEWAIT)
        if reset:
            self.reset_concepts()

    def trigger(self):
        if self.state == BizUnit.STATUS_TREEWAIT:
            self._dm.stack.push(self)
        self.set_state(BizUnit.STATUS_TRIGGERED)

    def hierarchy_trigger(self):
        unit = self
        if unit.parent.is_root():
            unit.trigger()
            return
        while unit.parent.state == BizUnit.STATUS_TREEWAIT:
            # find the first ancestor node whose parent is in the stack.
            unit.parent.trigger_child = unit
            unit = unit.parent
        if unit.parent.is_root():
            # push to stack and triggered
            if unit.state == BizUnit.STATUS_TREEWAIT:
                self._dm.stack.push(unit)
            unit.set_state(BizUnit.STATUS_TRIGGERED)
        else:
            unit.parent.set_state(BizUnit.STATUS_TRIGGERED)
            unit.parent.trigger_child = unit

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
        #self.reset_concepts()
        pass
