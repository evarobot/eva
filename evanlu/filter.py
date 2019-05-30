#!/usr/bin/env python
# encoding: utf-8
#from evanlu.model import IntentQuestion


class NonSenseFilter(object):
    """
    Detect nonsense question.
    """
    def __init__(self, io):
        self._words = []
        self._filter_length = 2
        self._io = io

    @staticmethod
    def get_filter(io):
        """
        Create and return an NonSense object.
        """
        nonsense = NonSenseFilter(io)
        nonsense.init_words()
        return nonsense

    def init_words(self):
        """ Initialize nonsense words

        """
        self._words = self._io.get_not_nonsense_words()

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


class SensitiveFilter(object):
    """
    Detect sensitive words from question.
    """
    def __init__(self, io):
        self._words = []
        self._io = io

    @staticmethod
    def get_filter(io):
        sensitive = SensitiveFilter(io)
        sensitive.init_words()
        return sensitive

    def init_words(self):
        """ Initialize sensitive  words

        """
        self._words = self._io.get_sensitive_words()

    def detect(self, question):
        """ Check if question contains sensitive words.

        Parameters
        ----------
        question : str
            Dialogue text.

        Returns
        -------
        weather question contain sensitive words : boolean

        """
        for word in self._words:
            if word in question:
                return True
        return False
