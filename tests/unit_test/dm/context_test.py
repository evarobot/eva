#!/usr/bin/env python
# encoding: utf-8
import copy
from evadm.context import Slot
from evadm.context import Context


class TestContext(object):
    """"""

    def test_context(self):
        c1 = Slot("intent", "location.query")
        c2 = Slot("intent", "name.query", life_type="forever")
        c3 = Slot("location", "nike")
        c4 = Slot("date", "today")
        ctx = Context()

        ctx.add_slot(copy.deepcopy(c1))
        ctx.update_slot("intent", copy.deepcopy(c2))
        ctx.add_slot(copy.deepcopy(c3))
        ctx.add_slot(copy.deepcopy(c4))
        assert ctx["intent"].dirty
        assert not ctx["location"].dirty
        assert ctx.satisfied(copy.deepcopy(c2))
        assert not ctx.satisfied(copy.deepcopy(c1))
        assert not ctx.satisfied(copy.deepcopy(c3))
        ctx.reset_slot('intent')
        assert not ctx["intent"].dirty
        assert ctx["intent"].life_type == "forever"
        ctx.update_slot("intent", c2)


if __name__ == '__main__':
    tc = TestContext()
    tc.test_context()
