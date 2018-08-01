# coding=utf-8
import logging
from json import JSONEncoder

log = logging.getLogger(__name__)


class Concept(JSONEncoder):
    """
    概念类，包含键值对。
    """
    LIFE_STACK = "LIFE_STACK"

    def __init__(self, key, value=None, life_type="LIFE_STACK"):
        self._key = key
        self._value = value
        self.life_type = life_type

    def default(self, o):
        return o.__dict__

    @property
    def key(self):
        return self._key

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = v
        if hasattr(self, '_hash'):
            self._hash = hash(str(self))

    @property
    def dirty(self):
        return self.value is not None

    def __unicode__(self):
        return u"Concept({0}={1})".format(self.key, self.value)

    def __str__(self):
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
    """ System have one context instance,
    which is used to manage a set of concepts(Memory).

    Attributes
    ----------
    _all_concepts : dict, {"key1": concept1, "key2": concept2}

    """

    def __init__(self):
        self._all_concepts = {}

    def add_concept(self, concept):
        """ Add one concept instance to memory.

        Parameters
        ----------
        concept : Concept, Concept instance

        """
        concept.value = None
        self._all_concepts[concept.key] = concept

    def update_concept(self, key, concept):
        """ Update specific concept.

        Parameters
        ----------

        key : str, key of target concept.
        concept : Concept, Concept instance.

        """
        assert(key == concept.key)
        if key not in self._all_concepts:
            log.error("不存在概念{0}".format(key))
            return
        self._all_concepts[key] = concept

    def reset_concept(self, key):
        """ Set specific concept with `None` value.

        Parameters
        ----------
        key : str, used to identify concept.

        """
        concept = self._all_concepts.get(key, None)
        if concept:
            concept.value = None
            return
        log.error("不存在概念{0}".format(key))

    def get_concept(self, key):
        """ Get specific concept by string key.

        Parameters
        ----------
        key : str, used to identify concept.

        """
        return self._all_concepts[key]

    def __getitem__(self, key):
        return self._all_concepts[key]

    def satisfied(self, concept):
        """ Check if memory have a concept equal to target concept.

        Parameters
        ----------
        concept: Concept, target comparing concept.

        """
        target = self._all_concepts.get(concept.key, None)
        if target is None:
            return False
        if target.dirty and concept.value.startswith("@") or\
                target == concept:
            return True
        return False

    def dirty(self, key):
        """ Check if value of specific concept is asigned.

        Parameters
        ----------
        key : str, key of specific concept.

        """
        target = self._all_concepts.get(key, None)
        if target and target.dirty:
            return True
        return False

    def __str__(self):
        concepts = []
        for key in sorted(self._all_concepts.iterkeys()):
            concepts.append(self._all_concepts[key])
        return "\n                ".join(["\n            Context:"] +
                                         [str(c) for c in concepts])

    def __repr__(self):
        return self.__str__()
