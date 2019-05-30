#!/usr/bin/env python
# encoding: utf-8
import logging
import json
import pprint
import treelib

from evadm.units.agent import Agent
from evadm.units.agency import Agency
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

    def add_subtree_from_dict(self, dict_subtree, parent, dm):
        """ Add a subtree to parent node.

        Parameters
        ----------
        dict_subtree : dict,
        parent: treelib.Node

        """
        self._parse_tree(dict_subtree, parent, dm)

    def init_from_dict(self, dict_tree, dm):
        """ Constructing a biz tree with dict data.

        Each tree node is instance of some subtype of `BizUnit`

        Parameters
        ----------
        dict_tree : dict, dict tree data

        """
        self.add_subtree_from_dict(dict_tree, None, dm)
        self.get_node(self.root).tag = BizTree.TAG_ROOT

    def _parse_tree(self, dict_node, parent, dm):
        data = dict_node['data']
        tag = data['tag']
        log.debug("parse node: [%s]" % data['tag'])
        if data["type"] in [Agency.TYPE_MIX, Agency.TYPE_TARGET,
                            Agency.TYPE_CLUSTER]:
            tr_node = Agency.get_agency(dm, tag, data)
            self.add_node(tr_node, parent)
        else:
            tr_node = Agent.get_agent(dm, tag, data)
            self.add_node(tr_node, parent)
        for child in dict_node['children']:
            self._parse_tree(child, tr_node, dm)
        tr_node.parent = parent

    def __repr__(self):
        self.show()
        detail = pprint.pformat(json.loads(self.to_json(with_data=True)))
        return "--------------------------\n{0}".format(detail)
