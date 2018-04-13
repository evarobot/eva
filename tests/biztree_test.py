#!/usr/bin/env python
# encoding: utf-8

import os
import pprint
import logging

from vikidm.biztree import BizTree
from vikidm.util import PROJECT_DIR

from vikidm.config import ConfigLog
from vikicommon.log import init_logger
init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)

data_path = os.path.join(PROJECT_DIR, "tests", "data")


def check_biz_tree(tree):
    assert(len(tree.children('root')) == 1)
    assert(len(tree.children('where.query')) == 2)
    assert(tree.get_node('zhou_hei_ya').target_concepts[0] == "Concept(location=None)")
    assert(tree.get_node('zhou_hei_ya').trigger_concepts[0] in ["Concept(intent=where.query)"])


def test_create_tree_from_json():
    tree = BizTree()
    tree.add_subtree_from_json_file(os.path.join(data_path, 'biz_simulate_data/biz_unit_test.json'))
    check_biz_tree(tree)
    log.info(pprint.pformat(tree.to_dict(with_data=True)))
    # tree.show()
    # print(tree.get_node('nike'))
