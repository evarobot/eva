#!/usr/bin/env python
# encoding: utf-8
import logging
from evanlp.ner import KeyWordEntity
log = logging.getLogger(__name__)


class EntityRecognizer(object):
    """
    Detect entities from dialogue text.

    Attributes
    ----------
    _entities : dict,
        Slots and related value, like:
            {
                "entity_name1": {
                    "value_name1": ["word1", "word2", ..],

                    "value_name2": ["word1", "word2", ..]
                },

                "entity_name2": {
                    "value_name1": ["word1", "word2", ..],

                    "value_name2": ["word1", "word2", ..]
                }
            }
    _detector_funcs : dict,
        dict of entity detect function.
    """
    def __init__(self, io):
        self._entities = {}
        self._detector_funcs = {}
        self._io = io

    def init_entities(self):
        def detect(text):
            return []
        result = self._io.get_entities_with_value()
        self._entities = result["entities"]
        name_space = {}
        for name, script in result["scripts"].items():
            code = compile(script, name, "exec")
            exec(code, name_space)
            func = name_space.get("detect", None)
            if name in self._detector_funcs:
                log.warning("重复的脚本名 :{0}".format(name))
            self._detector_funcs[name] = func

    @staticmethod
    def get_entity_recognizer(io):
        entity = EntityRecognizer(io)
        entity.init_entities()
        return entity

    def recognize(self, question, entity_names):
        """

        Parameters
        ----------
        question : str, Dialogue text.
        entity_names : [str], Name of target entities to detect.

        Returns
        -------
        dict.

        """
        entities = {}
        for entity_name in entity_names:
            if entity_name in self._entities:
                values = self._entities[entity_name]
                for value_name, value_pattern in values.items():
                    ret = KeyWordEntity.recognize(question, value_pattern)
                    if ret:
                        entities[entity_name] = value_name
            else:
                detect_func = self._detector_funcs[entity_name]
                value = detect_func(question)
                if value is not None:
                    entities[entity_name] = value

        return entities
