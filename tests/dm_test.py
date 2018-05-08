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
            "title": "Mix(root)",
            "subject": "",
            "scope": "",
            "timeout": "5",
            "type": "TYPE_MIX"
        },
        "children": []
    }
    root["children"] = d_subtrees
    data = {
        "code": 0,
        "tree": json.dumps(root)
    }
    cms_rpc.get_dm_biztree = mock.Mock(return_value=data)


class TestMixAgency(object):

    def _construct_dm(self):
        fpath1 = os.path.join(data_path, 'biz_simulate_data/biz_mix_travel.json')
        fpath2 = os.path.join(data_path, 'biz_simulate_data/biz_mix_home.json')
        fpath3 = os.path.join(data_path, 'biz_simulate_data/biz_chat.json')
        fpath4 = os.path.join(data_path, 'biz_simulate_data/biz_unit_test.json')
        fpath5 = os.path.join(data_path, 'biz_simulate_data/biz_01.json')
        dm = DialogEngine()
        dm.debug_timeunit = 0.2
        mock_cms_rpc([fpath1, fpath2, fpath3, fpath4, fpath5])
        dm.init_from_db("mock_domain_id")
        return dm

    def test_multi_entrance(self):
        dm = self._construct_dm()
        dm.process_concepts("sid002", [
            Concept("intent", "weather.query"),
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(Mix(weather.query))(STATUS_STACKWAIT)
                Mix(weather.query)(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                default@weather.query(STATUS_WAIT_ACTION_CONFIRM)''')

    def test_mix_trigger(self):
        dm = self._construct_dm()
        dm.process_concepts("sid001", [
            Concept("intent", "consume.query"),
        ])
        assert(dm.is_waiting == False)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)''')
        assert(str(dm.context) == '''
            Context:
                Concept(city=None)
                Concept(date=None)
                Concept(intent=None)
                Concept(location=None)'''
        )

        # 2
        context = dm.get_candicate_units()
        priority_nodes = [agent[0] for agent in context["agents"]]
        assert(priority_nodes == [
            u'travel.service', u'default@weather.query', u'city',
            u'date', u'result', u'home.service', u'casual_talk',
            u'nike', u'zhou_hei_ya', u'name.query'
        ])
        assert(set(context["valid_slots"]) == set(["date", "city", "location"]))
        dm.process_concepts("sid002", [
            Concept("intent", "travel.service"),
        ])
        context = dm.get_candicate_units()
        priority_nodes = [agent[0] for agent in context["agents"]]
        assert(priority_nodes == [
            'travel.service', 'travel_consume.query', 'travel_left.query',
            'default@weather.query', 'city', 'date', 'result',
            'home.service', 'casual_talk', u'nike', 'zhou_hei_ya',
            'name.query'
        ])
        assert(set(context["valid_slots"]) == set(["date", "city", "location"]))
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(Mix(weather.query))(STATUS_STACKWAIT)
                travel.service(STATUS_WAIT_ACTION_CONFIRM)''')
        assert(str(dm.context) == '''
            Context:
                Concept(city=None)
                Concept(date=None)
                Concept(intent=travel.service)
                Concept(location=None)'''
        )
        dm.process_confirm('sid002', {
            'code': 0,
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(Mix(weather.query))(STATUS_DELAY_EXIST)''')
        assert(str(dm.context) == '''
            Context:
                Concept(city=None)
                Concept(date=None)
                Concept(intent=None)
                Concept(location=None)'''
        )
        dm.process_concepts("sid003", [
            Concept("intent", "consume.query"),
        ])
        # test ExpectAgenda
        assert(str(dm._agenda) == '''
            ValidIntents:
                casual_talk
                consume.query
                home.service
                left.query
                name.query
                travel.service
                weather.query
                where.query
            ValidSlots:
                city
                date
                location'''
        )
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(Mix(weather.query))(STATUS_STACKWAIT)
                travel_consume.query(STATUS_WAIT_ACTION_CONFIRM)''')
        assert(str(dm.context) == '''
            Context:
                Concept(city=None)
                Concept(date=None)
                Concept(intent=consume.query)
                Concept(location=None)'''
        )
        assert(dm.is_waiting == True)
        # 3
        dm.process_confirm('sid003', {
            'code': 0,
        })
        dm.process_concepts('sid004', [
            Concept("intent", "weather.query"),
            Concept("date", "明天"),
            Concept("city", "深圳")
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(Mix(weather.query))(STATUS_STACKWAIT)
                Mix(weather.query)(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                result(STATUS_WAIT_ACTION_CONFIRM)''')
        assert(str(dm.context) == '''
            Context:
                Concept(city=深圳)
                Concept(date=明天)
                Concept(intent=weather.query)
                Concept(location=None)'''
        )
        context = dm.get_candicate_units()
        priority_nodes = [agent[0] for agent in context["agents"]]
        assert(priority_nodes == [
            'result', 'default@weather.query', 'city', 'date',
            'all_city', 'travel.service', 'travel_consume.query',
            'travel_left.query', 'home.service', 'casual_talk',
            'nike', 'zhou_hei_ya', 'name.query'
        ])
        assert(dm.debug_loop == 4)
        dm._cancel_timer()

    def mix_trigger(self):
        dm = self._construct_dm()
        dm.process_concepts("sid001", [
            Concept("intent", "consume.query"),
        ])
        dm.process_concepts("sid002", [
            Concept("intent", "travel.service"),
        ])
        dm.process_confirm('sid002', {
            'code': 0,
        })
        dm.process_concepts("sid003", [
            Concept("intent", "consume.query"),
        ])
        dm.process_confirm('sid003', {
            'code': 0,
        })
        dm.process_concepts('sid004', [
            Concept("intent", "weather.query"),
            Concept("date", "明天"),
            Concept("city", "深圳")
        ])
        return dm

    def test_clear_and_share(self):
        dm = self.mix_trigger()
        dm.process_confirm('sid004', {
            'code': 0,
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(Mix(weather.query))(STATUS_STACKWAIT)
                Mix(weather.query)(STATUS_STACKWAIT)
                weather.query(STATUS_DELAY_EXIST)''')
        time.sleep(6 * dm.debug_timeunit)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(Mix(weather.query))(STATUS_STACKWAIT)
                Mix(weather.query)(STATUS_DELAY_EXIST)''')
        assert(str(dm.context) == '''
            Context:
                Concept(city=深圳)
                Concept(date=明天)
                Concept(intent=None)
                Concept(location=None)'''
        )
        dm.process_concepts("sid005", [
            Concept("intent", "spots.query"),
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(Mix(weather.query))(STATUS_STACKWAIT)
                Mix(weather.query)(STATUS_STACKWAIT)
                spots.query(STATUS_STACKWAIT)
                all_city(STATUS_WAIT_ACTION_CONFIRM)''')
        assert(dm.debug_loop == 3)

    def clear_share_clear(self):
        pass
