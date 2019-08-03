#!/usr/bin/env python
# encoding: utf-8
import logging
import jieba

from evanlu.classifier import (
    QuestionSearch,
    FuzzyClassifier,
    BizChatClassifier
)

log = logging.getLogger(__name__)


class IntentRecognizer(object):
    """
    Recognize intent from question.

    Attributes
    ----------
    custom_words : set, Custom words added to Tokenizer.
    _biz_chat_classifier : BizChatClassifier, Classify question to business or
        casual_talk.
    _biz_classifier : FuzzyClassifier, Classify
    """
    custom_words = set()

    def __init__(self, io):
        self._feature = None
        self._strict_classifier = QuestionSearch(io.domain_id)
        self._biz_classifier = FuzzyClassifier(io.domain_id, "logistic")
        self._biz_chat_classifier = BizChatClassifier(io.domain_id, "logistic")
        self._io = io

    @staticmethod
    def get_intent_recognizer(io):
        intent = IntentRecognizer(io)
        intent.add_custom_words_to_jieba()
        return intent

    def add_custom_words_to_jieba(self):
        """ add custom words to jieba"""
        value_words = []
        entities = self._io.get_entities_with_value()["entities"]
        for name, values in entities.items():
            for words in values.values():
                value_words += words
        value_words = set(value_words)
        for word in value_words:
            if word not in self.custom_words:
                self.custom_words.add(word)
                jieba.add_word(word, freq=10000)
        return self.custom_words

    def train(self, label_data):
        """ Save Normalized question to database and train quetions to
        algorithm model.

        Parameters
        ----------
        label_data : [(label, question, treenode), ..], Labeld question.

        Returns
        -------
        {
            "intents": [

                "label": 意图标识,

                "count": 问题数量,

                "precise": 准去率,

            ]

            "total_prciese": 业务准确率

        }

        """
        self._strict_classifier.train(label_data)
        return {}
        biz_statics = self._biz_classifier.train(label_data)
        biz_chat_statics = self._biz_chat_classifier.train(label_data)
        label_question = {}
        label_question_count = {}
        for record in label_data:
            label_question.setdefault(record[0], record[1])
            count = label_question_count.get(record[0], 0)
            count += 1
            label_question_count[record[0]] = count
        ret = {
            "total_prciese": float(biz_statics['total_precise']) * float(biz_chat_statics['total_precise']),
            "intents": [
                {
                    "label": "业务",
                    "count": len(label_question_count.keys()),
                    "pricise": biz_statics["total_precise"]
                },
                {
                    "label": "闲聊",
                    "count": 500,
                    "pricise": biz_chat_statics["total_precise"]
                }
            ]
        }
        for label, precise in biz_statics["class_precise"].items():
            ret["intents"].append({
                "label": label,
                "count": label_question_count[label],
                "precise": precise
            })
        return ret

    def strict_classify(self, context, question):
        """ Classify question by database quering, given specific context.

        Parameters
        ----------
        context : dict, Context information from DM, used to filter invisible
                        agents.
        question : str, Dialogue text from user.

        Returns
        -------
        (label, confidence, node_id) : (str, float, int)

        """
        objects, confidence = self._strict_classifier.predict(question)
        if objects:
            log.info("STRICTLY CLASSIFY to [{0}]".format(objects[0]))
        intent, node_id = self._get_valid_intent(context, objects)
        if objects and intent is None:
            log.info("FILTERED INTENT: [{0}]".format(objects[0]))
        return intent, confidence, node_id

    def rule_classify(self, context, question):
        confidence = 1
        objects = []
        if "查" in question:
            objects = ["search"]
        if objects:
            log.info("STRICTLY CLASSIFY to [{0}]".format(objects[0]))
        intent, node_id = self._get_valid_intent(context, objects)
        return intent, confidence, node_id

    def fuzzy_classify(self, context, question):
        """ Classify question by algorithm model, given specific context.

        Parameters
        ----------
        context : dict, Context information from DM, used to filter invisible
                        agents.
        question : str, Dialogue text from user.

        Returns
        -------
        (label, confidence, node_id) : (str, float, int)

        """
        objects, confidence = self._biz_chat_classifier.predict(question)
        if len(objects) == 0 or objects[0].label == 'casual_talk':
            return('casual_talk', confidence, None)
        objects, confidence = self._biz_classifier.predict(question)
        label, node_id = self._get_valid_intent(context, objects)
        return(label, confidence, node_id)

    def _get_valid_intent(self, context, intents):
        """
        Filter intents agents by context, ending with one label.
        """
        if not intents:
            return None, None
        for unit in context:
            for intent in intents:
                # TODO remove useless tag filed
                tag, intent_, node_id_ = tuple(unit)
                if intent == intent_:
                    return intent, node_id_
        log.info("NO VISIBLE AGENTS SATISFIED!")
        return None, None
