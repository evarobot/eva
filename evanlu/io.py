# coding=utf-8
import json
import os
import logging
from evanlu.util import PROJECT_DIR
from evadm.io import DMFileIO

log = logging.getLogger(__name__)


class NLUFileIO(object):
    """"""

    def __init__(self, domain_id):
        self._domain_id = domain_id
        self._dm_io = DMFileIO(domain_id)
        self._project_path = os.path.join(
            PROJECT_DIR, "data", "projects", domain_id)

    @property
    def domain_id(self):
        return self._domain_id

    def get_dm_biztree(self):
        """ Call CMS module for tree.

        """
        url = self.base_url + '/v2/{}/evadm'.format(domain_id)
        data = requests.get(url, timeout=timeout)
        log.info("GET %s %s", url, data.status_code)
        assert (data.status_code == 200)
        return json.loads(data.text)

    def response_id_to_answer(self, domain_id, response_id):
        """

        Parameters
        ----------
        domain_id : 项目ID
        response_id : 事件ID

        """
        params = {
            'domain_id': domain_id,
            'response_id': response_id
        }
        headers = {'content-type': 'application/json'}
        url = self.base_url + '/v2/response_id_to_answer'
        data = requests.post(url,
                             data=json.dumps(params),
                             headers=headers,
                             timeout=timeout)
        assert (data.status_code == 200)
        return json.loads(data.text)

    def get_domain_by_name(self, name):
        """ Call CMS module for domain id.

        """
        params = {
            'name': name,
        }
        url = self.base_url + '/v2/rpc/get_domain_by_name'
        headers = {'content-type': 'application/json'}
        data = requests.post(url,
                             data=json.dumps(params),
                             headers=headers,
                             timeout=timeout)
        assert (data.status_code == 200)
        return json.loads(data.text)

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

    def get_domain_entities(self, domain_id):
        url = self.base_url + '/v2/rpc/get_domain_entities'
        headers = {'content-type': 'application/json'}
        data = requests.post(url,
                             data=json.dumps({
                                 'domain_id': domain_id
                             }),
                             headers=headers,
                             timeout=timeout)
        assert (data.status_code == 200)
        return json.loads(data.text)

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
            for fname in files:
                if fname.endswith("txt"):
                    fpath = os.path.join(path, fname)
                    name = fname.rstrip(".txt")
                    lines = [line.rstrip('\n') for line in open(fpath)]
                    values = {}
                    for line in lines:
                        words = line.split(' ')
                        values[words[0]] = words
                    entities[name] = values
        return entities

    def get_all_intent_entities(self, domain_id):
        url = self.base_url + '/v2/rpc/get_all_intent_entities'
        headers = {'content-type': 'application/json'}
        data = requests.post(url,
                             data=json.dumps({
                                 'domain_id': domain_id
                             }),
                             headers=headers,
                             timeout=timeout)
        assert (data.status_code == 200)
        return json.loads(data.text)

    def get_tree_label_data(self):

        pass


    def get_intent_entities_without_value(self, domain_id, intent_name):
        url = self.base_url + '/v2/rpc/get_intent_entities_without_value'
        headers = {'content-type': 'application/json'}
        data = requests.post(url,
                             data=json.dumps({
                                 'domain_id': domain_id,
                                 'intent_name': intent_name
                             }),
                             headers=headers,
                             timeout=timeout)
        assert (data.status_code == 200)
        return json.loads(data.text)


class FileSearchIO(object):
    """"""

    def __init__(self, domain_id):
        self._domain_id = domain_id

    def save(self, label_data):
        pass

    def search(self, question):
        pass


IO = NLUFileIO
SearchIO = FileSearchIO

__all__ = ["IO", "SearchIO", "NLUFileIO", "FileSearchIO"]
