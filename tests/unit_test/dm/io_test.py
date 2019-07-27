import os
from evadm.io import DMFileIO
from evadm.util import PROJECT_DIR
from evadm.testing import file_io
from evashare.util import same_dict


def test_dm_file_io():
    tree = file_io.get_dict_tree()
    assert(len(tree["children"]) == 7)
    target = {
        "data": {
            "id": "root",
            "tag": "root",
            "entrance": False,
            "response_id": "root",
            "timeout": "5",
            "type": "TYPE_MIX"
        }
    }
    assert same_dict(tree, target, "children")


def test_get_tree_label_data():
    file_io = DMFileIO("project_cn_test")
    file_io._project_path = os.path.join(
        PROJECT_DIR, "tests", "data", "projects", "project_cn_test")
    rst = file_io.get_tree_label_data()

