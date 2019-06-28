#!/usr/bin/env python
# encoding: utf-8
import logging
from eva.dm.units import (
    Agent,
    BizUnit,
    TargetAgent,
    TargetAgency,
    ClusterAgency,
    AbnormalHandler
)


log = logging.getLogger(__name__)


class TopicController(object):
    """"""
    def __init__(self):
        self.stack = None

    def ancestor_in_stack(self, unit):
        temp = unit  # inlcude itself
        while temp.parent is not None:
            if temp in self.stack.stack._items:
                return True
            temp = temp.parent
        return False

    def is_ancestor_of(self, source, target):
        #  TODO: test #
        temp = target.parent
        while temp is not None:
            if temp == source:
                return True
            temp = temp.parent
        return False

    def same_topic(self, source, target):
        #  TODO: test
        # share a none root ancestor
        temp1 = source
        while temp1.parent.is_root() == False:
            temp1 = temp1.parent

        temp2 = target
        while temp2.parent.is_root() == False:
            temp2 = temp2.parent
        return temp1 == temp2

    def notify_switch_topic(self):
        pass

    def hierarchy_trigger(self, unit):
        """ Activate and return the top ancestor node in the stack.

        It will push `trigger_child` node to stack.
        """
        if unit.parent.is_root():
            if unit.state == BizUnit.STATUS_TREEWAIT:
                self.stack.push(unit)
            unit.set_state(BizUnit.STATUS_TRIGGERED)
            return unit

        ancestor = unit
        while not ancestor.parent.is_root():
            ancestor.parent.trigger_child = ancestor
            ancestor = ancestor.parent

        if ancestor.parent.is_root():
            # push to stack and triggered
            if ancestor.state == BizUnit.STATUS_TREEWAIT:
                self.stack.push(ancestor)
            ancestor.set_state(BizUnit.STATUS_TRIGGERED)
            return ancestor
        else:
            ancestor.parent.set_state(BizUnit.STATUS_TRIGGERED)
            ancestor.parent.trigger_child = ancestor
            return ancestor.parent

    def trigger_bizunit(self, visible_agents):
        # 如果多个，都执行，就需要多个反馈，可能需要主动推送功能。
        # 目前只支持返回一个。
        for bizunit in visible_agents:
            if not isinstance(bizunit, Agent):
                continue
            if not bizunit.satisfied():
                continue
            log.debug("Init Trigger: {0}".format(bizunit))
            new_focus = self.hierarchy_trigger(bizunit)
            # Remove units not in the hierarchy path,
            # except 'casual_talk'
            self._clear_focus_to_stack_top(new_focus)
            self._clear_focus_to_root()
            # 清理trigger到栈顶间的节点
            log.debug("Triggered Stack:")
            log.debug(self.stack)
            return new_focus

    def _clear_focus_to_root(self):
        if self.stack.top().tag != 'casual_talk':
            focus = self.stack.pop()
            for unit in reversed(self.stack.items[1:]):
                to_pop_unit = self.stack.pop()
                to_pop_unit.set_state(BizUnit.STATUS_TREEWAIT)
                to_pop_unit.reset_slots()
            self.stack.push(focus)

    def _clear_focus_to_stack_top(self, focus):
        """
        Note: Won't reset concepts if ancestor node in the stack, but may clear
        shared slots.
        """
        count = 0
        for unit in reversed(self.stack.items):
            if unit == focus:
                break
            count += 1
        while count > 0:
            to_pop_unit = self.stack.pop()
            to_pop_unit.set_state(BizUnit.STATUS_TREEWAIT)
            to_pop_unit.reset_slots()
            count -= 1

    def pop_focus_unit(self, old_focus_unit):
        self.stack.pop()
        old_focus_unit.set_state(BizUnit.STATUS_TREEWAIT)
        old_focus_unit.reset_slots()
        log.debug("POP_STACK: {0}({1})".format(
            old_focus_unit.__class__.__name__, old_focus_unit.tag))

        new_focus_unit = self.stack.top()
        if old_focus_unit.parent and old_focus_unit.parent != new_focus_unit:
            # Topic switch.
            # previous focus and current focus not in the same hierarchy path.
            pass
            log.debug("ROUND_RETURN BizUnit({0})".format(new_focus_unit.tag))
            new_focus_unit.restore_topic_and_focus()
        elif not new_focus_unit.is_root():
            # same hierarchy path.
            new_focus_unit.restore_focus_after_child_done()
