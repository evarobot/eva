#!/usr/bin/env python
# encoding: utf-8

import json
import treelib
from copy import deepcopy

from vikicommon.util import escape_unicode
from vikidm.util import object_to_dict


class Concept(object):
    """
    """
    def __init__(self, key, value=None):
        self.key = key
        self.value = value
        self.life_type = None

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class BizUnit(treelib.Node):
    def __init__(self, tag, data):
        super(BizUnit, self).__init__(tag, tag, data=data)


class Agency(BizUnit):
    def __init__(self, tag, data):
        super(Agency, self).__init__(tag, data)

    def __str__(self):
        return self.tag.encode('utf8')


class Agent(BizUnit):
    def __init__(self, tag, data):
        data = {
            'subject': data['subject'],
            'scope': data['scope'],
            'event_id': data['event_id'],
            'timeout': float(data['timeout']),
            'trigger_concepts': list(self._deserialize_trigger_concepts(data)),
            'target_concepts': list(self._deserialize_target_concepts(data))
        }
        super(Agent, self).__init__(tag, data)

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
    def trigger_concepts(self):
        return self.data['trigger_concepts']

    @trigger_concepts.setter
    def trigger_concepts(self,  value):
        self.data['trigger_concepts'] = value

    @property
    def target_concepts(self):
        return self.data['target_concepts']

    @target_concepts.setter
    def target_concepts(self,  value):
        self.data['target_concepts'] = value

    def _deserialize_trigger_concepts(self, data):
        for kv in data['trigger_concepts']:
            key, value = tuple(kv.split('='))
            yield Concept(key, value)

    def _deserialize_target_concepts(self, data):
        for key in data['target_concepts']:
            yield Concept(key)

    def __str__(self):
        data = deepcopy(self.data)
        data['trigger_concepts'] = ["%s=%s" % (c.key, c.value) for c in self.trigger_concepts]
        data['target_concepts'] = [c.key for c in self.data['target_concepts']]
        return json.dumps(escape_unicode(data))


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
