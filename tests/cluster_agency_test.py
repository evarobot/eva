#!/usr/bin/env python
# encoding: utf-8
from vikidm.context import Concept
from .prepare import construct_dm


class TestClusterAgencyCase(object):
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

    def test_location_input(self):
        dm = construct_dm()
        dm.process_concepts("sid001", [
            Concept("intent", "where.query"),
            Concept("location", "nike")
        ])
        assert(str(dm.stack) == '''
            Stack:
                root(STATUS_STACKWAIT)
                where.query(STATUS_STACKWAIT)
                nike(STATUS_WAIT_ACTION_CONFIRM)''')

        assert(str(dm.context) == '''
            Context:
                Concept(city=None)
                Concept(date=None)
                Concept(intent=where.query)
                Concept(location=nike)'''
        )
        assert(dm.debug_loop == 2)
        assert(dm.is_waiting == True)
        dm._cancel_timer()

    def test_success_confirm(self):
        dm = construct_dm()
        dm.process_concepts("sid001", [
            Concept("intent", "where.query"),
            Concept("location", "nike")
        ])
        dm.process_confirm('sid001', {
            'code': 0,
            'message': ''
        })
        assert(dm.debug_loop == 3)
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
        assert(dm.is_waiting == False)

    def test_failed_confirm(self):
        dm = construct_dm()
        dm.process_concepts("sid001", [
            Concept("intent", "where.query"),
            Concept("location", "nike")
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
                Concept(city=None)
                Concept(date=None)
                Concept(intent=None)
                Concept(location=None)'''
        )
        assert(dm.debug_loop == 6)