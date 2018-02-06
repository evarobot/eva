#!/usr/bin/env python
# encoding: utf-8

import json
import treelib
from copy import deepcopy

from vikicommon.util import escape_unicode
from vikicommon.log import gen_log as log
from vikidm.context import Concept


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

    STATUS_CONTINUE = "STATUS_CONTINUE"
    STATUS_DELAY_EXIST = "STATUS_DELAY_EXIST"
    def __init__(self, tag, data):
        super(BizUnit, self).__init__(tag, tag, data=data)
        self.status = self.STATUS_TREEWAIT

    def execute(self):
        raise NotImplementedError


class Agency(BizUnit):
    def __init__(self, tag, data):
        super(Agency, self).__init__(tag, data)

    def __str__(self):
        return self.tag.encode('utf8')

    def execute(self):
        if self.tag == 'root':
            return self.STATUS_STACKWAIT, None
        log.info("execute {0}".format(self.tag))


class Agent(BizUnit):
    TYPE_INPUT = "TYPE_INPUT"
    TYPE_INFORM = "TYPE_INFORM"
    def __init__(self, tag, data):
        data = {
            'subject': data['subject'],
            'scope': data['scope'],
            'event_id': data['event_id'],
            'timeout': data['timeout'],
            'agency_entrance': data['agency_entrance'],
            'trigger_concepts': data['trigger_concepts'],  # 用于tree.to_json(), 方便调试。
            'state': BizUnit.STATUS_TREEWAIT,
            'target_concepts': data['target_concepts']
        }
        self._trigger_concepts = list(self._deserialize_trigger_concepts(data))
        self._target_concepts = list(self._deserialize_target_concepts(data))
        self.type_ = Agent.TYPE_INPUT if self._target_concepts else Agent.TYPE_INFORM
        self.target_completed = False
        super(Agent, self).__init__(tag, data)

    def execute(self):
        """
        """
        if self.target_completed:
            self.status = BizUnit.STATUS_TARGET_COMPLETED
            return self.status, None

        if self.status == BizUnit.STATUS_TRIGGERED:
            self.status = BizUnit.STATUS_WAIT_ACTION_CONFIRM
            return self.status, self.event_id

    @property
    def subject(self):
        return self.data['subject']

    @subject.setter
    def subject(self,  value):
        self.data['subject'] = value

    @property
    def scope(self):
        return self.data['scope']

    @scope.setter
    def scope(self,  value):
        self.data['scope'] = value

    @property
    def event_id(self):
        return self.data['event_id']

    @event_id.setter
    def event_id(self,  value):
        self.data['event_id'] = value

    @property
    def timeout(self):
        return self.data['timeout']

    @timeout.setter
    def timeout(self,  value):
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
    def state(self):
        return self.data['state']

    def _deserialize_trigger_concepts(self, data):
        for kv in data['trigger_concepts']:
            key, value = tuple(kv.split('='))
            yield Concept(key, value)

    def _deserialize_target_concepts(self, data):
        for key in data['target_concepts']:
            yield Concept(key)

    def __str__(self):
        return json.dumps(escape_unicode(self.data))


class BizTree(treelib.Tree):
    """ 业务配置树 """
    def __init__(self):
        super(BizTree, self).__init__()
        root = Agency('root', {})
        self.add_node(root, None)

    def add_subtree_from_json(self, json_data, identifier='root'):
        def parse_json(dict_node, parent):
            data = dict_node['data']
            tag = dict_node['data']['tag']
            if dict_node['children']:
                tr_node = Agency(tag, data)
                self.add_node(tr_node, parent)
                for child in dict_node['children']:
                    parse_json(child, tr_node)
            else:
                tr_node = Agent(tag, data)
                self.add_node(tr_node, parent)

        parse_json(json_data, identifier)

    def add_subtree_from_json_file(self, fpath):
        with open(fpath, "r") as file_obj:
            json_data = json.load(file_obj)
            self.add_subtree_from_json(json_data)
