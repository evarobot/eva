#!/usr/bin/env python
# encoding: utf-8

import logging
import os

from collections import namedtuple
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


LabeledData = namedtuple("LabeledData", "label question node_id")


def _create_mock_context(mock_label_data):
    mock_context = {}
    context_list = set([(intent, intent, treenode_id) for intent, question, treenode_id in mock_label_data])
    mock_context["agents"] = list(context_list)
    return mock_context


TEST_PROJECT = "project_cn_test"
file_io = NLUFileIO(TEST_PROJECT)
file_io._project_path = os.path.join(
    PROJECT_DIR, "tests", "data", "projects", TEST_PROJECT)
file_io._sys_path = os.path.join(
    PROJECT_DIR, "tests", "data", "projects", "sys")


def test_file_io():
    sensitive_words = file_io.get_sensitive_words()
    assert(set(sensitive_words) == set(["共产党", "毛泽东", "法轮功"]))

    not_nonsense_words = file_io.get_not_nonsense_words()
    assert(set(not_nonsense_words) == set(["你好", "晚安"]))

    entities = file_io.get_entities_with_value()
    target = {
        'city': {
            '北京': ['帝都', '北京'],
            '上海': ['魔都', '上海']
        },
        '@sys.city': {
            '北京': ['帝都', '北京'],
            '上海': ['魔都', '上海'],
            '深圳': ['鹏城', '深圳']
        },
        'meteorology': {
            '晴': ['晴'],
            '雨': ['雨']
        }
    }
    assert same_dict(target, entities)


def test_file_search_io():
    labeled_data = [
        LabeledData("weather.query", "帮我看看去北京的航班有哪些", "node1"),
        LabeledData("weather.query", "帮我看看去北京的航班有哪些", "node2"),
        LabeledData("name.query", "你叫什么名字", "node3"),
        LabeledData("name.query", "你叫什么名字", "node4")
    ]
    search_io = FileSearchIO(TEST_PROJECT)
    search_io.save(labeled_data)
    assert search_io._caches == {}
    l_intent_node = search_io.search("你叫什么名字")
    assert l_intent_node == [
        ('name.query', 'node3'),
        ('name.query', 'node4'),
    ]
    assert search_io._caches != {}
    l_intent_node = search_io.search("什么名字")
    assert l_intent_node == []


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
    result = recognizer.recognize("深圳会下雨吗", ["city", "meteorology"])
    assert(same_dict(result, {
        "meteorology": "雨"
    }))
    result = recognizer.recognize("深圳会下雨吗", ["@sys.city", "meteorology"])
    assert(same_dict(result, {
        "meteorology": "雨",
        "@sys.city": "深圳"
    }))


def test_intent_recoginizer():
    recognizer = IntentRecognizer.get_intent_recognizer(file_io)
    words = recognizer.add_custom_words_to_jieba()
    target = {'魔都', '帝都', '北京', '上海', '晴', '雨', '深圳', '鹏城'}
    assert(words == target)
    labeled_data = [
        LabeledData("weather.query", "帮我看看去北京的航班有哪些", "node1"),
        LabeledData("weather.query", "帮我看看去北京的航班有哪些", "node2"),
        LabeledData("name.query1", "你叫什么名字", "node3"),
        LabeledData("name.query2", "你叫什么名字", "node4")
    ]
    context = [
        ("name.query2", "name.query2", "node4"),
        ("name.query1", "name.query1", "node3")
    ]
    recognizer.train(labeled_data)
    l_label_data = recognizer.strict_classify(context, "你叫什么名字")
    # TODO NLURobot.intent_classify 移动到Intent中，把Context参数细化成必须的的字段。
    import pdb
    pdb.set_trace()



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
