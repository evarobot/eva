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
    _entities : dict, Slots and related value, like:
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
    """
    def __init__(self, io):
        self._entities = {}
        self._io = io

    def init_entities(self):
        self._entities = self._io.get_entities_with_value()

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
            values = self._entities[entity_name]
            for value_name, value_pattern in values.items():
                ret = KeyWordEntity.recognize(question, value_pattern)
                if ret:
                    entities[entity_name] = value_name
        return entities
