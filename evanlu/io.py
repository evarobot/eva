# coding=utf-8
import json
import os
import logging

from evanlu.testing import LabeledData
from evanlu.util import PROJECT_DIR
from evanlu.config import ConfigData
from evadm.io import DMFileIO

log = logging.getLogger(__name__)


class NLUFileIO(object):
    """"""

    def __init__(self, domain_id):
        self._domain_id = domain_id
        self._dm_io = DMFileIO(domain_id)
        self._project_path = os.path.join(
            PROJECT_DIR, "data", "projects", domain_id)
        self._sys_path = os.path.join(
            PROJECT_DIR, "data", "projects", "sys")

    @property
    def domain_id(self):
        return self._domain_id

    def get_sensitive_words(self):
        """

        Returns
        -------
        list of sensitive words: [str]
        """
        path = os.path.join(self._project_path, "sensitive.txt")
        words = [line.rstrip('\n') for line in open(path)]
        return words

    def get_not_nonsense_words(self):
        """

        Returns
        -------
        list of not nonsense words: [str]
        """
        path = os.path.join(self._project_path, "not_nonsense.txt")
        words = [line.rstrip('\n') for line in open(path)]
        return words

    def get_all_intent_entities(self):
        """

        Returns
        -------
        entities_by_intent : dict
            entities by intent dict
        """
        path = os.path.join(self._project_path, "intent", "intent.json")
        with open(path, "r") as file:
            data = file.read()
            l_intents = json.loads(data)
        rst = {}
        for d_intent in l_intents:
            rst[d_intent["name"]] = list(set(d_intent["slots"].values()).union(
                                         set(d_intent["optional_slots"])))
        return rst

    def get_entities_with_value(self):
        """

        Returns
        -------
        entities : dict
        {
            "entities": {
                {
                    "entity_name1": {
                        "value_name1": ["word1", "word2", ..],
                        "value_name2": ["word1", "word2", ..]
                    },

                    "entity_name2": {
                        "value_name1": ["word1", "word2", ..],
                        "value_name2": ["word1", "word2", ..]
                    }
                }
            },
            "scripts": {
                "entitye_name1": "script file content",
                "entitye_name2": "script file content",
            }

        """
        entities = {}
        scripts = {}
        dir_path = os.path.join(self._project_path, "entity")
        for path, dirs, files in os.walk(dir_path):
            for file_name in files:
                file_path = os.path.join(path, file_name)
                if file_name.endswith("txt"):
                    name = file_name.rstrip(".txt")
                    lines = [line.rstrip('\n') for line in open(file_path)]
                    values = {}
                    for line in lines:
                        words = line.split(' ')
                        values[words[0]] = list(set(words))
                    entities[name] = values
                if file_name.endswith("py"):
                    name = file_name.rstrip(".py")
                    with open(file_path, "r") as file:
                        script = file.read()
                        scripts[name] = script

        # load data from sys
        dir_path = os.path.join(self._sys_path, "entity")
        for path, dirs, files in os.walk(dir_path):
            for file_name in files:
                file_path = os.path.join(path, file_name)
                if file_name.endswith("txt"):
                    name = "@sys." + file_name.rstrip(".txt")
                    lines = [line.rstrip('\n') for line in open(file_path)]
                    values = {}
                    for line in lines:
                        words = line.split(' ')
                        values[words[0]] = list(set(words))
                    entities[name] = values
                if file_name.endswith("py"):
                    name = "@sys." + file_name.rstrip(".py")
                    with open(file_path, "r") as file:
                        script = file.read()
                        scripts[name] = script
        return {
            "entities": entities,
            "scripts": scripts
        }

    def get_label_data(self):
        """

        Returns
        -------
        label_question : list
            such as: [
                LabledData("weather.query", "what's the weather today"),
                ...
            ]

        """
        label_question = []
        dir_path = os.path.join(self._project_path, "intent")
        for path, dirs, files in os.walk(dir_path):
            for file_name in files:
                if file_name.endswith("txt"):
                    label = file_name.rstrip(".txt")
                    file_path = os.path.join(path, file_name)
                    with open(file_path, "r") as file:
                        for line in file.readlines():
                            question = line.rstrip("\n")
                            label_question.append(LabeledData(label, question))
        return label_question

    def get_intent_entities(self):
        """

        Returns
        -------
        intent_entities : dict
            entities related to intent
        """
        file_path = os.path.join(self._project_path, "intent", "intent.json")
        with open(file_path, "r") as file:
            intents = json.loads(file.read())
        rst = {}
        for intent in intents:
            rst[intent["name"]] = list(set(intent["slots"].values()))
        return rst


class FileSearchIO(object):
    """"""
    SEP = "@"

    def __init__(self, domain_id):
        self._domain_id = domain_id
        self._model_path = os.path.join(ConfigData.model_data_path,
                                        domain_id + ".txt")
        self._caches = {}

    def save(self, labeled_data):
        """ save trading data to file.

        Parameters
        ----------
        labeled_data : [(lable, question, node_id]
            labled questions with node id in the project intent tree.
        """
        with open(self._model_path, "w") as f:
            for data in labeled_data:
                f.write("{0}@{1}\n".format(data.label, data.question))

    def search(self, question):
        if self._caches:
            data = self._caches.get(question, [])
            return data
        with open(self._model_path, "r") as f:
            for line in f.readlines():
                label, question = line.rstrip("\n").split(self.SEP)
                same_question_data = self._caches.setdefault(question, [])
                same_question_data.append(label)
        return self._caches[question]


IO = NLUFileIO
SearchIO = FileSearchIO

__all__ = ["IO", "SearchIO", "NLUFileIO", "FileSearchIO"]
