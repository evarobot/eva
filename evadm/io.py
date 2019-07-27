import os
import json
import logging

from evanlu.util import PROJECT_DIR

log = logging.getLogger(__name__)


class DMFileIO(object):
    def __init__(self, domain_id):
        self._domain_id = domain_id
        self._project_path = os.path.join(
            PROJECT_DIR, "data", "projects", domain_id)

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
        dir_path = os.path.join(self._project_path, "dm")
        for path, dirs, files in os.walk(dir_path):
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
        # useless
        label_question = {}
        dir_path = os.path.join(self._project_path, "intent")
        for path, dirs, files in os.walk(dir_path):
            for file_name in files:
                if file_name.endswith("txt"):
                    label = file_name.rstrip(".txt")
                    file_path = os.path.join(path, file_name)
                    with open(file_path, "r") as file:
                        data = [line.rstrip("\n") for line in file.readlines()]
                        label_question[label] = data

        label_nodeid = {}
        def parse_tree(parent):
            data = parent['data']
            trigger_slots = data.get("trigger_slots", None)
            if trigger_slots:
                intent = list(filter(lambda x: x.startswith("intent="),
                              trigger_slots))
                assert intent
                intent = intent[0]
                intent = intent.lstrip("intent=")
                nodeids = label_nodeid.setdefault(intent, [])
                nodeids.append(data["id"])
            for child in parent['children']:
                parse_tree(child)
        #
        dict_tree = self.get_dict_tree()
        parse_tree(dict_tree)
        label_data = []
        assert(set(label_question.keys()) == set(label_nodeid.keys()))
        for label in label_question.keys():
            label_data.append((label, ))
            label_question[label]
            label_nodeid[label]
        return label_question






DMIO = DMFileIO

__all__ = ["DMIO", "DMFileIO"]
