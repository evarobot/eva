#!/usr/bin/env python
# encoding: utf-8
from evadm.context import Slot
from evadm.testing import construct_dm, round_out_simulate


class TestTargetAgencyCase(object):
    '''
    root
    ├── casual_talk
    ├── name.query
    ├── weather.query
    │   ├── addtional_slot
    │   ├── city
    │   ├── city_priority
    │   ├── date
    │   ├── default@weather.query
    │   ├── optional_none
    │   └── result
    └── where.query
        ├── nike
        └── zhou_hei_ya
    '''

    def test_location_input(self):
        dm = construct_dm()
        dm.process_slots("sid001", [
            Slot("intent", "where.query"),
            Slot("location", "nike")
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                where.query(STATUS_STACKWAIT)
                nike(STATUS_WAIT_ACTION_CONFIRM)''')
        assert(str(dm.context) == '''
            Context:
                Slot(city=None)
                Slot(country=None)
                Slot(date=None)
                Slot(intent=where.query)
                Slot(location=nike)
                Slot(meteorology=None)'''
        )
        assert(dm.debug_loop == 2)

    def test_success_confirm(self):
        dm = construct_dm()
        dm.process_slots("sid001", [
            Slot("intent", "where.query"),
            Slot("location", "nike")
        ])
        dm.process_confirm('sid001', {
            'code': 0,
            'message': ''
        })
        assert(dm.debug_loop == 2)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                where.query(STATUS_DELAY_EXIST)''')
        assert(str(dm.context) == '''
            Context:
                Slot(city=None)
                Slot(country=None)
                Slot(date=None)
                Slot(intent=where.query)
                Slot(location=nike)
                Slot(meteorology=None)'''
        )

    def test_failed_confirm(self):
        dm = construct_dm()
        dm.process_slots("sid001", [
            Slot("intent", "where.query"),
            Slot("location", "nike")
        ])
        dm.process_confirm('sid001', {
            'code': -1,
            'message': ''
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)''')
        assert(str(dm.context) == '''
            Context:
                Slot(city=None)
                Slot(country=None)
                Slot(date=None)
                Slot(intent=None)
                Slot(location=None)
                Slot(meteorology=None)'''
        )
        assert(dm.debug_loop == 6)

    def test_default_triggered(self):
        dm = construct_dm()
        dm.process_slots("sid001", [Slot("intent", "weather.query")])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                default@weather.query(STATUS_WAIT_ACTION_CONFIRM)''')
        assert(str(dm.context) == '''
            Context:
                Slot(city=None)
                Slot(country=None)
                Slot(date=None)
                Slot(intent=weather.query)
                Slot(location=None)
                Slot(meteorology=None)'''
        )
        assert(dm.debug_loop == 2)
        dm.cancel_timer()

    def test_default_then_result(self):
        # default triggered
        dm = construct_dm()
        dm.process_slots("sid001", [Slot("intent", "weather.query")])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                default@weather.query(STATUS_WAIT_ACTION_CONFIRM)''')
        dm.process_confirm('sid001', {
            'code': 0,
            'message': ''
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                default@weather.query(STATUS_WAIT_TARGET)''')

        # result triggered
        dm.process_slots("sid002", [
            Slot('intent', 'weather.query'),
            Slot('city', 'Shenzheng'),
            Slot('meteorology', 'snow'),
            Slot('date', 'today')
        ])
        assert(str(dm.context) == '''
            Context:
                Slot(city=Shenzheng)
                Slot(country=None)
                Slot(date=today)
                Slot(intent=weather.query)
                Slot(location=None)
                Slot(meteorology=snow)'''
        )
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                result(STATUS_WAIT_ACTION_CONFIRM)''')
        dm.process_confirm('sid002', {
            'code': 0,
            'message': ''
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_DELAY_EXIST)''')

        # context preserve
        dm.process_slots("sid001", [
            Slot('intent', 'weather.query'),
            Slot('city', 'Shanghai'),
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                result(STATUS_WAIT_ACTION_CONFIRM)''')
        assert(str(dm.context) == '''
            Context:
                Slot(city=Shanghai)
                Slot(country=None)
                Slot(date=today)
                Slot(intent=weather.query)
                Slot(location=None)
                Slot(meteorology=snow)'''
        )
        dm.process_confirm('sid001', {
            'code': 0,
            'message': ''
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_DELAY_EXIST)''')

        # round out, clear context
        round_out_simulate(dm)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)''')
        assert(str(dm.context) == '''
            Context:
                Slot(city=None)
                Slot(country=None)
                Slot(date=None)
                Slot(intent=None)
                Slot(location=None)
                Slot(meteorology=None)'''
        )

    def test_target_complete(self):
        # incomplete input
        dm = construct_dm()
        dm.process_slots("sid001", [
            Slot("intent", "weather.query"),
            Slot("city", "Shenzheng")
        ])
        assert(str(dm.context) == '''
            Context:
                Slot(city=Shenzheng)
                Slot(country=None)
                Slot(date=None)
                Slot(intent=weather.query)
                Slot(location=None)
                Slot(meteorology=None)'''
        )
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                date(STATUS_WAIT_ACTION_CONFIRM)''')
        dm.process_confirm('sid001', {
            'code': 0,
            'message': ''
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                date(STATUS_WAIT_TARGET)''')

        # target complete
        dm.process_slots("sid002", [
            Slot("date", "today"),
            Slot("meteorology", "snow"),
            Slot("intent", "weather.query")
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                result(STATUS_WAIT_ACTION_CONFIRM)''')
        assert(str(dm.context) == '''
            Context:
                Slot(city=Shenzheng)
                Slot(country=None)
                Slot(date=today)
                Slot(intent=weather.query)
                Slot(location=None)
                Slot(meteorology=snow)''')
        dm.cancel_timer()

    def test_optional(self):
        dm = construct_dm()
        dm.process_slots("sid001", [
            Slot("intent", "weather.query"),
            Slot("city", "Shanghai"),
            Slot("date", "tomorrow"),
            Slot("meteorology", "rainy")
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                result(STATUS_WAIT_ACTION_CONFIRM)''')
        dm.process_confirm('sid001', {
            'code': 0,
            'message': ''
        })

        # The more slot match, the higher priority.
        # Three candicate nodes
        dm = construct_dm()
        dm.process_slots("sid001", [
            Slot("intent", "weather.query"),
            Slot("city", "Beijing"),
            Slot("date", "tomorrow")
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                optional_none(STATUS_WAIT_ACTION_CONFIRM)''')
        dm.process_confirm('sid002', {
            'code': 0,
            'message': ''
        })

        # Given the same slot matches,
        # The more specified slots match, the higher priority.
        # Two candicate nodes
        dm = construct_dm()
        dm.process_slots("sid001", [
            Slot("intent", "weather.query"),
            Slot("city", "Beijing"),
            Slot("date", "tomorrow"),
            Slot("meteorology", "rainy")
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                city_priority(STATUS_WAIT_ACTION_CONFIRM)''')
        dm.process_confirm('sid003', {
            'code': 0,
            'message': ''
        })

        # Addtional slots
        dm = construct_dm()
        dm.process_slots("sid001", [
            Slot("intent", "weather.query"),
            Slot("city", "Beijing"),
            Slot("date", "tomorrow"),
            Slot("country", "china"),
            Slot("meteorology", "rainy"),
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                addtional_slot(STATUS_WAIT_ACTION_CONFIRM)''')
