from enum import Enum
import time
from .constants import HISTORY_VALUES_QUEUE_SIZE

class AttrWriteType(Enum):
    READ=1
    WRITE=2

class DisplayLevel(Enum):
    OPERATOR=1
    ADMIN=2

class WriteLevel(Enum):
    OPERATOR=1
    ADMIN=2

class Attribute(dict):
    def __init__(self, key = '', label = '', value = None, unit=None, description = '', display_level = DisplayLevel.OPERATOR, writable = AttrWriteType.READ, write_level = WriteLevel.ADMIN, polling_period = -1, group = '', need_load = False):
        super(Attribute, self).__init__()
        self["key"] = key
        self["label"] = label
        self["value"] = value
        self["unit"] = unit
        self["description"] = description
        self["__tag__"] = 'Attribute'
        self["writable"] = writable
        self["display_level"] =display_level
        self["write_level"] = write_level
        self["polling_period"] = polling_period
        self["group"] = group
        self["need_load"] = need_load
        self["update_at"] = time.time()
        self["history_values"] = [(value, self["update_at"])]

    @property
    def key(self):
        return self["key"]
    @key.setter
    def key(self, v):
        self["key"] = v

    @property
    def label(self):
        return self["label"]
    @label.setter
    def label(self, v):
        self["label"] = v

    @property
    def value(self):
        return self["value"]
    @value.setter
    def value(self, v):
        self["label"] = v
        self["update_at"] = time.time()
        if len(self["history_values"]) > HISTORY_VALUES_QUEUE_SIZE:
            self["history_values"].pop(0)
        self["history_values"].append((v, self["update_at"])) 

    @property
    def unit(self):
        return self["unit"]
    @unit.setter
    def unit(self, v):
        self["unit"] = v

    @property
    def description(self):
        return self["description"]
    @description.setter
    def description(self, v):
        self["description"] = v

    @property
    def writable(self):
        return self["writable"]
    @writable.setter
    def writable(self, v):
        self["writable"] = v

    @property
    def display_level(self):
        return self["display_level"]
    @display_level.setter
    def display_level(self, v):
        self["display_level"] = v

    @property
    def write_level(self):
        return self["write_level"]
    @write_level.setter
    def write_level(self, v):
        self["write_level"] = v

    @property
    def polling_period(self):
        return self["polling_period"]
    @polling_period.setter
    def polling_period(self, v):
        self["polling_period"] = v

    @property
    def group(self):
        return self["group"]
    @group.setter
    def group(self, v):
        self["group"] = v            

    @property
    def need_load(self):
        return self["need_load"]
    @need_load.setter
    def need_load(self, v):
        self["need_load"] = v

    @property
    def update_at(self):
        return self["update_at"]
    @update_at.setter
    def update_at(self, v):
        self["update_at"] = v

    @property
    def history_values(self):
        return self["history_values"]
    @history_values.setter
    def history_values(self, v):
        self["history_values"] = v