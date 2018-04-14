#!/usr/bin/env python
# encoding: utf-8

import json
import treelib
import logging
import pprint

from vikicommon.util import escape_unicode
from vikidm.context import Concept
log = logging.getLogger(__name__)


class BizUnit(treelib.Node):
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

    def __init__(self, identifier, tag, data):
        super(BizUnit, self).__init__(tag, identifier, data=data)
        self.state = self.STATUS_TREEWAIT

    def execute(self):
        raise NotImplementedError


class AbnormalHandler(BizUnit):
    ABNORMAL_TIMEOUT = "ABNORMAL_TIMEOUT"
    ABNORMAL_FAILED = "ABNORMAL_FAILED"

    def __init__(self, handler_agent, type_):
        self.handler = handler_agent
        self.tag = "AbnormalHandler"
        self.identifier = "AbnormalHandler"
        self.state = BizUnit.STATUS_TRIGGERED
        self.parent = None
        self.data = {
            'trigger_concepts': []
        }
        self.target_concepts = []
        self.trigger_concepts = []
        self._handler_finished = False
        self._type = type_

    def is_root(self):
        return False

    def execute(self, stack, tree):
        if self._handler_finished:
            self._mark_abnormal_unit(stack, tree, stack._items[-2])
            self.state = BizUnit.STATUS_ACTION_COMPLETED
            return self.state

        # push handler unit
        self.handler.state = Agent.STATUS_TRIGGERED
        stack.push(self.handler)
        self.state = BizUnit.STATUS_STACKWAIT
        self._handler_finished = True
        return self.state

    def _mark_abnormal_unit(self, stack, tree, abnormal_unit):
        parent = tree.parent(abnormal_unit.identifier)

        def is_abnormal(bizunit):
            is_agency_parent = bizunit == parent and not parent.is_root()
            if bizunit == abnormal_unit or is_agency_parent:
                return True
            return False

        for unit in reversed(stack._items[:-1]):
            if is_abnormal(unit):
                unit.state = BizUnit.STATUS_ABNORMAL


class Agency(BizUnit):
    TYPE_CLUSTER = "TYPE_CLUSTER"  # no delay exit
    TYPE_TARGET = "TYPE_TARGET"
    TYPE_SEQUENCE = "TYPE_SEQUENCE"

    def __init__(self, tag, data):
        super(Agency, self).__init__(data["event_id"], tag, data)
        self.trigger_child = None
        self._type = data['type']
        self._handler_finished = False

    def __str__(self):
        return self.tag.encode('utf8')

    def execute(self, stack):
        if self.is_root():
            return self.STATUS_STACKWAIT
        elif self._type == Agency.TYPE_CLUSTER:
            if self._handler_finished:
                self.state = BizUnit.STATUS_AGENCY_COMPLETED
                return
            self.trigger_child.state = Agent.STATUS_TRIGGERED
            stack.push(self.trigger_child)
            self.trigger_child = None
            self.state = BizUnit.STATUS_STACKWAIT
            self._handler_finished = True


class Agent(BizUnit):
    TYPE_INPUT = "TYPE_INPUT"
    TYPE_INFORM = "TYPE_INFORM"

    def __init__(self, tag, data):
        data = {   # 用于tree.to_json(), 方便调试。
            'subject': data['subject'],
            'scope': data['scope'],
            'event_id': data['event_id'],
            'timeout': float(data['timeout']),
            'agency_entrance': data['agency_entrance'],
            'trigger_concepts': data['trigger_concepts'],
            'state': BizUnit.STATUS_TREEWAIT,
            'target_concepts': data['target_concepts']
        }

        self._trigger_concepts = list(self._deserialize_trigger_concepts(data))
        self._target_concepts = list(self._deserialize_target_concepts(data))
        self.type_ = Agent.TYPE_INPUT if self._target_concepts else Agent.TYPE_INFORM
        self.target_completed = False
        super(Agent, self).__init__(data["event_id"], tag, data)

    def execute(self):
        """
        """
        if self.target_completed:
            self.state = BizUnit.STATUS_TARGET_COMPLETED
            return None

        if self.state == BizUnit.STATUS_TRIGGERED:
            log.debug("WAIT_CONFIRM Agent(%s)" % self.tag)
            self.state = BizUnit.STATUS_WAIT_ACTION_CONFIRM
            return self.event_id

    @property
    def subject(self):
        return self.data['subject']

    @subject.setter
    def subject(self, value):
        self.data['subject'] = value

    @property
    def scope(self):
        return self.data['scope']

    @scope.setter
    def scope(self, value):
        self.data['scope'] = value

    @property
    def event_id(self):
        return self.data['event_id']

    @event_id.setter
    def event_id(self, value):
        self.data['event_id'] = value

    @property
    def timeout(self):
        return self.data['timeout']

    @timeout.setter
    def timeout(self, value):
        self.data['timeout'] = value

    @property
    def agency_entrance(self):
        return self.data['agency_entrance']

    @property
    def trigger_concepts(self):
        return self._trigger_concepts

    @property
    def target_concepts(self):
        return self._target_concepts

    @property
    def state(self):
        return self.data['state']

    @state.setter
    def state(self, value):
        self.data['state'] = value

    def _deserialize_trigger_concepts(self, data):
        for kv in data['trigger_concepts']:
            split_index = kv.find('=')
            key = kv[0: split_index]
            value = kv[split_index + 1:]
            yield Concept(key, value)

    def _deserialize_target_concepts(self, data):
        for key in data['target_concepts']:
            yield Concept(key)

    def __str__(self):
        return json.dumps(escape_unicode(self.data))


class DefaultFailedAgent(Agent):

    def __init__(self, agent):
        data = {
            'subject': '',
            'scope': '',
            'event_id': 'FAILED|' + agent.event_id,
            'tag': 'FAILED|' + agent.event_id,
            'timeout': 0,
            'agency_entrance': False,
            'trigger_concepts': {},
            'state': '',
            'target_concepts': [],
        }
        self._trigger_concepts = []
        self._target_concepts = []
        super(Agent, self).__init__(data["event_id"], data["event_id"], data)

    def execute(self):
        self.state = BizUnit.STATUS_WAIT_ACTION_CONFIRM
        return self.event_id

    @property
    def trigger_concepts(self):
        return self._trigger_concepts

    @property
    def target_concepts(self):
        return self._target_concepts


class BizTree(treelib.Tree):
    """ 业务配置树 """
    def __init__(self):
        super(BizTree, self).__init__()

    def add_subtree_from_json(self, json_subtree, parent):
        d_tree = json.loads(json_subtree)
        self._parse_node(d_tree, parent)

    def init_from_json(self, json_tree):
        self.add_subtree_from_json(json_tree, parent=None)

    def _parse_node(self, dict_node, parent):
        data = dict_node['data']
        tag = dict_node['data']['tag']
        if dict_node['children']:
            tr_node = Agency(tag, data)
            self.add_node(tr_node, parent)
            for child in dict_node['children']:
                self._parse_node(child, tr_node)
        else:
            tr_node = Agent(tag, data)
            self.add_node(tr_node, parent)

    def __repr__(self):
        self.show()
        detail = pprint.pformat(json.loads(self.to_json(with_data=True)))
        return "--------------------------\n{0}".format(detail)
