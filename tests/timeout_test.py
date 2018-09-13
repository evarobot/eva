#!/usr/bin/env python
# encoding: utf-8
import time

from vikidm.context import Slot
from .prepare import construct_dm, INPUT_TIMEOUT


class TestTiemoutCase(object):
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
    def test_process_confirm_case_agent_timeout(self):
        dm = construct_dm()
        dm.process_slots("sid001", [
            Slot('intent', 'name.query')
        ])
        assert(dm.is_waiting)
        time.sleep(INPUT_TIMEOUT * dm.debug_timeunit)
        assert(dm.is_waiting == False)
        assert(dm.debug_loop == 6)

    def test_target_default_triggered_timeout(self):
        dm = construct_dm()
        dm.process_slots("sid001", [
            Slot("intent", "weather.query")
        ])
        dm.process_confirm('sid001', {
            'code': 0,
            'message': ''
        })
        assert(dm.is_waiting)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                default@weather.query(STATUS_WAIT_TARGET)''')

        time.sleep(INPUT_TIMEOUT * dm.debug_timeunit)
        assert(dm.is_waiting == False)
        assert(dm.debug_loop == 7)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)''')
        assert(dm.context["intent"].value is None)
