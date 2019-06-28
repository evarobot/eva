#!/usr/bin/env python
# encoding: utf-8
import logging
log = logging.getLogger(__name__)


class Stack(object):
    """
     模拟栈
    """
    def __init__(self):
        self._items = []

    @property
    def items(self):
        """ items in the stack

        """
        return self._items

    def is_empty(self):
        """ If there are items in the stack return True,
        else return False

        Returns
        -------
        Boolean.

        """
        return self._items == []

    def push(self, item):
        """ Push an item to stack.

        """
        self._items.append(item)

    def pop(self):
        """ Pop an item from stack and return it.

        If none item exist, raise IndexError.

        """
        try:
            return self._items.pop()
        except IndexError:
            log.error("root node always in stack")
            raise IndexError

    def top(self):
        """ Return the top item of stack.

        If none item exist, raise IndexError.

        """
        try:
            return self._items[-1]
        except IndexError:
            log.error("root node always in stack")
            raise IndexError

    def __len__(self):
        return len(self._items)

    def __str__(self):
        return "\n                ".join(
            ["\n            Stack:"] + ["{0}({1})".format(c.tag, c.state)
                                        for c in self._items])

    def __repr__(self):
        name = self.__class__.__name__
        items = "\n".join([c.tag for c in self._items])
        kwargs = [
            "items=[\n{0}\n]".format(items)
        ]
        return "%s(%s)" % (name, ", ".join(kwargs))




