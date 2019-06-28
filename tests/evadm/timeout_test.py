#!/usr/bin/env python
# encoding: utf-8
import time

from eva.dm import Slot
from .prepare import construct_dm, round_out_simulate


class TestTiemoutCase(object):
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
    def test_agent_action_timeout(self):
        dm = construct_dm()
        dm.process_slots("sid001", [
            Slot('intent', 'name.query')
        ])
        assert(dm.is_waiting)
        time.sleep((dm.stack.top().timeout + 1) * dm.debug_timeunit)
        assert(dm.is_waiting == False)
        assert(dm.debug_loop == 6)

    def test_default_target_agent_input_timeout(self):
        dm = construct_dm()
        dm.process_slots("sid001", [
            Slot("intent", "weather.query")
        ])
        dm.process_confirm('sid001', {
            'code': 0,
            'message': ''
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                default@weather.query(STATUS_WAIT_TARGET)''')

        round_out_simulate(dm)
        assert(dm.debug_loop == 8)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)''')
        assert(dm.context["intent"].value is None)
