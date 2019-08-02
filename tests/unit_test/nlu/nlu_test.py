#!/usr/bin/env python
# encoding: utf-8

import logging
import os

from evanlu import util
util.PROJECT_DIR = os.path.join(util.PROJECT_DIR, "tests")
from evashare.util import same_dict
from evanlu.config import ConfigLog
from evanlu.entity import EntityRecognizer
from evanlu.filter import SensitiveFilter, NonSenseFilter
from evanlu.intent import IntentRecognizer
from evanlu.io import NLUFileIO
from evashare.log import init_logger
from evanlu.util import PROJECT_DIR
from evanlu.testing import LabeledData


init_logger(level="DEBUG", path=ConfigLog.log_path)
log = logging.getLogger(__name__)


TEST_PROJECT = "project_cn_test"
file_io = NLUFileIO(TEST_PROJECT)


def test_sensitive():
    sensitive = SensitiveFilter.get_filter(file_io)
    assert set(sensitive._words) == {"共产党", "毛泽东", "法轮功"}
    assert sensitive.detect('共产党万岁')
    assert not sensitive.detect('你叫什么')


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
    result = recognizer.recognize("深圳今天会下雨吗", ["@sys.date"])
    assert result == {
        "@sys.date": "今天"
    }


def test_intent_recognizer():
    recognizer = IntentRecognizer.get_intent_recognizer(file_io)
    words = recognizer.add_custom_words_to_jieba()
    target = {'魔都', '帝都', '北京', '上海', '晴', '雨', '深圳', '鹏城'}
    assert(words == target)
    labeled_data = [
        LabeledData("weather.query", "帮我看看去北京的航班有哪些"),
        LabeledData("name.query", "你叫什么名字")
    ]
    context = [
        ("name.query", "name.query", "node4"),
        ("name.query", "name.query", "node3")
    ]
    recognizer.train(labeled_data)
    result = recognizer.strict_classify(context, "你叫什么名字")
    assert result == ('name.query', 1, 'node4')


if __name__ == '__main__':
    assert(False)
