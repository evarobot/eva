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


