#!/usr/bin/env python
# encoding: utf-8
import copy
import os
import json
import pprint

from vikicommon.timer import TimerThread
from vikicommon.util.uniout import use_uniout
from vikicommon.log import (
    gen_log as log,
    add_stdout_handler,
    add_tornado_log_handler
)

from vikidm.util import PROJECT_DIR
from vikidm.dm import DialogEngine, Stack
from vikidm.context import Concept
from vikidm.biztree import Agent
from test_biztree import check_biz_tree

data_path = os.path.join(PROJECT_DIR, "tests", "data")


def test_stack():
    log.info("Test: Stack------------------------")
    stack = Stack()
    stack.push(1)
    stack.push(2)
    stack.push(3)
    assert(stack.top() == 3)
    assert(stack.pop() == 3)
    assert(stack.top() == 2)


def test_init_biz_from_json_file():
    """
    Test load json file;
    Test `Context` and `Stack` initialization.
    """
    log.info("Test: DialogEngine.init_biz_from_json_file()------------------------")
    dm = DialogEngine()
    fpath = os.path.join(data_path, 'biz_simulate_data/biz_unit_test.json')
    dm.init_from_json_files([fpath])
    # log.info("\n%s" % pprint.pformat(dm._biz_tree.to_dict(with_data=True)))
    # make sure _biz_tree, context, stack state.
    check_biz_tree(dm._biz_tree)
    concepts = dm._context._all_concepts.values()
    assert(str(concepts[0]) == "Concept(intent=None)")
    assert(str(concepts[1]) == "Concept(location=None)")
    assert(len(dm._stack) == 1)
    assert(dm._stack.top().tag == 'root')
    # make sure deep copy
    for bizunit in dm._biz_tree.all_nodes_itr():
        if isinstance(bizunit, Agent):
            for concept in bizunit.trigger_concepts:
                assert(concept.value is not None)
    for concept in dm._context._all_concepts.values():
        assert(concept.value is None)
    log.info("Tree:")
    dm._biz_tree.show()
    log.info("\n%s" % dm._context)
    log.info("\n%s" % dm._stack)


def test_get_triggered_bizunits():
    """
    Test trigger a simple Agent;
    Test trigger entrance_agent of Agency;
    TODO: Test trigger None entrance_agent of Agency;
    """
    log.info("Test: DialogEngine.test_get_triggered_bizunits()------------------------")
    dm = DialogEngine()
    fpath = os.path.join(data_path, 'biz_simulate_data/biz_unit_test.json')
    fpath2 = os.path.join(data_path, 'biz_simulate_data/biz_01.json')
    dm.init_from_json_files([fpath, fpath2])
    concepts = [
        Concept("intent", "where.query"),
        Concept("location", "nike")
    ]
    dm._update_concepts(concepts)
    for bizunit in dm._get_triggered_bizunits():
        assert(bizunit.tag == 'biz12')

    concepts = [
        Concept("intent", "name.query"),
    ]
    dm._update_concepts(concepts)
    for bizunit in dm._get_triggered_bizunits():
        assert(bizunit.tag == 'biz01')


def test_mark_completed_bizunits():
    """
     TODO
    """
    pass


def test_process_concepts():
    """
    name.query
    """
    fpath1 = os.path.join(data_path, 'biz_simulate_data/biz_12.json')
    fpath2 = os.path.join(data_path, 'biz_simulate_data/biz_01.json')
    dm = DialogEngine()
    dm.init_from_json_files([fpath1, fpath2])
    dm._biz_tree.show()
    log.info('\n%s' % pprint.pformat(dm._biz_tree.to_dict(with_data=True)))
    log.info('\n%s' % str(dm._stack))
    # test name.query
    concepts = [
        Concept('intent', 'name.query')
    ]
    dm.process_concepts("sid001", concepts)
    assert(len(dm._stack) == 2)
    assert(dm._stack.top().tag == 'biz01')
    log.info('\n%s' % str(dm._stack))

    confirm_data = {
        'sid': 'sid001',
        'error_code': 0,
        'error_msg': ''
    }
    dm.process_confirm(confirm_data)

    concepts = [
        Concept("intent", "where.query"),
        Concept("location", "nike")
    ]



class TestEngine(object):
    """  测试对话管理引擎 """
    def __init__(self):
        self._task = None
        self._timeunit = 0
        self._test_cases = self._load_test_case()
        self._dm = DialogEngine()

    def test_engine(self):
        fpath1 = os.path.join(data_path, 'biz_simulate_data/biz_12.json')
        fpath2 = os.path.join(data_path, 'biz_simulate_data/biz_01.json')
        self._dm.init_from_json_files([fpath1, fpath2])
        for caseid, case in self._test_cases.iteritems():
            time_list = []
            for session in case:
                time_list.append(session['input']['time'])
                time_list.append(session['confirm']['time'])
            max_timeunit = max(time_list) + 2
            self._task = TimerThread(1, self._run_case, case, max_timeunit)
            self._task.run()
            self._timeunit = 0

    def _run_case(self, sessions, max_timeunit):
        if self._timeunit == max_timeunit:
            self._task.stop()
            return
        self._timeunit += 1
        log.info("self._timeunit: %s" % self._timeunit)
        for session in sessions:
            request = session['input']
            confirm = session['confirm']
            if request['time'] == self._timeunit:
                request = copy.deepcopy(request)
                del request['time']
                del request['question']
                request['sid'] = str(self._timeunit)
                self._process_request(request)
            if confirm['time'] == self._timeunit:
                confirm = copy.deepcopy(confirm)
                del confirm['time']
                confirm['sid'] = str(self._timeunit)
                self._process_confirm(confirm)

    def _process_request(self, request):
        """
        """
        log.info("make request: \n%s" % pprint.pformat(request))
        concepts = []
        for key, value in request['concepts'].iteritems():
            concepts.append(Concept(key, value))
        #self._dm.process_request()

    def _process_confirm(self, request):
        """
        """
        log.info("make cofirm: \n%s" % pprint.pformat(request))

    def _load_test_case(self):
        """
        加载测试案例。
        """
        cases = {}
        path = os.path.join(data_path, 'terminal_simulate_data')
        list_dirs = os.walk(path)
        for path, dirs, files in list_dirs:
            for f in files:
                if f.startswith('case_12'):
                    source = os.path.join(path, f)
                    with open(source, 'r') as file:
                        biz = json.load(file)
                        cases.update(biz['cases'])
        return cases


if __name__ == '__main__':
    add_stdout_handler("INFO")
    use_uniout(True)
    add_tornado_log_handler("./", "INFO")
    test_stack()
    test_init_biz_from_json_file()
    test_get_triggered_bizunits()
    test_process_concepts()
    #test_process_confirm()
    tengine = TestEngine()
    #tengine.test_engine()
