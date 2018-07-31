#!/usr/bin/env python
# encoding: utf-8
import logging
import json
import pprint
import treelib

from vikidm.units.agent import Agent
from vikidm.units.agency import Agency
log = logging.getLogger(__name__)


class BizTree(treelib.Tree):
    """ 业务配置树
    We can print tree through `to_json` function, with `with_data` argument
    setting to `True` or `False`. Alternative, We can call `show` function to
    show the tree topology.
    """
    def __init__(self, dm):
        super(BizTree, self).__init__()
        self._dm = dm

    def add_subtree_from_json(self, json_subtree, parent):
        d_tree = json.loads(json_subtree)
        self._parse_node(d_tree, parent)

    def init_from_json(self, json_tree):
        self.add_subtree_from_json(json_tree, parent=None)

        def visit_tree(unit):
            for child in unit.children:
                visit_tree(child)
        visit_tree(self.get_node(self.root))
        self.get_node(self.root).tag = "root"

    def _parse_node(self, dict_node, parent):
        data = dict_node['data']
        tag = dict_node['data']['tag']
        # if dict_node['children']:
        if data["type"] in [Agency.TYPE_MIX, Agency.TYPE_TARGET,
                            Agency.TYPE_CLUSTER]:
            tr_node = Agency.get_agency(self._dm, tag, data)
            self.add_node(tr_node, parent)
            for child in dict_node['children']:
                self._parse_node(child, tr_node)
        else:
            tr_node = Agent.get_agent(self._dm, tag, data)
            self.add_node(tr_node, parent)
        tr_node.parent = parent

    def __repr__(self):
        self.show()
        detail = pprint.pformat(json.loads(self.to_json(with_data=True)))
        return "--------------------------\n{0}".format(detail)
