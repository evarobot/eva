#!/usr/bin/env python
# encoding: utf-8
import copy
import os
import json
import logging
import pprint
import pytest
import time

from vikicommon.timer import TimerThread
from vikicommon.log import init_logger

from vikidm.util import PROJECT_DIR
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
    assert(tree.get_node('zhou_hei_ya').target_concepts[0] == "Concept(location=None)")
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


def test_init_biz_from_json_file():
    """
    Test load json file;
    Test `Context` and `Stack` initialization.
    """
    log.info("test_init_biz_from_json_file")
    dm = DialogEngine()
    fpath = os.path.join(data_path, 'biz_simulate_data/biz_unit_test.json')
    dm.init_from_json_files([fpath])
    # log.info("\n%s" % pprint.pformat(dm._biz_tree.to_dict(with_data=True)))
    check_biz_tree(dm._biz_tree)
    concepts = dm._context._all_concepts.values()
    assert(str(concepts[0]) == "Concept(intent=None)")
    assert(str(concepts[1]) == "Concept(location=None)")
    assert(len(dm._stack) == 1)
    assert(dm._stack.top().tag == 'root')
    # make sure deep copy
    for bizunit in dm._biz_tree.all_nodes_itr():
        if isinstance(bizunit, Agent):
            for concept in bizunit.trigger_concepts:
                assert(concept.value is not None)
    for concept in dm._context._all_concepts.values():
        assert(concept.value is None)
    # log.info("Tree:")
    # dm._biz_tree.show()
    # log.info("\n%s" % dm._context)
    # log.info("\n%s" % dm._stack)


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
    dm.init_from_json_files([fpath, fpath2, fpath3])
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


def test_mark_completed_bizunits():
    """
     TODO
    """
    pass


class TestConceptsConfirm(object):
    """"""

    def _construct_dm(self):
        fpath1 = os.path.join(data_path, 'biz_simulate_data/biz_unit_test.json')
        fpath2 = os.path.join(data_path, 'biz_simulate_data/biz_01.json')
        fpath3 = os.path.join(data_path, 'biz_simulate_data/biz_chat.json')
        dm = DialogEngine()
        dm.init_from_json_files([fpath1, fpath2, fpath3])
        #pprint.pprint(dm._biz_tree.to_dict(with_data=True))
        #dm._biz_tree.show()
        # log.info('\n%s' % pprint.pformat(dm._biz_tree.to_dict(with_data=True)))
        # log.info('\n%s' % str(dm._stack))
        # test name.query
        return dm

    @pytest.mark.dependency()
    def test_process_concepts_case_agent(self):
        concepts = [
            Concept('intent', 'name.query')
        ]
        dm = self._construct_dm()
        dm.process_concepts("sid001", concepts)
        assert(len(dm._stack) == 2)
        assert(dm._stack.top().tag == 'name.query')
        assert(dm._context['intent'].value == 'name.query')
        assert(dm._session.valid_session("sid001"))
        assert(dm.debug_loop == 1)
        return dm

    @pytest.mark.dependency()
    def test_process_concepts_case_cluster(self):
        concepts = [
            Concept("intent", "where.query"),
            Concept("location", "nike")
        ]
        dm = self._construct_dm()
        dm.process_concepts("sid002", concepts)
        assert(len(dm._stack) == 3)
        assert(dm._stack.top().tag == 'nike')
        assert(dm._stack.item(1).tag == 'where.query')
        assert(dm._context['intent'].value == 'where.query')
        assert(dm._context['location'].value == 'nike')
        assert(dm._session.valid_session("sid002"))
        assert(dm.debug_loop == 2)
        return dm

    def test_wait_action_agent_switch_to_chat(self):
        dm = self.test_process_concepts_case_agent()
        concepts = [
            Concept("intent", "casual_talk"),
        ]
        dm.process_concepts("sid002", concepts)
        confirm_data = {
            'sid': 'sid002',
            'code': 0,
            'message': ''
        }
        dm.process_confirm(confirm_data)
        assert(len(dm._stack) == 1)
        assert(dm._context['intent'].value == None)

    # agent
    def test_process_confirm_case_agent_timeout(self):
        concepts = [
            Concept('intent', 'name.query')
        ]
        dm = self._construct_dm()
        dm.debug_timeunit = 0.2
        dm.process_concepts("sid001", concepts)
        time.sleep(6 * 0.2)

    def test_process_confirm_case_agent_sucess_confirm(self):
        dm = self.test_process_concepts_case_agent()
        confirm_data = {
            'sid': 'sid001',
            'code': 0,
            'message': ''
        }
        dm.process_confirm(confirm_data)
        assert(dm.debug_loop == 2)
        assert(len(dm._stack) == 1)
        assert(dm._stack.top().tag == 'root')

    def test_process_confirm_case_agent_failed_confirm(self):
        dm = self.test_process_concepts_case_agent()
        confirm_data = {
            'sid': 'sid001',
            'code': -1,
            'message': 'action failed'
        }
        dm.process_confirm(confirm_data)
        assert(dm.debug_loop == 5)
        assert(len(dm._stack) == 1)
        assert(dm._session._sid is None)
        assert(dm._context['intent'].value is None)

    def test_process_confirm_case_agent_ignore_old_session(self):
        dm = self.test_process_concepts_case_agent()
        # ignore old session
        confirm_data = {
            'sid': 'sid000',
            'code': 0,
            'message': ''
        }
        dm.process_confirm(confirm_data)
        assert(dm.debug_loop == 1)
        assert(len(dm._stack) == 2)
        assert(dm._stack.top().tag == 'name.query')

    # cluster
    def test_process_confirm_case_cluster_success_exit(self):
        dm = self.test_process_concepts_case_cluster()
        confirm_data = {
            'sid': 'sid002',
            'code': 0,
            'message': 'action failed'
        }
        dm.process_confirm(confirm_data)
        assert(dm.debug_loop == 5)
        assert(len(dm._stack) == 1)
        assert(dm._session._sid is None)
        assert(dm._context['intent'].value is None)
        assert(dm._context['location'].value is None)

    def test_process_confirm_case_agency_failed(self):
        dm = self.test_process_concepts_case_cluster()
        confirm_data = {
            'sid': 'sid002',
            'code': -1,
            'message': 'action failed'
        }
        dm.process_confirm(confirm_data)
        assert(len(dm._stack) == 1)
        assert(dm._session._sid is None)
        assert(dm._context['intent'].value is None)
        assert(dm._context['location'].value is None)

    # sequence
    # target




if __name__ == '__main__':
    #test_stack()
    #test_init_biz_from_json_file()
    #test_get_triggered_bizunits()
    #test_process_confirm()
    #tengine = TestEngine()
    #tengine.test_engine()
    tc = TestConceptsConfirm()
    tc.test_process_confirm_case_agent_timeout()
