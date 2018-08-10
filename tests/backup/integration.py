#!/usr/bin/env python
# encoding: utf-8

import logging
import mongoengine
import mock

from vikicommon.log import init_logger
from vikinlu.config import ConfigMongo
from vikinlu.filters import Sensitive
from vikinlu.slot import SlotRecognizer
from vikinlu.service import NLUService
from vikinlu.util import cms_rpc
from vikinlu.intent import IntentRecognizer
import util as db
from evecms.models import (
    Domain,
    Slot
)

init_logger(level="DEBUG", path="./")
log = logging.getLogger(__name__)
dm_robot_id = "12345"

mongoengine.connect(db=ConfigMongo.database,
                    host=ConfigMongo.host,
                    port=ConfigMongo.port)
log.info('连接Mongo开发测试环境[eve数据库]成功!')
db.clear_intent_question("C")


def test_integration_train():
    service = NLUService()
    domain = Domain.objects.get(name="C")
    service.train(str(domain.pk), ("logistic", "0.1"))
    label_data = cms_rpc.get_tree_label_data(str(domain.pk))
    db.assert_intent_question(str(domain.pk), label_data)



def atest_intent():
    domain_id = "C"
    intent = IntentRecognizer.get_intent_recognizer(domain_id)
    mock_context = []
    for data in mock_label_data:
        tr, intent, question = q
        assert(intent == intent.strict_classify(mock_context, question)[0])
    mock_fuzzy_result = []
    for data in mock_fuzyy_result:
        tr, intent, question = q
        assert(intent == intent.fuzzy_classify(mock_context, question)[0])



# TODO: casual talk test

if __name__ == '__main__':
    assert(False)
