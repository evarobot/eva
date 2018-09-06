# coding=utf-8
import json
import os
import requests

from evecms.services.service import EVECMSService

PROJECT_DIR = os.path.realpath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '../../'))

cms_rpc = EVECMSService()


def nlu_predict(domain_id, context, question):
    """ Call NLU module for semantic parsing.

    Parameters
    ----------
    domain_id :  TODO
    context : TODO
    question : TODO

    Returns
    -------
    TODO

    """
    params = {
        'context': context,
        'question': question
    }
    headers = {'content-type': 'application/json'}
    nlu_url = "http://127.0.0.1:5000/v2/nlu/{0}/predict".format(domain_id)
    json_data = requests.post(nlu_url,
                              data=json.dumps(params),
                              headers=headers,
                              timeout=10).text
    rst = json.loads(json_data)
    return rst


def nlu_train(domain_id):
    """ Call NLU module for training.

    Parameters
    ----------
    domain_id :  TODO

    Returns
    -------
    TODO

    """
    nlu_url = "http://127.0.0.1:5000/v2/nlu/{0}/train".format(domain_id)
    json_data = requests.get(nlu_url, timeout=10).text
    rst = json.loads(json_data)
    return rst
