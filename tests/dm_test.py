#!/usr/bin/env python
# encoding: utf-8
import os
import json
import logging
import pytest
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
            "agency_entrance": False,
            "event_id": "root",
            "subject": "主题",
            "scope": "可见域",
            "timeout": "5",
            "type": "TYPE_ROOT"
        },
        "children": []
    }
    root["children"] = d_subtrees
    cms_rpc.get_json_biztree = mock.Mock(return_value=json.dumps(root))


def construct_dm():
    fpath1 = os.path.join(data_path, 'biz_simulate_data/biz_unit_test.json')
    fpath2 = os.path.join(data_path, 'biz_simulate_data/biz_01.json')
    fpath3 = os.path.join(data_path, 'biz_simulate_data/biz_chat.json')
    fpath4 = os.path.join(data_path, 'biz_simulate_data/biz_weather.json')
    dm = DialogEngine()
    mock_cms_rpc([fpath1, fpath2, fpath3, fpath4])
    dm.init_from_db("mock_domain_id")
    return dm


def test_init_biz_from_db():
    """
    Test load json file;
    Test `Context` and `Stack` initialization.
    """
    log.info("test_init_biz_from_json_file")
    dm = DialogEngine()

    fpath = os.path.join(data_path, 'biz_simulate_data/biz_unit_test.json')
    mock_cms_rpc([fpath])
    dm.init_from_db("mock_domain_id")
    # log.info("\n%s" % pprint.pformat(dm.biz_tree.to_dict(with_data=True)))
    check_biz_tree(dm.biz_tree)
    concepts = dm.context._all_concepts.values()
    assert(str(concepts[0]) == "Concept(intent=None)")
    assert(str(concepts[1]) == "Concept(location=None)")
    assert(len(dm.stack) == 1)
    assert(dm.stack.top().tag == 'root')
    # make sure deep copy
    for bizunit in dm.biz_tree.all_nodes_itr():
        if isinstance(bizunit, Agent):
            for concept in bizunit.trigger_concepts:
                assert(concept.value is not None)
    for concept in dm.context._all_concepts.values():
        assert(concept.value is None)
    # log.info("Tree:")
    # dm.biz_tree.show()
    # log.info("\n%s" % dm.context)
    # log.info("\n%s" % dm.stack)


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


def test_mark_completed_bizunits():
    """
     TODO
    """
    pass


class TestAgentCase(object):

    def test_name_input(self):
        dm = self.name_input()
        assert(len(dm.stack) == 2)
        assert(dm.stack.top().tag == 'name.query')
        assert(dm.context['intent'].value == 'name.query')
        assert(dm._session.valid_session("sid001"))
        assert(dm.debug_loop == 1)
        return dm

    @classmethod
    def name_input(self):
        concepts = [
            Concept('intent', 'name.query')
        ]
        dm = construct_dm()
        dm.process_concepts("sid001", concepts)
        return dm

    def test_process_confirm_case_agent_sucess_confirm(self):
        dm = self.name_input()
        confirm_data = {
            'sid': 'sid001',
            'code': 0,
            'message': ''
        }
        dm.process_confirm(confirm_data)
        assert(dm.debug_loop == 2)
        assert(len(dm.stack) == 1)
        assert(dm.stack.top().tag == 'root')

    def test_process_confirm_case_agent_failed_confirm(self):
        dm = self.name_input()
        confirm_data = {
            'sid': 'sid001',
            'code': -1,
            'message': 'action failed'
        }
        dm.process_confirm(confirm_data)
        assert(dm.debug_loop == 6)
        assert(len(dm.stack) == 1)
        assert(dm._session._sid is None)
        assert(dm.context['intent'].value is None)



class TestClusterAgencyCase(object):

    def test_location_input(self):
        dm = self.location_input()
        assert(len(dm.stack) == 3)
        assert(dm.stack.top().tag == 'nike')
        assert(dm.stack.item(1).tag == 'where.query')
        assert(dm.context['intent'].value == 'where.query')
        assert(dm.context['location'].value == 'nike')
        assert(dm._session.valid_session("sid002"))
        assert(dm.debug_loop == 2)

    @classmethod
    def location_input(self):
        concepts = [
            Concept("intent", "where.query"),
            Concept("location", "nike")
        ]
        dm = construct_dm()
        dm.process_concepts("sid002", concepts)
        assert(dm.debug_loop == 2)
        return dm

    def test_process_confirm_case_cluster_success_exit(self):
        dm = self.location_input()
        confirm_data = {
            'sid': 'sid002',
            'code': 0,
            'message': 'action failed'
        }
        dm.process_confirm(confirm_data)
        assert(dm.debug_loop == 5)
        assert(len(dm.stack) == 1)
        assert(dm._session._sid is None)
        assert(dm.context['intent'].value is None)
        assert(dm.context['location'].value is None)

    def test_process_confirm_case_agency_failed(self):
        dm = self.location_input()
        confirm_data = {
            'sid': 'sid002',
            'code': -1,
            'message': 'action failed'
        }
        dm.process_confirm(confirm_data)
        assert(len(dm.stack) == 1)
        assert(dm._session._sid is None)
        assert(dm.context['intent'].value is None)
        assert(dm.context['location'].value is None)
        assert(dm.debug_loop == 8)


class TestTargetAgencyCase(object):

    def test_default_triggered(self):
        dm = self.default_triggered()
        assert(len(dm.stack) == 3)
        assert(dm.stack.top().tag == 'default@weather.query')
        assert(dm.context['intent'].value == 'weather.query')
        assert(dm.debug_loop == 2)


    @classmethod
    def default_triggered(self):
        concepts = [
            Concept("intent", "weather.query")
        ]
        dm = construct_dm()
        dm.debug_timeunit = 0.2
        dm.process_concepts("sid001", concepts)
        assert(dm.debug_loop == 2)
        return dm

    def test_default_result(self):
        dm = self.default_triggered()
        concepts = [
            Concept('intent', 'weather.query'),
            Concept('city', '深圳'),
            Concept('date', '今天')
        ]
        confirm_data = {
            'sid': 'sid001',
            'code': 0,
            'message': ''
        }
        dm.process_confirm(confirm_data)
        dm.process_concepts("sid002", concepts)
        assert(str(dm.stack) == 'Stack[root, weather.query, result]')
        assert(str(dm.context) == '''
        Context:
        Concept(date=今天)
        Concept(city=深圳)
        Concept(intent=weather.query)
        Concept(location=None)''')
        confirm_data = {
            'sid': 'sid002',
            'code': 0,
            'message': ''
        }
        import pdb
        pdb.set_trace()
        dm.process_confirm(confirm_data)
        assert(str(dm.stack) == 'Stack[root, weather.query]')


class TestTiemoutCase(object):
    def test_process_confirm_case_agent_timeout(self):
        concepts = [
            Concept('intent', 'name.query')
        ]
        dm = construct_dm()
        dm.debug_timeunit = 0.2
        dm.process_concepts("sid001", concepts)
        time.sleep(6 * dm.debug_timeunit)
        assert(dm.debug_loop == 6)

    def test_target_default_triggered_timeout(self):
        dm = TestTargetAgencyCase.default_triggered()
        confirm_data = {
            'sid': 'sid001',
            'code': 0,
            'message': ''
        }
        dm.process_confirm(confirm_data)
        assert(len(dm.stack) == 2)
        assert(dm.stack.top().tag == 'weather.query')
        time.sleep(6 * dm.debug_timeunit)
        assert(len(dm.stack) == 1)
        assert(dm.debug_loop == 9)
        assert(dm.context["intent"].value == None)


class TestSessionCase(object):
    def test_process_confirm_case_agent_ignore_old_session(self):
        dm = TestAgentCase.name_input()
        # ignore old session
        confirm_data = {
            'sid': 'sid000',
            'code': 0,
            'message': ''
        }
        dm.process_confirm(confirm_data)
        assert(len(dm.stack) == 2)
        assert(dm.stack.top().tag == 'name.query')
        assert(dm.is_waiting == True)
        time.sleep(6 * dm.debug_timeunit)
        assert(dm.is_waiting == False)
        assert(dm.debug_loop == 6)


    def test_wait_action_agent_switch_to_chat(self):
        dm = TestAgentCase.name_input()
        concepts = [
            Concept("intent", "casual_talk"),
        ]
        assert(dm.is_waiting == True)
        ret = dm.process_concepts("sid002", concepts)
        assert(ret == 'casual_talk')
        confirm_data = {
            'sid': 'sid002',
            'code': 0,
            'message': ''
        }
        ret = dm.process_confirm(confirm_data)
        assert(ret["code"] == 0)
        assert(len(dm.stack) == 1)
        assert(dm.context['intent'].value is None)
        assert(dm.is_waiting == False)
        assert(dm.debug_loop == 4)

    def test_target_agency_wait_switch_to_chat(self):
        dm = TestTargetAgencyCase.default_triggered()
        confirm_data = {
            'sid': 'sid001',
            'code': 0,
            'message': ''
        }
        dm.process_confirm(confirm_data)
        assert(len(dm.stack) == 2)
        assert(dm.stack.top().tag == 'weather.query')
        assert(dm.context['intent'].value == 'weather.query')
        # state: Agency Waiting

        # switch after 2 unit time passed
        time.sleep(2 * dm.debug_timeunit)
        concepts = [
            Concept("intent", "casual_talk"),
        ]
        dm.process_concepts("sid002", concepts)
        assert(len(dm.stack) == 3)
        assert(dm.stack.top().tag == 'casual_talk')
        confirm_data = {
            'sid': 'sid002',
            'code': 0,
            'message': ''
        }
        dm.process_confirm(confirm_data)
        # reset timer
        time.sleep(4 * dm.debug_timeunit)
        # before timeout
        assert(len(dm.stack) == 2)
        assert(dm.stack.top().tag == 'weather.query')
        assert(dm.context['intent'].value == 'weather.query')
        # after timeout
        time.sleep(2 * dm.debug_timeunit)
        assert(len(dm.stack) == 1)
        assert(dm.context['intent'].value == None)
        assert(dm.debug_loop == 12)



if __name__ == '__main__':
    #test_stack()
    #test_init_biz_from_json_file()
    #test_get_triggered_bizunits()
    #test_process_confirm()
    #tengine = TestEngine()
    #tengine.test_engine()
    tc = TestConceptsConfirm()
    tc.test_process_confirm_case_agent_timeout()
