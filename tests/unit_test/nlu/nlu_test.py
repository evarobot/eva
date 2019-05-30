#!/usr/bin/env python
# encoding: utf-8

import logging
from collections import namedtuple
import os

from evashare.log import init_logger
from evashare.util import same_dict
from evanlu.io import NLUFileIO, FileSearchIO
from evanlu.config import ConfigLog
from evanlu.filter import SensitiveFilter, NonSenseFilter
from evanlu.entity import EntityRecognizer
from evanlu.intent import IntentRecognizer
from evanlu.robot import NLURobot
from evanlu.util import PROJECT_DIR

init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)


def _create_mock_context(mock_label_data):
    mock_context = {}
    context_list = set([(intent, intent, treenode_id) for intent, question, treenode_id in mock_label_data])
    mock_context["agents"] = list(context_list)
    return mock_context


TEST_PROJECT = "project_cn_test"
file_io = NLUFileIO(TEST_PROJECT)
file_io._project_path = os.path.join(
    PROJECT_DIR, "data", "projects", TEST_PROJECT)


def test_file_io():
    sensitive_words = file_io.get_sensitive_words()
    assert(set(sensitive_words) == set(["共产党", "毛泽东", "法轮功"]))

    not_nonsense_words = file_io.get_not_nonsense_words()
    assert(set(not_nonsense_words) == set(["你好", "晚安"]))

    entities = file_io.get_entities_with_value()
    target = {'city': {'北京': ['帝都', '北京'], '上海': ['魔都', '上海']}}
    assert same_dict(target, entities)

def test_file_search_io():
    return
    search_io = FileSearchIO(TEST_PROJECT)


def test_sensitive():
    sensitive = SensitiveFilter.get_filter(file_io)
    assert(set(sensitive._words) == set(["共产党", "毛泽东", "法轮功"]))
    assert(sensitive.detect('共产党万岁') == True)
    assert(sensitive.detect('你叫什么') == False)


def test_nonsense():
    nonsense = NonSenseFilter.get_filter(file_io)
    assert(nonsense.detect('啊'))
    assert(not nonsense.detect('晚安'))


def test_entity_recognizer():
    recognizer = EntityRecognizer.get_entity_recognizer(file_io)
    result = recognizer.recognize("北京在哪里", ["city"])
    target = {'city': '北京'}
    assert(result == target)
    result = recognizer.recognize("帝都在哪里", ["city"])
    assert(result == target)
    result = recognizer.recognize("深圳在哪里", ["city"])
    assert(result == {})


def test_intent_recoginizer():
    recognizer = IntentRecognizer.get_intent_recognizer(file_io)
    words = recognizer.add_custom_words_to_jieba()
    target = {'魔都', '帝都', '北京', '上海'}
    assert(words == target)


class aTestClassifier(object):
    nlurobot = None

    def test_train(self):
        TestClassifier.nlurobot = NLURobot.get_robot(TEST_PROJECT)
        return
        TestClassifier.nlurobot.train(("logistic", "0.1"))
        assert_intent_question(domain_id, mock_label_data)

    def test_intent(self):
        return
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
