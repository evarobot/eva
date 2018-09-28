# coding=utf-8
import json
import os
import requests

from evecms.services.service import EVECMSService
from vikidm.config import ConfigNLU

PROJECT_DIR = os.path.realpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '../../'))

cms_rpc = EVECMSService()


def nlu_predict(domain_id, context, question):
    """ Call NLU module for semantic parsing.

    """
    params = {
        'context': context,
        'question': question
    }
    headers = {'content-type': 'application/json'}
    nlu_url = ConfigNLU.predict_url.format(domain_id)
    data = requests.post(nlu_url,
                         data=json.dumps(params),
                         headers=headers,
                         timeout=ConfigNLU.request_timeout)
    assert(data.status_code == 200)
    return json.loads(data.text)


def nlu_train(domain_id):
    """ Call NLU module for training.

    """
    nlu_url = ConfigNLU.train_url.format(domain_id)
    data = requests.get(nlu_url, timeout=10)
    assert(data.status_code == 200)
    return json.loads(data.text)
