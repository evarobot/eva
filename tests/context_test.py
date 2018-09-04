#!/usr/bin/env python
# encoding: utf-8
import copy
from vikidm.context import Slot
from vikidm.context import Context


class TestContext(object):
    """"""

    def test_context(self):
        c1 = Slot("intent", "location.query")
        c2 = Slot("intent", "name.query", "forever")
        c3 = Slot("location", "nike")
        c4 = Slot("date", "today")
        ctx = Context()

        ctx.add_slot(copy.deepcopy(c1))
        ctx.update_slot("intent", copy.deepcopy(c2))
        ctx.add_slot(copy.deepcopy(c3))
        ctx.add_slot(copy.deepcopy(c4))
        assert(ctx["intent"].dirty == True)
        assert(ctx["location"].dirty == False)
        assert(ctx.satisfied(copy.deepcopy(c2)))
        assert(ctx.satisfied(copy.deepcopy(c1)) == False)
        assert(ctx.satisfied(copy.deepcopy(c3)) == False)
        ctx.reset_slot('intent')
        assert(ctx["intent"].dirty == False)
        assert(ctx["intent"].life_type == "forever")
        ctx.update_slot("intent", c2)


if __name__ == '__main__':
    tc = TestContext()
    tc.test_context()
