#!/usr/bin/env python
# encoding: utf-8
import os
import json
import logging
import time
import mock

from vikicommon.log import init_logger

from vikidm.util import PROJECT_DIR, cms_rpc
from vikidm.dm import DialogEngine, Stack
from vikidm.context import Concept
from vikidm.biztree import Agent
from vikidm.config import ConfigLog

data_path = os.path.join(PROJECT_DIR, "tests", "data")

init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)


def check_biz_tree(tree):
    assert(len(tree.children('root')) == 1)
    assert(len(tree.children('where.query')) == 2)
    assert(tree.get_node('zhou_hei_ya').trigger_concepts[0] in ["Concept(intent=where.query)"])


def test_stack():
    log.info("test_stack")
    stack = Stack()
    stack.push(1)
    stack.push(2)
    stack.push(3)
    assert(stack.top() == 3)
    assert(stack.pop() == 3)
    assert(stack.top() == 2)


def mock_cms_rpc(paths):
    d_subtrees = []
    for fpath in paths:
        with open(fpath, 'r') as file_obj:
            d_subtrees.append(json.load(file_obj))
    root = {
        "data": {
            "id": "root",
            "tag": "root",
            "entrance": False,
            "event_id": "root",
            "subject": "",
            "scope": "",
            "timeout": "5",
            "type": "TYPE_ROOT"
        },
        "children": []
    }
    root["children"] = d_subtrees
    cms_rpc.get_json_biztree = mock.Mock(return_value=json.dumps(root))


def test_get_triggered_bizunits():
    """
    Test trigger a simple Agent;
    Test trigger entrance_agent of Agency;
    TODO: Test trigger None entrance_agent of Agency;
    """
    dm = DialogEngine()
    fpath = os.path.join(data_path, 'biz_simulate_data/biz_unit_test.json')
    fpath2 = os.path.join(data_path, 'biz_simulate_data/biz_01.json')
    fpath3 = os.path.join(data_path, 'biz_simulate_data/biz_01_failed.json')
    mock_cms_rpc([fpath, fpath2, fpath3])
    dm.init_from_db("mock_domain_id")
    concepts = [
        Concept("intent", "where.query"),
        Concept("location", "nike")
    ]
    dm._update_concepts(concepts)
    for bizunit in dm._get_triggered_bizunits():
        assert(bizunit.tag == 'where.query')

    concepts = [
        Concept("intent", "name.query"),
    ]
    dm._update_concepts(concepts)
    for bizunit in dm._get_triggered_bizunits():
        assert(bizunit.tag == 'name.query')



class TestMixAgency(object):

    def _construct_dm(self):
        fpath1 = os.path.join(data_path, 'biz_simulate_data/biz_mix_travel.json')
        fpath2 = os.path.join(data_path, 'biz_simulate_data/biz_mix_home.json')
        fpath3 = os.path.join(data_path, 'biz_simulate_data/biz_chat.json')
        dm = DialogEngine()
        dm.debug_timeunit = 0.2
        mock_cms_rpc([fpath1, fpath2, fpath3])
        dm.init_from_db("mock_domain_id")
        return dm

    def test_weather(self):
        dm = self._construct_dm()
        import pdb
        pdb.set_trace()



if __name__ == '__main__':
    #test_stack()
    #test_init_biz_from_json_file()
    #test_get_triggered_bizunits()
    #test_process_confirm()
    #tengine = TestEngine()
    #tengine.test_engine()
    tc = TestConceptsConfirm()
    tc.test_process_confirm_case_agent_timeout()
