import os
from evadm.io import DMFileIO
from evadm.util import PROJECT_DIR
from evadm.config import Config
from evadm.dm import DialogEngine
from evadm.context import Slot


TEST_PROJECT = "project_dm_test"
file_io = DMFileIO(TEST_PROJECT)
file_io._project_path = os.path.join(
    PROJECT_DIR, "tests", "data", "projects", TEST_PROJECT)


Config.input_timeout = 5.0
INPUT_TIMEOUT = Config.input_timeout + 1.0


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
    file_io = DMFileIO("mock_project")
    file_io._project_path = os.path.join(
        PROJECT_DIR, "tests", "data", "projects", TEST_PROJECT)
    dm = DialogEngine.get_dm(file_io, "0.1")
    dm.load_data(["name_query", "location_query", "weather_query"])
    dm.debug_timeunit = 0.2
    return dm


def round_out_simulate(dm):
    count = 0
    while count < dm.MAX_CONTEXT_RESERVED_ROUND:
        if dm._session._sid is None:
            new_sid = "sid00x%s" % count
        else:
            new_sid = dm._session._sid + 'a'
        dm.process_slots(new_sid, [Slot("intent", "casual_talk")])
        dm.process_confirm(new_sid, {
            'code': 0,
            'message': ''
        })
        count += 1
    assert(count == dm.MAX_CONTEXT_RESERVED_ROUND)


#__all__ = ["file_io"]
