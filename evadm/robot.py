#!/usr/bin/env python
# encoding: utf-8
import logging

from evadm.context import Slot
from evadm.dm import DialogEngine
from evadm.util import cms_gate, nlu_gate
from evadm.io import DMIO
from evanlu.robot import NLURobot

log = logging.getLogger(__name__)


class EvaRobot(object):
    def __init__(self, robot_id, domain_id, domain_name):
        self._dm_robot = DMRobot.get_robot(robot_id, domain_id, domain_name)
        self._nlu_robot = NLURobot.get_robot(domain_id)

    def process_question(self, question):
        question = question.strip(' \n')
        context = self._dm_robot.get_context()
        ret = self._nlu_robot.predict(context, question)
        ret = self._dm_robot.process_request(ret["intent"],
                                             ret["entities"],
                                             ret["target_entities"],
                                             0)
        self._dm_robot.process_confirm(ret["sid"], {"code": 0})
        return ret

    def train(self):
        self._nlu_robot.train()


class DMRobot(object):
    """
    Every DMRobot instance corresponds to a device.
    """
    robots_pool = {}

    def __init__(self, robot_id, domain_id, domain_name):
        self.domain_id = domain_id
        self.domain_name = domain_name
        self._dm = DialogEngine.get_dm(DMIO(domain_id), "0.1")
        log.info("CREATE ROBOT: [{0}] of domain [{1}]"
                 .format(robot_id, self.domain_name))

    def load_data(self):
        self._dm.load_data()

    def _get_context_slots(self, intent):
        """
        Return slots correspond to all dirty slots in Context.
        """
        slots = {}
        ret2 = cms_gate.get_intent_entities_without_value(self.domain_id, intent)
        if ret2['code'] != 0:
            log.error("调用错误")
        else:
            for slot_name in ret2['slots']:
                value = self._dm.context[slot_name].value
                if value:
                    slots[slot_name] = value
        return slots

    def process_request(self, intent, d_slots, related_slots, sid):
        """ Process question from device.

        It will parse question to (`Intent`, Slots, Slots) with NLU and
        query database or call thirdparty service.


        Returns
        -------
        dict.

        """
        ret = {
            "code": 0,
            "sid": "",
            "response": {
                "tts": "噪音导致的胡话",
                "web": {}
            },
            "event": {
                "intent": intent,
                "slots": {}
            },
            "nlu": {
                "intent": intent,
                "slots": {}
            }
        }
        if intent in [None, "nonsense"]:
            # When intent is invalid in current context, NLU return None.
            return ret
        if intent == "sensitive":
            ret["response"]["tts"] = "很抱歉，这个问题我还不太懂。"
            return ret
        slots = [Slot("intent", intent)]
        for slot_name, value_name in d_slots.items():
            slots.append(Slot(slot_name, value_name))
        ret = self._process_slots(slots, sid, intent)

        d_slots = {}
        for s_slot in related_slots:
            slot = self._dm.context[s_slot]
            if slot.value is not None:
                d_slots[slot.key] = slot.value

        ret["nlu"] = {
            "intent": intent,
            "slots": d_slots
        }
        return ret

    def _process_slots(self, slots, sid, intent=None):
        dm_ret = self._dm.process_slots(sid, slots)
        response_id = dm_ret["response_id"]
        if not dm_ret:
            intent = 'casual_talk'
            response_id = 'casual_talk'
        return {
            "intent": intent,
            "sid": sid,
            "response_id": response_id,
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
        slots = [Slot(key, value) for key, value in d_slots.items()]
        return self._process_slots(slots, sid)

    def process_event(self, response_id):
        """ Process event from device.

        System will convert event to `Slots`

        Parameters
        ----------
        response_id : str, event id.

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
        slots = [Slot(key, value) for key, value in d_slots.items()]
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
        robot.load_data()
        DMRobot.robots_pool[robotid] = robot
        return robot

    @classmethod
    def reset_robot(self, robotid, domain_id, domain_name):
        """ Delete old robot from buffer and recreate new one.

        Parameters
        ----------
        robotid : str, device id.
        domain_id : str, application id.

        """
        robot = DMRobot(robotid, domain_id, domain_name)
        robot.load_data()
        DMRobot.robots_pool[robotid] = robot
        return robot
