#!/usr/bin/env python
# encoding: utf-8
import copy
import os
import json
import logging
import pprint
import requests

from evashare.timer import TimerThread
from evashare.log import init_logger

from evadm.util import PROJECT_DIR
from evadm import ConfigLog

data_path = os.path.join(PROJECT_DIR, "tests", "data")

init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)


def to_concepts_request(request):
    params = {
        'robot_id': '123',
        'project': 'test',
        'sid': request['sid']
    }
    concepts = {}
    for key, value in request['concepts'].iteritems():
        concepts[key] = value
    params['concepts'] = concepts
    url = "http://127.0.0.1:8888/v2/dm/concepts/"
    return url, params


def to_question_request(request):
    params = {
        'robot_id': '123',
        'project': 'test',
        'sid': request['sid']
    }
    params['question'] = request['question']
    url = "http://127.0.0.1:8888/v2/dm/question/"
    return url, params


class TestDM(object):
    """  测试对话管理引擎 """
    def init(self):
        self._task = None
        self._timeunit = 0
        self._test_cases = self._load_test_case()
        self._debug_timeunit = 0.5

    def test_engine(self):
        self.init()
        for caseid, case in self._test_cases.iteritems():
            time_list = []
            log.info("RUN CASE %s---------------------------" % caseid)
            for session in case:
                time_list.append(session['input']['time'])
                time_list.append(session['confirm']['time'])
            max_timeunit = max(time_list) + 2
            self._task = TimerThread(self._debug_timeunit, self._run_case, case, max_timeunit)
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
                #  TODO: SID #
                request['sid'] = str(self._timeunit)
                self._process_request(request)
            if confirm['time'] == self._timeunit:
                confirm = copy.deepcopy(confirm)
                del confirm['time']
                confirm['sid'] = str(self._timeunit)
                self._process_confirm(confirm)

    def _process_request(self, request):
        headers = { 'content-type': 'application/json' }
        url, params = to_concepts_request(request)
        #url, params = to_question_request(request)
        log.info("post %s \n%s" % (url, pprint.pformat(params)))
        data = requests.post(url, data=json.dumps(params), headers=headers, timeout=2).text
        print data

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
                        dict_cases = json.load(file)
                        cases.update(dict_cases['cases'])
        return cases
