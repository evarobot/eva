#!/usr/bin/env python
# encoding: utf-8

import os
from pprint import pprint

from vikidm.biztree import BizTree
from vikidm.util import PROJECT_DIR

data_path = os.path.join(PROJECT_DIR, "tests", "data")


def check_biz_tree(tree):
    assert(len(tree.children('root')) == 1)
    assert(len(tree.children('biz12')) == 2)
    # pprint(tree.to_dict(with_data=True))
    # tree.show()
    # print(tree.get_node('nike'))


def test_create_tree_from_json():
    tree = BizTree()
    tree.add_subtree_from_json_file(os.path.join(data_path, 'biz_simulate_data/biz_12.json'))
    check_biz_tree(tree)


if __name__ == '__main__':
    test_create_tree_from_json()
