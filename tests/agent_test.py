#!/usr/bin/env python
# encoding: utf-8
import os
import time

from vikidm.dm import DialogEngine, Stack
from vikidm.context import Concept
from vikidm.biztree import Agent
from .prepare import data_path, mock_cms_rpc, construct_dm, INPUT_TIMEOUT


def test_stack():
    stack = Stack()
    stack.push(1)
    stack.push(2)
    stack.push(3)
    assert(stack.top() == 3)
    assert(stack.pop() == 3)
    assert(stack.top() == 2)


def test_init_biz_from_db():
    """
    Test load json file;
    Test `Context` and `Stack` initialization.
    """
    dm = DialogEngine()
    fpath = os.path.join(data_path, 'biz_simulate_data/biz_unit_test.json')
    mock_cms_rpc([fpath])
    dm.init_from_db("mock_domain_id")

    # tree testing
    assert(len(dm.biz_tree.children('root')) == 1)
    assert(len(dm.biz_tree.children('where.query')) == 2)
    assert(dm.biz_tree.get_node('zhou_hei_ya').trigger_concepts[0] in
           ["Concept(intent=where.query)"])
    for bizunit in dm.biz_tree.all_nodes_itr():
        if isinstance(bizunit, Agent):
            for concept in bizunit.trigger_concepts:
                assert(concept.value is not None)

    # context testing
    concepts = dm.context._all_concepts.values()
    assert(str(concepts[0]) == "Concept(intent=None)")
    assert(str(concepts[1]) == "Concept(location=None)")
    assert(len(dm.stack) == 1)
    assert(dm.stack.top().tag == 'root')
    for concept in dm.context._all_concepts.values():
        assert(concept.value is None)


class TestAgentCase(object):
    '''
    root
    ├── casual_talk
    ├── name.query
    ├── weather.query
    │   ├── city
    │   ├── date
    │   ├── default@weather.query
    │   └── result
    └── where.query
        ├── nike
        └── zhou_hei_ya
    '''

    def test_name_input(self):
        dm = construct_dm()
        dm.process_concepts("sid001", [
            Concept('intent', 'name.query')
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                name.query(STATUS_WAIT_ACTION_CONFIRM)''')
        assert(str(dm.context) == '''
            Context:
                Concept(city=None)
                Concept(date=None)
                Concept(intent=name.query)
                Concept(location=None)'''
        )
        assert(dm._session.valid_session("sid001"))
        assert(dm.debug_loop == 1)
        time.sleep(INPUT_TIMEOUT * dm.debug_timeunit)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)''')

    def test_success_confirm(self):
        dm = construct_dm()
        dm.process_concepts("sid001", [
            Concept('intent', 'name.query')
        ])
        dm.process_confirm('sid001', {
            'code': 0,
            'message': ''
        })
        assert(dm.debug_loop == 1)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)''')

    def test_failed_confirm(self):
        dm = construct_dm()
        dm.process_concepts("sid001", [
            Concept('intent', 'name.query')
        ])
        dm.process_confirm('sid001', {
            'code': -1,
            'message': ''
        })
        assert(dm.debug_loop == 5)
        assert(dm._session._sid is None)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)''')
        assert(dm.context['intent'].value is None)