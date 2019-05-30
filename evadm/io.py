import os
import json
import logging

from evanlu.util import PROJECT_DIR

log = logging.getLogger(__name__)


class DMFileIO(object):
    def __init__(self, domain_id):
        self._domain_id = domain_id
        self._data_path = os.path.join(
            PROJECT_DIR, "data", "projects", domain_id, "dm")

    @property
    def domain_id(self):
        return self._domain_id

    def get_dict_tree(self, including=[]):
        """ construct a tree from json files.

        Parameters
        ----------
        including : list
            used for testing

        Returns
        -------
        tree of dict : dict

        """
        trees = []
        opened_file_names = []
        for path, dirs, files in os.walk(self._data_path):
            for f in files:
                if f.endswith('json'):
                    file_name = f.rstrip(".json")
                    if len(including) == 0 or file_name in including:
                        file_path = os.path.join(path, f)
                        with open(file_path, 'r') as file_obj:
                            trees.append(
                                json.loads(file_obj.read()))
                        opened_file_names.append(file_name)
        if including:
            assert(set(opened_file_names) == set(including))
        root = {
            "data": {
                "id": "root",
                "tag": "root",
                "entrance": False,
                "response_id": "root",
                "timeout": "5",
                "type": "TYPE_MIX"
            },
            "children": trees
        }
        return root

    def get_tree_label_data(self):
        # for nlu
        pass


DMIO = DMFileIO

__all__ = ["DMIO", "DMFileIO"]
