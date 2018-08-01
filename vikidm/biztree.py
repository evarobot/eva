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
    """ Dialog configure tree.

    We can print tree through `to_json` function, with `with_data` argument
    setting to `True` or `False`. Alternative, We can call `show` function to
    show the tree topology.

    """
    TAG_ROOT = "root"

    def __init__(self):
        super(BizTree, self).__init__()

    def add_subtree_from_json(self, json_subtree, parent, dm):
        """ Add a subtree to parent node.

        Parameters
        ----------
        json_subtree : json, json tree data
        parent: treelib.Node

        """
        d_tree = json.loads(json_subtree)
        self._parse_node(d_tree, parent, dm)

    def init_from_json(self, json_tree, dm):
        """ Constructing a biz tree with json data.

        Each tree node is instance of some subtype of `BizUnit`

        Parameters
        ----------
        json_tree : json, json tree data

        """

        self.add_subtree_from_json(json_tree, None, dm)

        def visit_tree(unit):
            for child in unit.children:
                visit_tree(child)
        visit_tree(self.get_node(self.root))
        self.get_node(self.root).tag = BizTree.TAG_ROOT

    def _parse_node(self, dict_node, parent, dm):
        data = dict_node['data']
        tag = dict_node['data']['tag']
        if data["type"] in [Agency.TYPE_MIX, Agency.TYPE_TARGET,
                            Agency.TYPE_CLUSTER]:
            tr_node = Agency.get_agency(dm, tag, data)
            self.add_node(tr_node, parent)
            for child in dict_node['children']:
                self._parse_node(child, tr_node, dm)
        else:
            tr_node = Agent.get_agent(dm, tag, data)
            self.add_node(tr_node, parent)
        tr_node.parent = parent

    def __repr__(self):
        self.show()
        detail = pprint.pformat(json.loads(self.to_json(with_data=True)))
        return "--------------------------\n{0}".format(detail)
