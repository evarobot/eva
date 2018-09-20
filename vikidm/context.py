# coding=utf-8
import logging
from json import JSONEncoder

log = logging.getLogger(__name__)


class Slot(JSONEncoder):
    """
    概念类，包含键值对。
    """
    LIFE_STACK = "LIFE_STACK"

    def __init__(self, key, value=None,
                 optional=False, life_type="LIFE_STACK"):
        self._key = key
        self._value = value
        self.life_type = life_type
        self.optional = optional

    def default(self, o):
        return o.__dict__

    @property
    def key(self):
        return self._key

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = v
        if hasattr(self, '_hash'):
            self._hash = hash(str(self))

    @property
    def dirty(self):
        return self.value is not None

    def __unicode__(self):
        return u"Slot({0}={1})".format(self.key, self.value)

    def __str__(self):
        return unicode(self).encode('utf8')

    def __hash__(self):
        if hasattr(self, '_hash'):
            return self._hash
        self._hash = hash(str(self))
        return self._hash

    def __eq__(self, r):
        try:
            return self._hash == r._hash
        except AttributeError:
            return hash(self) == hash(r)

    def __repr__(self):
        return self.__unicode__()


class Context(object):
    """ System have one context instance,
    which is used to manage a set of slots(Memory).

    Attributes
    ----------
    _all_slots : dict, {"key1": slot1, "key2": slot2}

    """

    def __init__(self):
        self._all_slots = {}

    def add_slot(self, slot):
        """ Add one slot instance to memory.

        Parameters
        ----------
        slot : Slot, Slot instance

        """
        slot.value = None
        self._all_slots[slot.key] = slot

    def update_slot_by_value(self, key, value):
        """

        Parameters
        ----------
        key : str, key of target slot
        value : Slot, Slot instance

        """
        self.update_slot(key, Slot(key, value))

    def update_slot(self, key, slot):
        """ Update specific slot.

        Parameters
        ----------

        key : str, key of target slot.
        slot : Slot, Slot instance.

        """
        assert(key == slot.key)
        if key not in self._all_slots:
            log.error("不存在概念{0}".format(key))
            return
        self._all_slots[key] = slot

    def reset_slot(self, key):
        """ Set specific slot with `None` value.

        Parameters
        ----------
        key : str, used to identify slot.

        """
        slot = self._all_slots.get(key, None)
        if slot:
            slot.value = None
            return
        log.error("不存在概念{0}".format(key))

    def get_slot(self, key):
        """ Get specific slot by string key.

        Parameters
        ----------
        key : str, used to identify slot.

        """
        return self._all_slots[key]

    def __getitem__(self, key):
        return self._all_slots[key]

    def satisfied(self, slot):
        """ Check if memory have a slot equal to target slot.

        Parameters
        ----------
        slot: Slot, target comparing slot.

        """
        target = self._all_slots[slot.key]
        if target.dirty and slot.value.startswith("@") or\
                slot.optional and not target.dirty or\
                target == slot:
            return True
        return False

    def dirty(self, key):
        """ Check if value of specific slot is asigned.

        Parameters
        ----------
        key : str, key of specific slot.

        """
        target = self._all_slots.get(key, None)
        if target and target.dirty:
            return True
        if target is None:
            log.error("不存在概念{0}".format(key))
        return False

    def __str__(self):
        slots = []
        for key in sorted(self._all_slots.iterkeys()):
            slots.append(self._all_slots[key])
        return "\n                ".join(["\n            Context:"] +
                                         [str(c) for c in slots])

    def __repr__(self):
        return self.__str__()
