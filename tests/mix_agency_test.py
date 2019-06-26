#!/usr/bin/env python
# encoding: utf-8
import os
from evadm.context import Slot
from evadm.dm import DialogEngine
from .prepare import data_path, mock_cms_gate, round_out_simulate


class TestMixAgency(object):
    '''
    root
    ├── Mix(Mix(weather.query))
    │   ├── Mix(weather.query)
    │   │   ├── spots.query
    │   │   │   └── all_city
    │   │   └── weather.query
    │   │       ├── city
    │   │       ├── date
    │   │       ├── default@weather.query
    │   │       └── result
    │   ├── travel.service
    │   ├── travel_consume.query
    │   └── travel_left.query
    ├── Mix(home.service)
    │   ├── home.service
    │   ├── home_consume.query
    │   └── home_left.query
    ├── casual_talk
    ├── name.query
    └── where.query
        ├── nike
        └── zhou_hei_ya
    '''

    def _construct_dm(self):
        fpath1 = os.path.join(data_path, 'biz_simulate_data/biz_mix_travel.json')
        fpath2 = os.path.join(data_path, 'biz_simulate_data/biz_mix_home.json')
        fpath4 = os.path.join(data_path, 'biz_simulate_data/biz_unit_test.json')
        fpath5 = os.path.join(data_path, 'biz_simulate_data/biz_01.json')
        dm = DialogEngine.get_dm("0.1")
        dm.debug_timeunit = 0.2
        mock_cms_gate([fpath1, fpath2, fpath4, fpath5])
        dm.init_from_db("mock_domain_id")
        return dm

    def test_multi_entrance(self):
        dm = self._construct_dm()
        dm.biz_tree.show()
        dm.process_slots("sid002", [
            Slot("intent", "weather.query"),
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(Mix(weather.query))(STATUS_STACKWAIT)
                Mix(weather.query)(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                default@weather.query(STATUS_WAIT_ACTION_CONFIRM)''')
        dm.cancel_timer()

    def test_mix_trigger(self):
        dm = self._construct_dm()
        dm.process_slots("sid001", [
            Slot("intent", "consume.query"),
        ])
        assert(dm.is_waiting == False)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)''')
        assert(str(dm.context) == '''
            Context:
                Slot(city=None)
                Slot(date=None)
                Slot(intent=None)
                Slot(location=None)'''
        )

        # 2
        context = dm.get_visible_units()
        priority_nodes = [agent[0] for agent in context["agents"]]
        assert(priority_nodes == [
            u'travel.service', u'default@weather.query', u'city',
            u'date', u'result', u'home.service', u'nike', u'zhou_hei_ya'
            , u'name.query', 'casual_talk'
        ])
        assert(set(context["visible_slots"]) == set(["date", "city", "location"]))
        dm.process_slots("sid002", [
            Slot("intent", "travel.service"),
        ])
        context = dm.get_visible_units()
        priority_nodes = [agent[0] for agent in context["agents"]]
        assert(priority_nodes == [
            'travel.service', 'travel_consume.query', 'travel_left.query',
            'default@weather.query', 'city', 'date', 'result',
            'home.service', u'nike', 'zhou_hei_ya',
            'name.query', 'casual_talk',
        ])
        assert(set(context["visible_slots"]) == set(["date", "city", "location"]))
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(Mix(weather.query))(STATUS_STACKWAIT)
                travel.service(STATUS_WAIT_ACTION_CONFIRM)''')
        assert(str(dm.context) == '''
            Context:
                Slot(city=None)
                Slot(date=None)
                Slot(intent=travel.service)
                Slot(location=None)'''
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
                Slot(city=None)
                Slot(date=None)
                Slot(intent=None)
                Slot(location=None)'''
        )
        dm.process_slots("sid003", [
            Slot("intent", "consume.query"),
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
                Slot(city=None)
                Slot(date=None)
                Slot(intent=consume.query)
                Slot(location=None)'''
        )
        assert(dm.is_waiting == True)
        # 3
        dm.process_confirm('sid003', {
            'code': 0,
        })
        dm.process_slots('sid004', [
            Slot("intent", "weather.query"),
            Slot("date", "tomorrow"),
            Slot("city", "Shenzheng")
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
                Slot(city=Shenzheng)
                Slot(date=tomorrow)
                Slot(intent=weather.query)
                Slot(location=None)'''
        )
        context = dm.get_visible_units()
        priority_nodes = [agent[0] for agent in context["agents"]]
        assert(priority_nodes == [
            'result', 'default@weather.query', 'city', 'date',
            'all_city', 'travel.service', 'travel_consume.query',
            'travel_left.query', 'home.service',
            'nike', 'zhou_hei_ya', 'name.query', 'casual_talk'
        ])
        assert(dm.debug_loop == 4)
        dm.cancel_timer()

    def mix_trigger(self):
        dm = self._construct_dm()
        dm.process_slots("sid001", [
            Slot("intent", "consume.query"),
        ])
        dm.process_slots("sid002", [
            Slot("intent", "travel.service"),
        ])
        dm.process_confirm('sid002', {
            'code': 0,
        })
        dm.process_slots("sid003", [
            Slot("intent", "consume.query"),
        ])
        dm.process_confirm('sid003', {
            'code': 0,
        })
        dm.process_slots('sid004', [
            Slot("intent", "weather.query"),
            Slot("date", "tomorrow"),
            Slot("city", "Shenzheng")
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
        round_out_simulate(dm)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(Mix(weather.query))(STATUS_STACKWAIT)
                Mix(weather.query)(STATUS_DELAY_EXIST)''')
        assert(str(dm.context) == '''
            Context:
                Slot(city=Shenzheng)
                Slot(date=tomorrow)
                Slot(intent=None)
                Slot(location=None)'''
        )
        dm.process_slots("sid00x", [
            Slot("intent", "spots.query"),
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                Mix(Mix(weather.query))(STATUS_STACKWAIT)
                Mix(weather.query)(STATUS_STACKWAIT)
                spots.query(STATUS_STACKWAIT)
                all_city(STATUS_WAIT_ACTION_CONFIRM)''')
        assert(dm.debug_loop == 4)

    def clear_share_clear(self):
        pass
