#!/usr/bin/env python
# encoding: utf-8
import copy
import os
import json
import pprint

from vikicommon.timer import TimerThread
from vikidm.util import PROJECT_DIR
from vikidm.dm import DialogEngine
from vikidm.context import Concept
from vikicommon.util.uniout import use_uniout
from vikicommon.log import (
    gen_log as log,
    add_stdout_handler,
    add_tornado_log_handler
)
from test_biztree import check_biz_tree

data_path = os.path.join(PROJECT_DIR, "tests", "data")


class TestEngine(object):
    """  测试对话管理引擎 """
    def __init__(self):
        self._task = None
        self._timeunit = 0
        self._test_cases = self._load_test_case()

    def test_init_biz_from_json_file(self):
        dm = DialogEngine()
        fpath = os.path.join(data_path, 'biz_simulate_data/biz_12.json')
        dm.init_from_json_files([fpath])
        log.info("\n%s" % pprint.pformat(dm._biz_tree.to_dict(with_data=True)))
        log.info("\n%s" % dm._context)
        check_biz_tree(dm._biz_tree)
        concepts = dm._context._all_concepts.values()
        assert(str(concepts[0]) == "Concept(intent=None)")
        assert(str(concepts[1]) == "Concept(location=None)")

    def test_update_concept(self):
        dm = DialogEngine()
        fpath = os.path.join(data_path, 'biz_simulate_data/biz_12.json')
        dm.init_from_json_files([fpath])
        log.info("\n%s" % pprint.pformat(dm._biz_tree.to_dict(with_data=True)))
        log.info("\n%s" % dm._context)
        concepts = [
            Concept("intent", "where.query"),
            Concept("location", "nike")
        ]
        dm._update_concepts(concepts)
        log.info("*" * 30)
        for bizunit in dm._get_focus_bizunit():
            assert(bizunit.tag == 'nike')
            log.info(bizunit.event_id)
            log.info(bizunit.tag)


    def test_engine(self):
        dm = DialogEngine()
        fpath1 = os.path.join(data_path, 'biz_simulate_data/biz_12.json')
        fpath2 = os.path.join(data_path, 'biz_simulate_data/biz_01.json')
        dm.init_from_json_files([fpath1, fpath2])
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
        request['concepts']

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
    tengine = TestEngine()
    #tengine.test_engine()
    tengine.test_update_concept()
    #tengine.test_init_biz_from_json_file()
