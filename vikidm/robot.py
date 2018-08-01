#!/usr/bin/env python
# encoding: utf-8
import logging
import time
from vikidm.context import Concept
from vikidm.chat import CasualTalk
from vikidm.dm import DialogEngine
from evecms.models import Domain
from vikidm.util import cms_rpc
from vikinlu.robot import NLURobot
log = logging.getLogger(__name__)


class DMRobot(object):
    """
    Every DMRobot instance corresponds to a device.
    """
    robots_pool = {}

    def __init__(self, robot_id, domain_id):
        self.domain_id = domain_id
        self.domain_name = Domain.objects.with_id(domain_id).name
        self.robot_id = robot_id
        self._dialog = DialogEngine()
        self._dialog.init_from_db(self.domain_id)
        self.nlu = NLURobot.get_robot(domain_id)
        log.info("CREATE ROBOT: [{0}] of domain [{1}]"
                 .format(robot_id, self.domain_name))

    def _parse_question(self, question):
        """
        Convert question to intent, slots, concepts with NLU.
        """
        question = question.strip(' \n')
        ret = self.nlu.predict(self, question)
        concepts = [Concept("intent", ret["intent"])]
        for slot_name, value_name in ret["slots"].iteritems():
            concepts.append(Concept(slot_name, value_name))
        return ret["intent"], ret["slots"], concepts

    def _get_context_concepts(self, intent):
        """
        Return slots correspond to all dirty concepts in Context.
        """
        slots = {}
        ret2 = cms_rpc.get_intent_slots_without_value(self.domain_id, intent)
        if ret2['code'] != 0:
            log.error("调用错误")
        else:
            for slot_name in ret2['slots']:
                value = self._dialog.context[slot_name].value
                if value:
                    slots[slot_name] = value
        return slots

    def process_question(self, question):
        """ Process question from device.

        It will parse question to (`Intent`, Slots, Concepts) with NLU and
        query database or call thirdparty service.

        Parameters
        ----------
        question : str, question text from human being.

        Returns
        -------
        dict.

        """
        # if rpc, pass robot id
        intent, slots, concepts = self._parse_question(question)
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
        ret = self._process_concepts(intent, slots, concepts)
        if intent == 'casual_talk':
            ret["action"] = {"tts": CasualTalk.get_tuling_answer(question)}
        ret["nlu"]["intent"] = intent
        ret["nlu"]["slots"] = slots
        return ret

    def _process_concepts(self, intent, concepts):
        sid = int(round(time.time() * 1000))
        dm_ret = self._dialog.process_concepts(sid, concepts)
        if dm_ret is None:
            return {
                'code': -1,
                'message': '对话管理无响应',
                "sid": sid,
            }
        action = cms_rpc.event_id_to_answer(self.domain_id,
                                            dm_ret["event_id"])
        return {
            "code": 0,
            "sid": sid,
            "event_id": dm_ret["event_id"],
            "action": action,
            "nlu": {
                "ask": dm_ret.get('target', ""),
            }
        }

    def process_concepts(self, d_concepts):
        """ Process concepts input from device

        Parameters
        ----------
        d_concepts : dict, concepts with diction format.

        Returns
        -------
        dict.

        """
        concepts = [Concept(key, value)
                    for key, value in d_concepts.iteritems()]
        return self._process_concepts(concepts)

    def process_event(self, event_id):
        """ Process event from device.

        System will convert event to `Concepts`

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
        return self._dialog.process_confirm(sid, d_confirm)

    def update_concepts_by_backend(self, d_concepts):
        """ Update by business service.

        Parameters
        ----------
        d_concepts : dict, dict of concepts.

        Returns
        -------
        dict.
        {
            "code": 0   // alway success
        }

        """
        concepts = [Concept(key, value)
                    for key, value in d_concepts.iteritems()]
        self._dialog.update_by_remote(concepts)
        log.info(self._dialog.context)
        return {
            "code": 0,
        }

    @classmethod
    def get_robot(self, robotid, domain_id):
        """ Get a DMRobot instance with device id and it's application id.

        If there is no correspond robot instance in the robots buffer,
        create one. Otherwise, return the buffered one.

        Parameters
        ----------
        robotid : str, device id.
        domain_id : str, application id.

        Returns
        -------
        DMRobot.

        """
        robot = DMRobot.robots_pool.get(robotid, None)
        if robot:
            return robot
        robot = DMRobot(robotid, domain_id)
        DMRobot.robots_pool[robotid] = robot
        return robot

    @classmethod
    def reset_robot(self, robotid, domain_id):
        """ Delete old robot from buffer and recreate new one.

        Parameters
        ----------
        robotid : str, device id.
        domain_id : str, application id.

        Returns
        -------
        DMRobot.

        """
        robot = DMRobot(robotid, domain_id)
        robot.nlu.reset_robot()
        DMRobot.robots_pool[robotid] = robot
        return True
