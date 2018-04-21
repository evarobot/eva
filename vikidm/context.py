# coding=utf-8
# Copyright (C) 2017 AXMTEC.
# https://axm.ai/

import logging
from json import JSONEncoder

log = logging.getLogger(__name__)


class Concept(JSONEncoder):
    """
    """
    LIFE_STACK = "LIFE_STACK"

    def __init__(self, key, value=None, life_type="LIFE_STACK"):
        self.key = key
        self.value = value
        self.life_type = life_type

    def default(self, o):
        return o.__dict__

    @property
    def dirty(self):
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

    def __repr__(self):
        return self.__unicode__()


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
            log.error("不存在概念{0}".format(key))
            return
        self._all_concepts[key] = concept

    def reset_concept(self, key):
        concept = self._all_concepts.get(key, None)
        if concept:
            concept.value = None
            return
        log.error("不存在概念{0}".format(key))

    def get_concept(self, key):
        return self._all_concepts[key]

    def satisfied(self, concept):
        target = self._all_concepts.get(concept.key, None)
        if target and target == concept or (concept.value == "*" and target.dirty):
            return True
        return False

    def dirty(self, concept):
        target = self._all_concepts.get(concept.key, None)
        if target and target.dirty:
            return True
        return False

    def __getitem__(self, key):
        return self._all_concepts[key]

    def __str__(self):
        concepts = []
        for key in sorted(self._all_concepts.iterkeys()):
            concepts.append(self._all_concepts[key])
        return "\n                ".join(["\n            Context:"] + [str(c) for c in concepts])

    def __repr__(self):
        return self.__str__()
