#!/usr/bin/env python
# encoding: utf-8

import logging
import mongoengine
import mock
import copy
from collections import namedtuple
import os

from evashare.log import init_logger
from eva.evanlu import IntentQuestion
from eva.evanlu import remove_stopwords
from eva.evanlu.config import ConfigMongo, ConfigLog
from eva.evanlu import Sensitive
from eva.evanlu.slot import SlotRecognizer
from eva.evanlu import NLURobot
from eva.evanlu.util import cms_gate, PROJECT_DIR
from eva.evanlu import clear_intent_question

LabelData = namedtuple("LabelData", "label, question, treenode")
init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)
dm_robot_id = "12345"

mongoengine.connect(db=ConfigMongo.db,
                    host=ConfigMongo.host,
                    port=ConfigMongo.port)
log.info('连接Mongo开发测试环境[eve数据库]成功!')


def assert_intent_question(domain_id, label_data):
    intent_questions = IntentQuestion.objects(domain=domain_id)
    db_data = set()
    for db_obj in intent_questions:
        db_data.add((db_obj.treenode, db_obj.label,
                     db_obj.question))
    for tuple_obj in label_data:
        tuple_obj = (int(tuple_obj.treenode), tuple_obj.label,
                     remove_stopwords(tuple_obj.question))
        assert(tuple_obj in db_data)


def mock_get_slot_values_for_nlu(slot_id):
    data = {
        'code': 0,
        'data': {
            'values': [
                {
                    'name': '周黑鸭',
                    'words': ['鸭鸭', '鸭翅', '-小鸭鸭', '-小鸭翅'],
                    'update_time': '2018-03-03'
                },

                {
                    'name': '耐克',
                    'words': ['耐克'],
                    'update_time': '2018-03-03'
                }
            ]
        }
    }
    return data


def _create_mock_label_data():
    path1 = os.path.join(PROJECT_DIR, "tests/data/guangkai.txt")
    mock_label_list = list()
    with open(str(path1), "r") as f:
        i = 1
        item_copy = f.readline().strip().split("$@")
        lines = f.readlines()
    for line in lines:
        item = line.strip().split("$@")
        if item[0] == item_copy[0]:
            pass
        else:
            i += 1
        item_copy = copy.deepcopy(item)
        item.insert(0, str(i))
        u_item = map(lambda x:x, item)
        u_item = tuple(u_item)
        mock_label_list.append(LabelData(treenode=u_item[0],
                                         label=u_item[1],
                                         question=u_item[2]))
    return mock_label_list

mock_label_data = _create_mock_label_data()

cms_gate.get_tree_label_data = mock.Mock(
    return_value=mock_label_data)

cms_gate.get_filter_words = mock.Mock(return_value={
    'code': 0,
    'data': {
        'words': ["共产党", "毛泽东", "法轮功"]
    }
})

cms_gate.get_domain_slots = mock.Mock(return_value={
    'code': 0,
    'slots': [
        {
            'name': 'location',
            'id': 'slot_id',
            'values': {
                'id1': '周黑鸭',
                'id2': '耐克'
            }
        }
    ]
})

cms_gate.get_slot_values_for_nlu = mock.Mock(
    side_effect=mock_get_slot_values_for_nlu)

cms_gate.get_domain_values = mock.Mock(return_value={
    'code': 0,
    'values': [
        {
            'id': 'id1',
            "name": '周黑鸭',
            "words": ['鸭鸭', '鸭翅', '-小鸭鸭', '-小鸭翅'],
        },
        {
            'id': 'id2',
            "name": '耐克',
            "words": [],
        }
    ]
})


def _create_mock_context(mock_label_data):
    mock_context = {}
    context_list = set([(intent, intent, treenode_id) for intent, question, treenode_id in mock_label_data])
    mock_context["agents"] = list(context_list)
    return mock_context


def test_sensitive():
    domain_id = "C"
    sensitive = Sensitive.get_sensitive(domain_id)
    assert(set(sensitive._words) == set(["共产党", "毛泽东", "法轮功"]))
    assert(sensitive.detect('共产党万岁') == True)
    assert(sensitive.detect('你叫什么') == False)


def test_slot_recognizer():
    domain_id = "C"
    slot = SlotRecognizer.get_slot_recognizer(domain_id)
    where_query = [
        '耐克店怎么走？',
    ]
    where_query2 = [
        '周黑鸭怎么走？',
        '鸭鸭怎么走？',
        '鸭翅怎么走？',
        '小鸭鸭怎么走？',
        '小鸭翅怎么走？',
    ]
    name_query = [
        '你叫什么名字',
    ]
    for question in where_query:
        ret = slot.recognize(question, ['location'])
        assert(ret == {"location": "耐克"})
    for question in where_query2:
        ret = slot.recognize(question, ['location'])
        if '小鸭鸭' in question or '小鸭翅' in question:
            assert(ret == {})
        else:
            assert(ret == {"location": u"周黑鸭"})
    for question in name_query:
        ret = slot.recognize(question, ['location'])
        assert(ret == {})


def test_nonsense():
    #  TODO:  <03-05-18, yourname> #
    pass


class TestClassifier(object):
    nlurobot = None

    def test_train(self):
        clear_intent_question("C")
        domain_id = "C"
        TestClassifier.nlurobot = NLURobot.get_robot(domain_id)
        TestClassifier.nlurobot.train(("logistic", "0.1"))
        assert_intent_question(domain_id, mock_label_data)

    def test_intent(self):
        self.mock_context = _create_mock_context(mock_label_data)
        self.domain_id = "C"
        self.intent = TestClassifier.nlurobot._intent
        for data in mock_label_data:
            predicted_label = self.intent.strict_classify(self.mock_context,
                                                          data.question)[0]
            if predicted_label != data.label:
                # filtered by priority
                assert(predicted_label == '信用卡什么时候还款')
            else:
                assert(predicted_label == data.label)

        # biz_classifier
        count = 0.0
        for data in mock_label_data:
            predicted = self.intent._biz_classifier.predict(data.question)[0][0]
            if predicted.label == data.label:
                count += 1
        log.info(
            "Biz Classify Precise: {0}".format(count / len(mock_label_data)))
        assert(count >= 0.9)

        # biz vs casual_talk
        count = 0.0
        for data in mock_label_data:
            predicted = self.intent._biz_chat_classifier.predict(data.question)[0][0]
            if predicted.label == 'biz':
                count += 1
        log.info("Biz vs. Chat Precise: {0}".format(count/len(mock_label_data)))

        ## fuzytest
        count = 0.0
        for data in mock_label_data:
            predicted_label = self.intent.fuzzy_classify(self.mock_context, data.question)[0]
            if predicted_label == data.label:
                count += 1
        log.info("Total Precise: {0}".format(count/len(mock_label_data)))
        clear_intent_question("C")



if __name__ == '__main__':
    test_slot_recognizer()
    test_sensitive()
    test_case = TestClassifier()
    test_case.test_train()
    test_case.test_intent()
    assert(True)
