#!/usr/bin/env python
# encoding: utf-8
import time
from evadm.context import Slot
from .prepare import construct_dm, round_out_simulate


class TestSessionCase(object):
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

    def test_process_confirm_case_agent_ignore_old_session(self):
        dm = construct_dm()
        dm.process_slots("sid001", [
            Slot('intent', 'name.query')
        ])
        assert(dm._session.valid_session("sid001"))
        assert(dm.is_waiting)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                name.query(STATUS_WAIT_ACTION_CONFIRM)''')

        # ignore old session
        dm.process_confirm('sid000', {
            'code': 0,
            'message': ''
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                name.query(STATUS_WAIT_ACTION_CONFIRM)''')
        assert(dm.is_waiting)
        time.sleep((dm.stack.top().timeout + 1) * dm.debug_timeunit)
        assert(not dm.is_waiting)
        assert(dm.debug_loop == 5)


class TestTopicCase(object):

    def test_action_waiting_agent_switch(self):
        dm = construct_dm()
        dm.process_slots("sid001", [
            Slot('intent', 'name.query')
        ])
        assert(dm.is_waiting)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                name.query(STATUS_WAIT_ACTION_CONFIRM)''')

        # switch to another agent
        ret = dm.process_slots("sid002", [
            Slot("intent", "casual_talk"),
        ])
        assert(ret['response_id'] == 'casual_talk')
        ret = dm.process_confirm('sid002', {
            'code': 0,
            'message': ''
        })
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)''')
        assert(dm.context['intent'].value is None)
        assert(not dm.is_waiting)
        assert(dm.debug_loop == 2)

    def test_target_waiting_agent_switch(self):
        pass

    def test_preserve_agency_switch(self):
        pass

    def test_target_agency_to_agent(self):
        dm = construct_dm()
        dm.process_slots("sid001", [
            Slot("intent", "weather.query")
        ])
        dm.process_confirm('sid001', {
            'code': 0,
            'message': ''
        })
        assert(str(dm.context) == '''
            Context:
                Slot(city=None)
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
                default@weather.query(STATUS_WAIT_TARGET)''')

        # switch to agent
        dm.process_slots("sid002", [
            Slot("intent", "casual_talk"),
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                default@weather.query(STATUS_WAIT_TARGET)
                casual_talk(STATUS_WAIT_ACTION_CONFIRM)'''
        )

        dm.process_confirm('sid002', {'code': 0, 'message': ''})

        assert(dm.is_waiting)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                default@weather.query(STATUS_WAIT_TARGET)''')
        assert(str(dm.context) == '''
            Context:
                Slot(city=None)
                Slot(country=None)
                Slot(date=None)
                Slot(intent=None)
                Slot(location=None)
                Slot(meteorology=None)'''
        )
        round_out_simulate(dm)
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)'''
        )
        assert(str(dm.context) == '''
            Context:
                Slot(city=None)
                Slot(country=None)
                Slot(date=None)
                Slot(intent=None)
                Slot(location=None)
                Slot(meteorology=None)'''
        )

    def test_target_agency_to_target_agency(self):
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

        dm.process_slots("sid002", [
            Slot("intent", "casual_talk"),
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                weather.query(STATUS_STACKWAIT)
                default@weather.query(STATUS_WAIT_TARGET)
                casual_talk(STATUS_WAIT_ACTION_CONFIRM)'''
        )

        dm.process_slots("sid00x", [
            Slot("intent", "where.query"),
            Slot("location", "nike")
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                where.query(STATUS_STACKWAIT)
                nike(STATUS_WAIT_ACTION_CONFIRM)'''
        )
