#!/usr/bin/env python
# encoding: utf-8
import logging
import time
from vikinlu.robot import NLURobot
from vikidm.dm import DialogEngine
from vikidm.context import Concept
from vikidm.util import cms_rpc
from vikidm.chat import CasualTalk
from evecms.models import Domain
log = logging.getLogger(__name__)


class DMRobot(object):
    robots_pool = {}

    def __init__(self, robot_id, domain_id):
        self.domain_id = domain_id
        self.domain_name = Domain.objects.with_id(domain_id).name
        self.robot_id = robot_id
        self._dialog = DialogEngine()
        self._dialog.init_from_db(self.domain_id)
        self.nlu = NLURobot.get_robot(domain_id)
        log.info("CREATE ROBOT: [{0}] of domain [{1}]".format(robot_id, self.domain_name))

    def process_question(self, question):
        # if rpc, pass robot id
        question = question.strip(' \n')
        ret = self.nlu.predict(self, question)
        if ret["intent"] in [None, "nonsense"]:
            return {
                "code": 0,
                "sid": "",
                "event_id": ret["intent"],
                "action": {},
                "nlu": {
                    "intent": ret["intent"],
                    "slots": {}
                }
            }
        else:
            concepts = []
            concepts.append(Concept("intent", ret["intent"]))
            for slot_name, value_name in ret["slots"].iteritems():
                concepts.append(Concept(slot_name, value_name))
            sid = int(round(time.time() * 1000))
            dm_ret = self._dialog.process_concepts(sid, concepts)
            if dm_ret is None:
                return {
                    'code': -1,
                    'message': '对话管理无响应',
                    "sid": sid,
                    "event_id": "",
                    "action": {},
                    "nlu": {
                        "intent": ret["intent"],
                        "ask": "",
                        "slots": ret["slots"]
                    },
                    "debug": {
                        "stack": str(self._dialog.stack),
                        "context": str(self._dialog.context),
                    }
                }
            slots = {}
            ret2 = cms_rpc.get_intent_slots_without_value(self.domain_id, ret["intent"])
            if ret2['code'] != 0:
                log.error("调用错误")
            else:
                for slot_name in ret2['slots']:
                    value = self._dialog.context[slot_name].value
                    if value:
                        slots[slot_name] = value
            #for concept in self._dialog.context._all_concepts.values():
                #if concept.dirty and concept.key != "intent":
                    #slots[concept.key] = concept.value
            action = cms_rpc.event_id_to_answer(self.domain_id, dm_ret["event_id"])
            if ret["intent"] == "casual_talk":
                tts = CasualTalk.get_tuling_answer(question)
                action["tts"] = tts
            return {
                "code": 0,
                "sid": sid,
                "event_id": dm_ret["event_id"],
                "action": action,
                "nlu": {
                    "intent": ret["intent"],
                    "ask": dm_ret.get('target', ""),
                    "slots": slots
                },
                "debug": {
                    "stack": str(self._dialog.stack),
                    "context": str(self._dialog.context),
                }
            }

    def update_concepts_by_backend(self, d_concepts):
        concepts = [Concept(key, value) for key, value in d_concepts.iteritems()]
        self._dialog.update_by_remote(concepts)
        log.info(self._dialog.context)
        return {
            "code": 0,
            "context": str(self._dialog.context)
        }

    def process_concepts(self, d_concepts):
        concepts = [Concept(key, value) for key, value in d_concepts.iteritems()]
        self._dialog.process_concepts(concepts)

    def process_event(self, event_id):
        pass

    def process_confirm(self, sid, d_confirm):
        return self._dialog.process_confirm(sid, d_confirm)

    @classmethod
    def get_robot(self, robotid, domain_id):
        robot = DMRobot.robots_pool.get(robotid, None)
        if robot:
            return robot
        robot = DMRobot(robotid, domain_id)
        DMRobot.robots_pool[robotid] = robot
        return robot

    @classmethod
    def reset_robot(self, robotid, domain_id):
        robot = DMRobot(robotid, domain_id)
        robot.nlu.reset_robot()
        DMRobot.robots_pool[robotid] = robot
        return True

    def get_context(self):
        return self._dialog.get_candicate_units()
