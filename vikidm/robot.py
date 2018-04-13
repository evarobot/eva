#!/usr/bin/env python
# encoding: utf-8
import logging
from vikidm.dm import DialogEngine
from vikidm.context import Concept

log = logging.getLogger(__name__)


class DMRobot(object):
    robots_pool = {}
    def __init__(self, robotid, domain_name):
        self._domain_name = domain_name
        self._id = robotid
        self._dialog = DialogEngine()
        import pdb
        pdb.set_trace()
        self._dialog.init_from_db(domain_name)

    @property
    def id(self):
        return self._id

    @property
    def domain_name(self):
        return self._domain_name

    def process_question(self, question):
        pass

    def process_concepts(self, d_concepts):
        concepts = [Concept(key, value) for key, value in d_concepts.iteritems()]
        self._dialog.process_concepts(concepts)

    def process_event(self, event_id):
        pass

    def process_confirm(self, d_confirm):
        pass

    @classmethod
    def get_robot(self, robotid, domain_name):
        robot = DMRobot.robots_pool.get(robotid, None)
        if robot:
            return robot
        robot = DMRobot(robotid, domain_name)
        DMRobot.robots_pool[robotid] = robot
        log.info("CREATE ROBOT: [{0}] of domain [{1}]".format(robotid, domain_name))
        return robot
