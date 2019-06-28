#!/usr/bin/env python
# encoding: utf-8
from evanlu.util import cms_gate
from evanlu.model import IntentQuestion


class NonSense(object):
    """
    Detect nonsense question.
    """
    def __init__(self):
        self._words = set([u'你好', u'晚安'])
        self._filter_length = 2

    @classmethod
    def get_nonsense(self, domain_id):
        """
        Create and return an NonSense object.
        """
        nonsense = NonSense()
        nonsense.init_words(domain_id)
        return nonsense

    def init_words(self, domain_id):
        """ Initialize nonsense words

        Parameters
        ----------
        domain_id : str, Project id.

        """
        for obj in IntentQuestion.objects(domain=domain_id):
            if len(obj.question) <= self._filter_length:
                self._words.add(obj.question)

    def detect(self, question):
        """ Check if question is nonsense text.

        Parameters
        ----------
        question : str, Dialogue text.

        Returns
        -------
        boolean

        """
        if len(question) <= self._filter_length and\
                question not in self._words:
            return True
        return False


class Sensitive(object):
    """
    Detect sensitive words from question.
    """
    def __init__(self):
        self._words = []

    @classmethod
    def get_sensitive(self, domain_id):
        sensitive = Sensitive()
        sensitive.init_words(domain_id)
        return sensitive

    def init_words(self, domain_id):
        """ Initialize sensitive  words

        Parameters
        ----------
        domain_id : str, Project id.

        """
        rst = cms_gate.get_filter_words(domain_id)
        self._words = rst['data']['words']

    def detect(self, question):
        """ Check if question contains sensitive words.

        Parameters
        ----------
        question : str, Dialogue text.

        Returns
        -------
        boolean

        """
        for word in self._words:
            if word in question:
                return True
        return False
