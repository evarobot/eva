#!/usr/bin/env python
# encoding: utf-8
import logging
import json
import mock
import os
from vikidm.util import PROJECT_DIR, cms_rpc
from vikicommon.log import init_logger
from vikidm.config import ConfigLog, ConfigDM
from vikidm.dm import DialogEngine


init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)
data_path = os.path.join(PROJECT_DIR, "tests", "data")
ConfigDM.input_timeout = 5.0
INPUT_TIMEOUT = ConfigDM.input_timeout + 1.0


def mock_cms_rpc(paths):
    d_subtrees = []
    for fpath in paths:
        with open(fpath, 'r') as file_obj:
            d_subtrees.append(json.load(file_obj))
    root = {
        "data": {
            "id": "root",
            "tag": "root",
            "entrance": False,
            "event_id": "root",
            "subject": "",
            "scope": "",
            "timeout": "5",
            "type": "TYPE_MIX"
        },
        "children": []
    }
    root["children"] = d_subtrees
    data = {
        "code": 0,
        "tree": json.dumps(root)
    }
    cms_rpc.get_dm_biztree = mock.Mock(return_value=data)


def construct_dm():
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
    fpath1 = os.path.join(data_path, 'biz_simulate_data/biz_unit_test.json')
    fpath2 = os.path.join(data_path, 'biz_simulate_data/biz_01.json')
    fpath3 = os.path.join(data_path, 'biz_simulate_data/biz_chat.json')
    fpath4 = os.path.join(data_path, 'biz_simulate_data/biz_weather.json')
    dm = DialogEngine()
    mock_cms_rpc([fpath1, fpath2, fpath3, fpath4])
    dm.init_from_db("mock_domain_id")
    dm.debug_timeunit = 0.2
    return dm
