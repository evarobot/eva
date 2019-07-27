import os
from evashare.util import same_dict
from evanlu.io import NLUFileIO, FileSearchIO
from evanlu.testing import LabeledData
from evanlu.util import PROJECT_DIR


TEST_PROJECT = "project_cn_test"
file_io = NLUFileIO(TEST_PROJECT)
file_io._project_path = os.path.join(
    PROJECT_DIR, "tests", "data", "projects", TEST_PROJECT)
file_io._sys_path = os.path.join(
    PROJECT_DIR, "tests", "data", "projects", "sys")


def test_file_io():
    sensitive_words = file_io.get_sensitive_words()
    assert(set(sensitive_words) == {"共产党", "毛泽东", "法轮功"})

    not_nonsense_words = file_io.get_not_nonsense_words()
    assert(set(not_nonsense_words) == {"你好", "晚安"})

    rst = file_io.get_entities_with_value()
    entities = rst["entities"]
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
    scripts = rst["scripts"]
    sys_script_path = os.path.join(PROJECT_DIR, "tests", "data",
                                   "projects", "sys", "entity", "date.py")
    script_path = os.path.join(PROJECT_DIR, "tests", "data",
                               "projects", "project_cn_test",
                               "entity", "date.py")
    with open(sys_script_path, "r") as file:
        sys_script = file.read()
    with open(script_path, "r") as file:
        script = file.read()
    assert scripts == {
        "@sys.date": sys_script,
        "date": script,
    }

    rst = file_io.get_label_data()
    target = set(
        LabeledData("weather.query", "帮我查一下北京今天的天气"),
        LabeledData("weather.query", "深圳明天会下雨吗"),
        LabeledData("weather.query", "今天什么天气"),
        LabeledData("airline.query", "帮我查一下从北京到上海的航班"),
        LabeledData("airline.query", "帮我看看去北京的航班有哪些")
    )
    assert set(rst) == target


def test_file_search_io():
    labeled_data = [
        LabeledData("weather.query", "帮我看看去北京的航班有哪些"),
        LabeledData("name.query", "你叫什么名字")
    ]
    search_io = FileSearchIO(TEST_PROJECT)
    search_io.save(labeled_data)
    assert search_io._caches == {}
    l_intent_node = search_io.search("你叫什么名字")
    assert l_intent_node == ["name.query"]
    assert search_io._caches != {}
    l_intent_node = search_io.search("什么名字")
    assert l_intent_node == []
