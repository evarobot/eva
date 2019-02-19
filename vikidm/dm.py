#!/usr/bin/env python
# encoding: utf-8
import copy
import logging
import pprint
import time
import os

from vikicommon.timer import TimerReset
from vikidm import errors
from vikidm.util import PROJECT_DIR, cms_gate
from vikidm.stack import Stack
from vikidm.context import Context
from vikidm.topic import TopicController
from vikidm.biztree import BizTree
from vikidm.agenda import ExpectAgenda
from vikidm.units import (
    Agent,
    BizUnit,
    TargetAgent,
    TargetAgency,
    ClusterAgency,
    AbnormalHandler
)

log = logging.getLogger(__name__)


class Session(object):
    def __init__(self):
        self._sid = None

    def begin_session(self, sid):
        self._sid = sid

    def valid_session(self, sid):
        return self._sid and sid >= self._sid

    def end_session(self):
        self._sid = None

    def new_session(self, sid):
        return self._sid is not None and sid > self._sid


class DialogEngine(object):
    """ Dialog Manager.

    Any Device correspond to a `DialogEngine` instance, which maintain the
    dialogue status of device and answer request from device.

    Attributes
    ----------
    SAFE_UPPER_LIMIT : 100, the maximum execution loop between two request,
                       used to recover from endless loop if there is a bug.
    MAX_CONTEXT_RESERVED_ROUND : The maximum rounds that context will reserved.
    context : Context, maintaining the slot status of device.
    stack : Stack, maintaining the active interaction history.
    _timer : TimerRest, Calling handle function when timeout.
    _agenda : ExpectAgenda, Manage the visiblility of bizunit.
    _session : Session, Manage dialogue session.
    _topic : TopicController, Manage Topic switch and select trigger agent.
    countdown_round : Countdown by none `TargetAgent` or `TargetAgency`
        dialog quantity.
    """
    SAFE_UPPER_LIMIT = 100
    MAX_CONTEXT_RESERVED_ROUND = 2

    def __init__(self, topic_controller):
        self.context = Context()
        self.biz_tree = BizTree()
        self.stack = Stack()
        self._session = Session()
        self._agenda = ExpectAgenda(self.stack)
        self._topic = topic_controller
        self._topic.stack = self.stack
        self.countdown_round = 0
        self.countdown_unit = None

        self._timer = None
        self._debug_timer_count = 0
        self.debug_loop = 0
        self.debug_timeunit = 1  # 为了测试的时候加速时间计数

    @classmethod
    def get_dm(self, version="0.1"):
        """TODO: Docstring for get_dm.

        Parameters
        ----------
        version : version of DialogEngine

        Returns
        -------
        DialogEngine.

        """
        if version == "0.1":
            topic = TopicController()
            dm = DialogEngine(topic)
            return dm

    @property
    def is_waiting(self):
        """
        If DM is in the waiting user's input.
        """
        return self.stack.top().state in [BizUnit.STATUS_WAIT_ACTION_CONFIRM,
                                          BizUnit.STATUS_WAIT_TARGET]

    def init_from_db(self, domain_id):
        """ Initialize DM from database.

        It will call `evecms.get_dm_biztree`.
        If failed, return `DMError.RPCError`

        Parameters
        ----------
        domain_id : str, Project id.

        Returns
        -------
        None

        """
        ret = cms_gate.get_dm_biztree(domain_id)
        if ret['code'] != 0:
            raise errors.RPCError
        self.biz_tree.init_from_json(ret['tree'], self)
        root = self.biz_tree.get_node(self.biz_tree.root)
        fpath = os.path.join(PROJECT_DIR, "data", "casual_talk.json")
        with open(fpath, 'r') as file_obj:
            casual_talk_json = file_obj.read()
        self.biz_tree.add_subtree_from_json(casual_talk_json, root, self)
        self._init_context()
        node = self.biz_tree.get_node(self.biz_tree.root)
        node.set_state(BizUnit.STATUS_STACKWAIT)
        self.stack.push(node)
        self._agenda.compute_visible_units()

    def _init_context(self):
        for bizunit in self.biz_tree.all_nodes_itr():
            if isinstance(bizunit, Agent):
                for slot in bizunit.trigger_slots + bizunit.target_slots:
                    slot = copy.deepcopy(slot)
                    self.context.add_slot(slot)

    def execute_focus_agent(self):
        """
        Main routine of DM.

        Returns
        -------
        dict.

        """
        ret = {}
        focus_unit = self.stack.top()
        while focus_unit.transferable():
            if focus_unit.is_completed() or focus_unit.is_abnormal():
                self._topic.pop_focus_unit(focus_unit)
                log.debug("STATUS: \n{0}\n{1}".format(self.stack, self.context))
            else:
                ret = focus_unit.execute()
            focus_unit = self.stack.top()
            self.debug_loop += 1
            if self.debug_loop >= DialogEngine.SAFE_UPPER_LIMIT:
                #  TODO: recover from bug #
                assert(False)
        return ret

    def process_slots(self, sid, slots):
        """ Process user inputs.

        Dialogue text or events will be coverted to `Slot` list, as input
        of DialogEngine.

        Parameters
        ----------
        sid : Dialog session. Every dialog contains a `process_slots` and
             `process_confirm` calling pair. `sid` is used to pairing two call.
        slots : [], `Slot` instance list.

        Returns
        -------
        {
            'response_id': "id of event"
                        // Used to extract answer from db or event notifying.

            'target': ['slot_key1', 'slot_key2', ..]
                    // Tell the recommend system which slot to fill.
        }

        """
        self.debug_loop = 0
        log.info("-------- {0} ----- {1} -------------------".format(
            sid, slots))
        if self._session.new_session(sid) or self.is_waiting:
            focus = self.stack.top()
            if focus.state == BizUnit.STATUS_WAIT_ACTION_CONFIRM:
                # Could be a remote error
                self.cancel_timer()
                log.debug("NEW_SESSION, ABANDON OLD CONFIRM WAITING")
                log.debug("CANCEL_TIMER {0}({1})".format(
                    self._timer.owner.__class__.__name__,
                    self._timer.owner.tag))
        self._session.begin_session(sid)
        self._update_slots(slots)
        self._mark_completed_bizunits()
        new_focus = self._topic.trigger_bizunit(self._agenda.visible_agents)
        if new_focus is None:
            log.debug("INVALID AGENTS")
            log.debug(
                "Valid Agents: {0}".format(self._agenda.show_visible_agents()))

        ret = self.execute_focus_agent()
        if not ret:
            self._session.end_session()
        log.info(self.stack)
        log.info(self.context)
        log.info("\n            Round:\n                {0}".format(
            self.countdown_round))
        #  @OPTIMIZE return then compute visible units
        self._agenda.compute_visible_units()
        return ret

    def _update_slots(self, slots):
        # OPTIMIZE:  `get_visible_units` control the range of activation,
        # maybe checking here is not necessary.
        visible_slots = []
        for agent in self._agenda.visible_agents:
            visible_slots.extend(agent.target_slots)
            visible_slots.extend(agent.trigger_slots)
        visible_slots = set([c.key for c in visible_slots])
        for slot in slots:
            if slot.key == "intent":
                if slot.value in self._agenda.visible_intents:
                    self.context.update_slot(slot.key, slot)
            else:
                # or check with visible_slots and slots of triggered intent.
                self.context.update_slot(slot.key, slot)

    def _mark_completed_bizunits(self):
        for bizunit in self.biz_tree.all_nodes_itr():
            if isinstance(bizunit, TargetAgent):
                completed = all([self.context.dirty(c.key)
                                 for c in bizunit.target_slots])
                if completed:
                    bizunit.set_state(BizUnit.STATUS_TARGET_COMPLETED)

    def process_confirm(self, sid, data):
        """ Process action confirmation from device.

        After receiving command from DM, device must send a confirmation
        request to DM to notify the result of command execution.

        Parameters
        ----------
        sid : str, see `DialogEngine.process_slots`

        data: dict, `{'code' : 0, 'message': ''}`

        Returns
        -------
        {
            'code': 0,
        }

        """
        log.info("======== {0} ===== {1} ==================".format(sid, data))
        self.debug_loop = 0
        ret = {
            'code': 0,
            'message': ''
        }
        if not self._session.valid_session(sid):
            log.info("IGNORE_OLD_SESSION_CONFIRM")
            return ret
        if data['code'] != 0:
            self._handle_failed_confirm()
        else:
            self._handle_success_confirm()
        log.info(self.stack)
        log.info(self.context)
        log.info("\n            Round:\n                {0}".format(
            self.countdown_round))
        return ret

    def _handle_failed_confirm(self):
        self._handle_abnormal(AbnormalHandler.ABNORMAL_ACTION_FAILED)
        self.cancel_timer()
        log.debug("CANCEL_TIMER {0}({1})".format(
            self._timer.owner.__class__.__name__, self._timer.owner.tag))

    def _handle_success_confirm(self):
        focus_unit = self.stack.top()
        assert(isinstance(focus_unit, Agent))
        log.debug("CONFIRM: {0}".format(focus_unit.tag))
        self.cancel_timer()
        log.debug("CANCEL_TIMER {0}({1})".format(
            self._timer.owner.__class__.__name__, self._timer.owner.tag))
        focus_unit.on_confirm()
        self.execute_focus_agent()
        self._session.end_session()

    def _handle_abnormal(self, abnormal_type):
        abnormal = AbnormalHandler(self, self.stack.top(), abnormal_type)
        self.stack.push(abnormal)
        self.execute_focus_agent()
        self._session.end_session()

    def start_timer(self, bizunit, seconds, function, *args, **kwargs):
        """ Start an timer.

        Make sure there is at most one timer active for any DM instance.

        Parameters
        ----------
        bizunit : Bizunit, instance that start the timer.
        seconds : float, time interval of the timer in seconds.
        function : funtion, handle function to call.
        *args : tuple, args for the handle function.
        **kwargs : dict, kwargs for the handle function.

        """
        assert(self._debug_timer_count == 0)
        self._timer = TimerReset(bizunit, seconds * self.debug_timeunit,
                                 function, *args, **kwargs)
        self._start_time = time.time()
        self._debug_timer_count += 1
        self._timer.start()

    def cancel_timer(self):
        self._debug_timer_count -= 1
        self._timer.cancel()

    def update_by_remote(self, slots):
        """ Called directly by thirdparty service like recommendation system,
        to update slots.

        Parameters
        ----------
        slots : [], `Slot` instance list.

        """
        focus_unit = self.stack.top()
        assert(isinstance(focus_unit.parent, TargetAgency))
        # @BUG Device may update DM before recommendation system.
        focus_unit.parent.api_slot_keys = [c.key for c in slots]
        self._update_slots(slots)
        self._agenda.compute_visible_units()

    def get_visible_units(self):
        """ Return visible units at the moment. """
        # self._agenda.compute_visible_units()
        agents = []
        for agent in self._agenda.visible_agents:
            parent = agent.parent
            identifier = agent.identifier
            if isinstance(parent, TargetAgency) or\
                    isinstance(parent, ClusterAgency):
                identifier = parent.identifier
            agents.append((agent.tag, agent.intent, identifier))

        return {
            "visible_slots": list(self._agenda.visible_slots),
            "visible_intents": list(self._agenda.visible_intents),
            "intent": self.context["intent"].value,
            "agents": agents
        }

    def reset_countdown_round(self):
        """ Reset count down round to zero.

        """
        self.countdown_unit = self.stack.top()
        self.countdown_round = 0

    def round_out(self):
        """ If `countdown_unit` have been waiting targets for some maximum
        rounds.

        """
        return self.countdown_round >= self.MAX_CONTEXT_RESERVED_ROUND

    def on_actionwait_timeout(self):
        """
        Invoked when device failed to send an action confirm to agents in time.
        """
        self._debug_timer_count -= 1
        delta = (time.time() - self._start_time) / self.debug_timeunit
        focus_unit = self.stack.top()
        log.debug("ACTION_TIMEOUT {2}({0}) {1}".format(
            self._timer.owner.tag, delta, focus_unit.__class__.__name__))
        self._handle_abnormal(AbnormalHandler.ABNORMAL_ACTION_TIMEOUT)
        self._agenda.compute_visible_units()

    def on_inputwait_round_out(self):
        """
        Invoked when device failed to send an inputting request
        to agents in time.
        """
        self.countdown_round = 0
        self.countdown_unit = None
        focus_unit = self.stack.top()
        log.debug("INPUT_ROUND_OUT {1}({0})".format(
            focus_unit.tag, focus_unit.__class__.__name__))
        self._handle_abnormal(AbnormalHandler.ABNORMAL_INPUT_TIMEOUT)
        self._agenda.compute_visible_units()

    def on_delaywait_round_out(self):
        """
        Invoked when device failed to send a new input request to agencies.
        """
        self.countdown_round = 0
        self.countdown_unit = None
        focus_unit = self.stack.top()
        log.debug("DELAY_TIMEOUT {1}({0})".format(
            focus_unit.tag, focus_unit.__class__.__name__))
        focus_unit.set_state(BizUnit.STATUS_AGENCY_COMPLETED)
        self.execute_focus_agent()
        self._agenda.compute_visible_units()

    def debug_info(self):
        msg = '''
        {0}
        {1}
        {2}
        '''
        return msg.format(
            str(self.stack),
            str(self.context),
            pprint.pformat(self.biz_tree.to_dict(with_data=True)))
