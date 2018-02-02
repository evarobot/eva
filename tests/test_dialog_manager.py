#!/usr/bin/env python
# encoding: utf-8

import os
import json
from pprint import pprint

from vikidm.util import PROJECT_DIR
from vikidm.dm import DialogEngine
from test_biztree import check_biz_tree
from vikicommon.log import (
    gen_log as log,
    add_tornado_log_handler,
    add_stdout_handler
)


data_path = os.path.join(PROJECT_DIR, "tests", "data")


def load_test_case():
    """
    加载测试案例。
    """
    cases = {}
    path = os.path.join(data_path, 'terminal_simulate_data')
    list_dirs = os.walk(path)
    for path, dirs, files in list_dirs:
        for f in files:
            if f.startswith('case_12'):
                source = os.path.join(path, f)
                with open(source, 'r') as file:
                    biz = json.load(file)
                    cases.update(biz['cases'])
    return cases


def test_case(case, dm):
    """ 测试一个案例。
    """
    pprint(case)
    #dm._biz_tree.show()



def construct_dm():
    dm = DialogEngine()
    fpath = os.path.join(data_path, 'biz_simulate_data/biz_12.json')
    dm.add_biz_from_json_file(fpath)
    check_biz_tree(dm._biz_tree)

    fpath = os.path.join(data_path, 'biz_simulate_data/biz_01.json')
    dm.add_biz_from_json_file(fpath)
    return dm




if __name__ == '__main__':
    add_stdout_handler("INFO")
    # add_tornado_log_handler("./", "INFO")

    cases = load_test_case()
    dm = construct_dm()
    log.info("construct dialog manager")
    test_case(cases['12.1'], dm)
