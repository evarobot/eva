#!/usr/bin/env python
# encoding: utf-8

from vikidm.units.bizunit import BizUnit
from vikidm.units.agent import Agent
import logging
log = logging.getLogger(__name__)


class AbnormalHandler(BizUnit):
    """ An abnormal controller.

    It always associate with an specific handle angent, dependent on abnormal
    type.

    Controlling logic is simililar with `ClusterAgency`. When Abnormal
    hanppens, It will be pushed to stack, then the handler agent executed.
    Finally, set the abnormal unit and it's agency parent(if any) to
    STATUS_ABNORMAL state.  The main routine will pop STATUS_ABNORMAL unit.

    Attributes
    ----------

    """
    ABNORMAL_ACTION_TIMEOUT = "ABNORMAL_ACTION_TIMEOUT"
    ABNORMAL_ACTION_FAILED = "ABNORMAL_ACTION_FAILED"
    ABNORMAL_INPUT_TIMEOUT = "ABNORMAL_INPUT_TIMEOUT"

    def __init__(self, dm, bizunit, type_):
        data = {
            'trigger_slots': []
        }
        super(AbnormalHandler, self).__init__(dm, 'AbnormalHandler',
                                              'AbnormalHandler', data)
        self.set_state(BizUnit.STATUS_TRIGGERED)
        self.parent = None
        self.target_slots = []
        self.trigger_slots = []
        self.handler = self._get_handler(bizunit, type_)
        self.handler.parent = self
        self._child_activated = False

    def restore_focus_after_child_done(self):
        """
        see :meth:`~vikidm.units.agency.Agency.restore_focus_after_child_done`
        """
        if not self.is_root() and self.state != BizUnit.STATUS_ABNORMAL:
            self.set_state(BizUnit.STATUS_TRIGGERED)

    def _get_handler(self, bizunit, type_):
        if type_ == self.ABNORMAL_ACTION_FAILED:
            return ActionFailedAgent(self._dm, bizunit)
        elif type_ == self.ABNORMAL_ACTION_TIMEOUT:
            return ActionTimeoutAgent(self._dm, bizunit)
        elif type_ == self.ABNORMAL_INPUT_TIMEOUT:
            return InputTimeoutAgent(self._dm, bizunit)

    def is_root(self):
        """ If is a root unit.  """
        return False

    def _execute(self):
        log.debug("EXECUTE AbnormalHandler({0})".format(self.handler.tag))
        if self._child_activated:
            self._mark_abnormal_unit(
                self._dm.stack, self._dm.biz_tree, self._dm.stack._items[-2])
            self._dm.stack.pop()
            self.set_state(BizUnit.STATUS_TREEWAIT)
            return self.state
        # push handler unit
        self.handler.set_state(Agent.STATUS_TRIGGERED)
        self.set_state(BizUnit.STATUS_STACKWAIT)
        self._dm.stack.push(self.handler)
        self._child_activated = True
        return self.state

    def _mark_abnormal_unit(self, stack, tree, abnormal_unit):
        """
        Mark the abnormal unit and it's Agency parent ABNORMAL.
        """
        parent = tree.parent(abnormal_unit.identifier)
        for unit in reversed(stack._items[:-1]):
            if unit == abnormal_unit or\
                    unit == parent and not parent.is_root():
                unit.set_state(BizUnit.STATUS_ABNORMAL)


class DefaultHandlerAgent(Agent):
    def __init__(self, dm, bizunit, data):
        data.update({
            'subject': '',
            'scope': '',
            'timeout': 0,  #
            'entrance': False,
            'trigger_slots': {},
            'state': '',
            'id': 'default_handler',
            'target_slots': [],
        })
        self._trigger_slots = []
        self._target_slots = []
        super(DefaultHandlerAgent, self).__init__(dm, data["id"], data)

    def _execute(self):
        if self.state == BizUnit.STATUS_TRIGGERED:
            if self.timeout == 0:
                # device don't deal with error right now, so confirm
                # immediately
                self.set_state(BizUnit.STATUS_ACTION_COMPLETED)
            else:
                self.set_state(BizUnit.STATUS_WAIT_ACTION_CONFIRM)
                self._dm._start_timer(
                    self.tag, self.timeout, self._dm._actionwait_timeout)
                log.debug("START_TIMER BizUnit({0})".format(self.tag))
        # subclass could custom returned answer.
        return {'response_id': self.response_id, 'target': []}


class ActionFailedAgent(DefaultHandlerAgent):
    def __init__(self, dm, bizunit):
        data = {
            'response_id': 'FAILED|' + bizunit.response_id,
            'tag': 'FAILED|' + bizunit.response_id,
        }
        super(ActionFailedAgent, self).__init__(dm, data["response_id"], data)


class InputTimeoutAgent(DefaultHandlerAgent):
    def __init__(self, dm, bizunit):
        data = {
            'response_id': 'INPUT_TIMEOUT|' + bizunit.response_id,
            'tag': 'INPUT_TIMEOUT|' + bizunit.response_id,
        }
        super(InputTimeoutAgent, self).__init__(dm, data["response_id"], data)


class ActionTimeoutAgent(DefaultHandlerAgent):
    def __init__(self, dm, bizunit):
        data = {
            'response_id': 'ACTION_TIMEOUT|' + bizunit.response_id,
            'tag': 'ACTION_TIMEOUT|' + bizunit.response_id,
        }
        super(ActionTimeoutAgent, self).__init__(dm, data["response_id"], data)
