#!/usr/bin/env python
# encoding: utf-8
import copy
from vikidm.context import Concept
from vikidm.context import Context


class TestContext(object):
    """"""

    def test_context(self):
        c1 = Concept("intent", "location.query")
        c2 = Concept("intent", "name.query", "forever")
        c3 = Concept("location", "nike")
        c4 = Concept("date", "today")
        ctx = Context()

        ctx.add_concept(copy.deepcopy(c1))
        ctx.update_concept("intent", copy.deepcopy(c2))
        ctx.add_concept(copy.deepcopy(c3))
        ctx.add_concept(copy.deepcopy(c4))
        assert(ctx["intent"].dirty == True)
        assert(ctx["location"].dirty == False)
        assert(ctx.satisfied(copy.deepcopy(c2)))
        assert(ctx.satisfied(copy.deepcopy(c1)) == False)
        assert(ctx.satisfied(copy.deepcopy(c3)) == False)
        ctx.reset_concept('intent')
        assert(ctx["intent"].dirty == False)
        assert(ctx["intent"].life_type == "forever")
        ctx.update_concept("intent", c2)


if __name__ == '__main__':
    tc = TestContext()
    tc.test_context()
