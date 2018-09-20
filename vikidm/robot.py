#!/usr/bin/env python
# encoding: utf-8
import logging
from vikidm.context import Slot
from vikidm.dm import DialogEngine
from vikidm.util import cms_rpc, nlu_predict
log = logging.getLogger(__name__)


class DMRobot(object):
    """
    Every DMRobot instance corresponds to a device.
    """
    robots_pool = {}

    def __init__(self, robot_id, domain_id, domain_name):
        self.domain_id = domain_id
        self.domain_name = domain_name
        self.robot_id = robot_id
        self._dm = DialogEngine()
        self._dm.init_from_db(self.domain_id)
        log.info("CREATE ROBOT: [{0}] of domain [{1}]"
                 .format(robot_id, self.domain_name))

    def _parse_question(self, question):
        """
        Convert question to intent, slots, slots with NLU.
        """
        question = question.strip(' \n')
        context = self.get_context()
        ret = nlu_predict(self.domain_id, context, question)
        slots = [Slot("intent", ret["intent"])]
        for slot_name, value_name in ret["slots"].iteritems():
            slots.append(Slot(slot_name, value_name))
        return ret["intent"], ret["slots"], slots

    def _get_context_slots(self, intent):
        """
        Return slots correspond to all dirty slots in Context.
        """
        slots = {}
        ret2 = cms_rpc.get_intent_slots_without_value(self.domain_id, intent)
        if ret2['code'] != 0:
            log.error("调用错误")
        else:
            for slot_name in ret2['slots']:
                value = self._dm.context[slot_name].value
                if value:
                    slots[slot_name] = value
        return slots

    def process_question(self, question, sid):
        """ Process question from device.

        It will parse question to (`Intent`, Slots, Slots) with NLU and
        query database or call thirdparty service.

        Parameters
        ----------
        question : str, question text from human being.
        sid : str, session id.

        Returns
        -------
        dict.

        """
        # if rpc, pass robot id
        intent, d_slots, slots = self._parse_question(question)
        if intent in [None, "nonsense"]:
            return {
                "code": 0,
                "sid": "",
                "event_id": intent,
                "action": {},
                "nlu": {
                    "intent": intent,
                    "slots": {}
                }
            }
        ret = self._process_slots(slots, sid)
        if intent == 'casual_talk':
            # ret["action"] = {"tts": CasualTalk.get_tuling_answer(question)}
            ret["action"] = {}
        ret["nlu"] = {
            "intent": intent,
            "slots": d_slots
        }
        return ret

    def _process_slots(self, slots, sid):
        dm_ret = self._dm.process_slots(sid, slots)
        if not dm_ret:
            return {
                'code': -1,
                'message': '对话管理无响应',
                "sid": sid,
            }
        ret = cms_rpc.event_id_to_answer(self.domain_id, dm_ret["event_id"])
        if ret["code"] != 0:
            return ret
        return {
            "code": 0,
            "sid": sid,
            "event_id": dm_ret["event_id"],
            "action": ret["answer"],
            "nlu": {
                "ask": dm_ret.get('target', ""),
            }
        }

    def get_context(self):
        """ Return context for NLU module.

        Returns
        -------
        {
            "visible_slots": list,

            "visible_intents": list,

            "agents": list
        }

        """
        return self._dm.get_visible_units()

    def process_slots(self, d_slots, sid):
        """ Process slots input from device

        Parameters
        ----------
        d_slots : dict, slots with diction format.
        sid : str, session id.

        Returns
        -------
        dict.

        """
        slots = [Slot(key, value)
                    for key, value in d_slots.iteritems()]
        return self._process_slots(slots, sid)

    def process_event(self, event_id):
        """ Process event from device.

        System will convert event to `Slots`

        Parameters
        ----------
        event_id : str, event id.

        Returns
        -------
        dict.

        """
        pass

    def process_confirm(self, sid, d_confirm):
        """ Process confirm form device.

        System use sid to identify which request to confirm.

        Parameters
        ----------
        sid : str, correspond to request sid.
        d_confirm : dict,
            {
                'code': 0,  // 0 -- success; others -- failed.

                'message': ''
            }

        Returns
        -------
        dict.
        {
            'code': 0,  // always success

            'message': ''
        }

        """
        return self._dm.process_confirm(sid, d_confirm)

    def update_slots_by_backend(self, d_slots):
        """ Update by business service.

        Parameters
        ----------
        d_slots : dict, dict of slots.

        Returns
        -------
        dict.
        {
            "code": 0   // alway success
        }

        """
        slots = [Slot(key, value)
                    for key, value in d_slots.iteritems()]
        self._dm.update_by_remote(slots)
        log.info(self._dm.context)
        return {
            "code": 0,
        }

    @classmethod
    def get_robot(self, robotid, domain_id, domain_name):
        """ Get a DMRobot instance with device id and it's application id.

        If there is no correspond robot instance in the robots buffer,
        create one. Otherwise, return the buffered one.

        Parameters
        ----------
        robotid : str, device id.
        domain_id : str, application id.
        domain_name : str, name of domain

        Returns
        -------
        DMRobot.

        """
        robot = DMRobot.robots_pool.get(robotid, None)
        if robot:
            return robot
        robot = DMRobot(robotid, domain_id, domain_name)
        DMRobot.robots_pool[robotid] = robot
        return robot

    @classmethod
    def reset_robot(self, robotid, domain_id):
        """ Delete old robot from buffer and recreate new one.

        Parameters
        ----------
        robotid : str, device id.
        domain_id : str, application id.

        """
        robot = DMRobot(robotid, domain_id)
        robot.nlu.reset_robot()
        DMRobot.robots_pool[robotid] = robot
