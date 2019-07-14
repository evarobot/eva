# coding=utf-8
import json
import os
import logging
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

    def get_entities_with_value(self):
        """

        Returns
        -------
        entities : dict
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
        """
        entities = {}
        dir_path = os.path.join(self._project_path, "entity")
        for path, dirs, files in os.walk(dir_path):
            for file_name in files:
                if file_name.endswith("txt"):
                    file_path = os.path.join(path, file_name)
                    name = file_name.rstrip(".txt")
                    lines = [line.rstrip('\n') for line in open(file_path)]
                    values = {}
                    for line in lines:
                        words = line.split(' ')
                        values[words[0]] = list(set(words))
                    entities[name] = values
        # load data from sys
        dir_path = os.path.join(self._sys_path, "entity")
        for path, dirs, files in os.walk(dir_path):
            for file_name in files:
                if file_name.endswith("txt"):
                    file_path = os.path.join(path, file_name)
                    name = "@sys." + file_name.rstrip(".txt")
                    lines = [line.rstrip('\n') for line in open(file_path)]
                    values = {}
                    for line in lines:
                        words = line.split(' ')
                        values[words[0]] = list(set(words))
                    entities[name] = values
        return entities

    def get_label_data(self):

        pass


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
                f.write("{0}@{1}@{2}\n".format(data.label, data.question,
                                               data.node_id))

    def search(self, question):
        if self._caches:
            data = self._caches.get(question, [])
            return data
        with open(self._model_path, "r") as f:
            for line in f.readlines():
                label, question, node_id = line.rstrip("\n").split(self.SEP)
                same_question_data = self._caches.setdefault(question, [])
                same_question_data.append((label, node_id))
        return self._caches[question]


IO = NLUFileIO
SearchIO = FileSearchIO

__all__ = ["IO", "SearchIO", "NLUFileIO", "FileSearchIO"]
