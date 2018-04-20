#!/usr/bin/env python
# encoding: utf-8
import json
import logging
import treelib
import pprint

from vikidm.units.agent import Agent
from vikidm.units.agency import Agency
log = logging.getLogger(__name__)


class BizTree(treelib.Tree):
    """ 业务配置树 """
    def __init__(self, dm):
        super(BizTree, self).__init__()
        self._dm = dm

    def add_subtree_from_json(self, json_subtree, parent):
        d_tree = json.loads(json_subtree)
        self._parse_node(d_tree, parent)

    def init_from_json(self, json_tree):
        self.add_subtree_from_json(json_tree, parent=None)

    def _parse_node(self, dict_node, parent):
        data = dict_node['data']
        tag = dict_node['data']['tag']
        if dict_node['children']:
            tr_node = Agency.get_agency(self._dm, tag, data)
            self.add_node(tr_node, parent)
            for child in dict_node['children']:
                self._parse_node(child, tr_node)
        else:
            tr_node = Agent.get_agent(self._dm, tag, data)
            self.add_node(tr_node, parent)

    def __repr__(self):
        self.show()
        detail = pprint.pformat(json.loads(self.to_json(with_data=True)))
        return "--------------------------\n{0}".format(detail)
