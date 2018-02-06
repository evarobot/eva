# coding=utf-8
# Copyright (C) 2017 AXMTEC.
# https://axm.ai/

from vikicommon.log import gen_log as log
from json import JSONEncoder


class Concept(JSONEncoder):
    """
    """
    def __init__(self, key, value=None, life_type=None):
        self.key = key
        self.value = value
        self.life_type = life_type

    def default(self, o):
        return o.__dict__

    @property
    def is_dirty(self):
        return self.value is not None

    def __unicode__(self):
        return u"Concept({0}={1})".format(self.key, self.value)

    def __str__(self):
        # return json.dumps(self, default=lambda o: o.__dict__)
        return unicode(self).encode('utf8')

    def __hash__(self):
        if hasattr(self, '_hash'):
            return self._hash
        self._hash = hash(str(self))
        return self._hash

    def __eq__(self, r):
        try:
            return self._hash == r._hash
        except AttributeError:
            return hash(self) == hash(r)


class Context(object):
    """"""
    def __init__(self):
        self._all_concepts = {}

    def add_concept(self, concept):
        """
        添加业务配置中的触发条件。
        """
        concept.value = None
        self._all_concepts[concept.key] = concept

    def update_concept(self, key, concept):
        assert(key == concept.key)
        if key not in self._all_concepts:
            log.warning("不存在概念{0}".format(key))
            return
        self._all_concepts[key] = concept

    def reset_concept(self, key):
        concept = self._all_concepts.get(key, None)
        if concept:
            concept.value = None
            return
        log.warning("不存在概念{0}".format(key))

    def get_concept(self, key):
        return self._all_concepts[key]

    def satisfied(self, concept):
        target = self._all_concepts.get(concept.key, None)
        if target and target == concept:
            return True
        return False

    def is_dirty(self, concept):
        target = self._all_concepts.get(concept.key, None)
        if target and target.is_dirty:
            return True
        return False

    def __str__(self):
        clean_concepts = []
        dirty_concepts = []
        for concept in self._all_concepts.values():
            if not concept.is_dirty:
                clean_concepts.append(concept)
            else:
                dirty_concepts.append(concept)
        return "\n".join(["Context:"] + [str(c) for c in dirty_concepts + clean_concepts])
