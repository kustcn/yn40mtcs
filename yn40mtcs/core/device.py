import logging

from .attribute import Attribute, AttrWriteType
from .constants import *

logger = logging.getLogger('{}.core.{}'.format(LOGGER_NAME, __name__))
class Device(object):
    def __init__(self, config):
        self.config = config
        self.attributes = {}
        self.commands = {}
        self.state = STATE.OFF
        self.state_attr = Attribute('state', 'State', value=STATE.OFF, group='Basic', description="State")

    def init_attributes(self):
        for _, value in vars(self).items():
            if isinstance(value, Attribute):
                self.add_attribute(value)
                
    def add_attribute(self, attr):
        self.attributes[attr.key] = attr

    def init_device(self):
        return True
    
    def run(self, command):
        logger.info("device ready to start... ♨️ ")

        self.init_attributes()
        
        if not self.init_device():
            return
