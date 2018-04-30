#!/usr/bin/env python
# encoding: utf-8
import logging
from vikidm.dm import DialogEngine
from vikidm.context import Concept
from vikidm.util import nlu_robot
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
        log.info("CREATE ROBOT: [{0}] of domain [{1}]".format(robot_id, self.domain_name))

    def process_question(self, sid, question):
        # if rpc, pass robot id
        ret = nlu_robot.predict(self, self.domain_id, question)
        if ret["intent"] is None:
            return {
                "code": 0,
                "sid": "",
                "event_id": None,
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
            event_id = self._dialog.process_concepts(sid, concepts)
            return {
                "code": 0,
                "sid": "",
                "event_id": event_id,
                "action": {},
                "nlu": {
                    "intent": ret["intent"],
                    "slots": ret["slots"]
                }
            }

    def process_concepts(self, d_concepts):
        concepts = [Concept(key, value) for key, value in d_concepts.iteritems()]
        self._dialog.process_concepts(concepts)

    def process_event(self, event_id):
        pass

    def process_confirm(self, d_confirm):
        pass

    @classmethod
    def get_robot(self, robotid, domain_id):
        robot = DMRobot.robots_pool.get(robotid, None)
        if robot:
            return robot
        robot = DMRobot(robotid, domain_id)
        DMRobot.robots_pool[robotid] = robot
        return robot

    def get_context(self):
        return self._dialog.get_candicate_units()
