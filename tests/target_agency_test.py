#!/usr/bin/env python
# encoding: utf-8
import time
from vikidm.context import Slot
from .prepare import construct_dm, INPUT_TIMEOUT


class TestTargetAgencyCase(object):
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
                Slot(date=None)
                Slot(intent=weather.query)
                Slot(location=None)'''
        )
        assert(dm.debug_loop == 2)
        assert(dm.is_waiting == True)
        dm._cancel_timer()

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
                weather.query(STATUS_WAIT_TARGET)''')

        # result triggered
        dm.process_slots("sid002", [
            Slot('intent', 'weather.query'),
            Slot('city', '深圳'),
            Slot('date', '今天')
        ])
        assert(str(dm.context) == '''
            Context:
                Slot(city=深圳)
                Slot(date=今天)
                Slot(intent=weather.query)
                Slot(location=None)'''
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
        assert(dm.is_waiting == True)

        # context preserve
        dm.process_slots("sid003", [
            Slot('intent', 'weather.query'),
            Slot('city', '北京'),
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                result(STATUS_WAIT_ACTION_CONFIRM)''')
        assert(str(dm.context) == '''
            Context:
                Slot(city=北京)
                Slot(date=今天)
                Slot(intent=weather.query)
                Slot(location=None)'''
        )
        dm.process_confirm('sid003', {
            'code': 0,
            'message': ''
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_DELAY_EXIST)''')
        assert(dm.is_waiting == True)

        # timeout, clear context
        time.sleep(INPUT_TIMEOUT * dm.debug_timeunit)
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
        assert(dm.is_waiting == False)

    def test_target_complete(self):
        # incomplete input
        dm = construct_dm()
        dm.process_slots("sid001", [
            Slot("intent", "weather.query"),
            Slot("city", "深圳")
        ])
        assert(str(dm.context) == '''
            Context:
                Slot(city=深圳)
                Slot(date=None)
                Slot(intent=weather.query)
                Slot(location=None)'''
        )
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                date(STATUS_WAIT_ACTION_CONFIRM)''')
        assert(dm.is_waiting == True)
        dm.process_confirm('sid001', {
            'code': 0,
            'message': ''
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                date(STATUS_WAIT_TARGET)''')
        assert(dm.is_waiting == True)

        # target complete
        dm.process_slots("sid002", [
            Slot("date", "今天"),
            Slot("intent", "weather.query")
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                result(STATUS_WAIT_ACTION_CONFIRM)''')
        assert(str(dm.context) == '''
            Context:
                Slot(city=深圳)
                Slot(date=今天)
                Slot(intent=weather.query)
                Slot(location=None)''')
        assert(dm.is_waiting == True)
        dm._cancel_timer()
