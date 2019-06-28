#!/usr/bin/env python
# encoding: utf-8
from evashare.collections import OrderedSet
from eva.dm.units import (
    Agent,
    MixAgency
)

import logging
log = logging.getLogger(__name__)


class ExpectAgenda(object):
    """
    Manage the visibility of bizunits and related intents and slots,
    given specific stack state.

    Attributes
    ----------
    visible_agents : OrderdSet, the visible agents, given specific context.
    visible_slots : set, the visible slots, given specific context.
    visible_intents : set, the visible intents, given specific context.

    """
    def __init__(self, stack):
        self._visible_tree_agents = None
        self._stack = stack
        self.visible_slots = None
        self.visible_slots = None
        self.visible_agents = None

    def compute_visible_units(self):
        """

        Calculate visible bizunits, intents, slots
        """
        # ordered by context priority
        candicates = self._visible_agents_of_focus_hierachy()
        if self._visible_tree_agents is None:
            self._visible_tree_agents = self._visible_descendant_agents(
                self._stack.items[0])
        candicates.extend(self._visible_tree_agents)

        self.visible_intents = set()
        slots = []
        for agent in candicates:
            slots.extend(agent.target_slots)
            slots.extend(agent.trigger_slots)
            for slot in agent.trigger_slots:
                if slot.key == "intent":
                    self.visible_intents.add(slot.value)

        #  TODO: valid_slots
        self.visible_slots = set([c.key for c in slots])
        self.visible_slots.remove("intent")
        self.visible_agents = OrderedSet(candicates)

    def _visible_agents_of_focus_hierachy(self):
        """
        Search bizunits up along the hierarchy path, and for each bizunit,
        search it's descendant.

        """
        candicates = []
        for unit in self._none_root_ancestors_of_focus_agent():
            candicates.extend(self._visible_descendant_agents(unit))
        return candicates

    def show_visible_agents(self):
        return [agent.tag for agent in self.visible_agents]

    def _none_root_ancestors_of_focus_agent(self):
        focus = self._stack.top()
        unit = focus
        while not unit.is_root():
            yield unit
            unit = unit.parent

    def _visible_descendant_agents(self, bizunit):
        agents = []

        def visit_tree(unit):
            if isinstance(unit, Agent):
                agents.append(unit)
            elif isinstance(unit, MixAgency):
                for child in unit.children:
                    # entrancable children of MixAgency node in the tree and
                    # children of active MixAgency node.
                    if child.entrance or unit in self._stack.items:
                        visit_tree(child)
            else:
                for child in unit.children:
                    visit_tree(child)
        visit_tree(bizunit)
        return agents

    def __repr__(self):
        str_slots = "\n                ".join(
            ["\n            ValidSlots:"] + [
                "{0}".format(c) for c in sorted(self.visible_slots)])

        str_intents = "\n                ".join(
            ["\n            ValidIntents:"] + [
                "{0}".format(c) for c in sorted(self.visible_intents)])
        return str_intents + str_slots
