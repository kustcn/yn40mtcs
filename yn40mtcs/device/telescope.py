import os
import sys
import threading
import logging

import numpy as np

from yn40mtcs.core.device import Device
from yn40mtcs.core.utils import get_parameter, data_path
from yn40mtcs.core.attribute import Attribute
from yn40mtcs.core.constants import *
from yn40mtcs.func import acu39, conv_coord, virtualacu

logger = logging.getLogger('{}.device.{}'.format(LOGGER_NAME, __name__))
class Telescope(Device):
    def __init__(self, cfg_fil):
        super(Telescope, self).__init__(cfg_fil)
        self.cfg_fil = cfg_fil
        self.status =  STATE_NAMES[7]
        self._lock = threading.Lock()
        self.declare_attributes()
        self.read_config()
        self.Threads = []

    def declare_attributes(self):
        self.AZ_cmd = Attribute('AZ_cmd', 'Latitude', value=0, unit="deg", group='Basic', description="input command  position AZ") 
        self.EL_cmd = Attribute('EL_cmd', 'Latitude', value=0, unit="deg", group='Basic', description="input command  position EL") 
        self.AZ_obj = Attribute('AZ_obj', 'AZ_obj', value=0, unit="deg", group='Basic', description="Instruction position sending to telescope AZ")
        self.EL_obj = Attribute('EL_obj', 'EL_obj', value=0, unit="deg", group='Basic', description="Instruction position sending to telescope EL") 
        self.AZ = Attribute('AZ', 'AZ', value=0, unit="deg", group='Basic', description="The intermediate value of the position calculation AZ")
        self.EL = Attribute('EL', 'EL', value=0, unit="deg", group='Basic', description="The intermediate value of the position calculation EL") 
        self.AZ_current = Attribute('AZ_current', 'AZ_current', value=0, unit="deg", group='Basic', description="Current postion AZ")
        self.EL_current = Attribute('EL_current', 'EL_current', value=0, unit="deg", group='Basic', description="Current postion EL") 
        self.RA_obj = Attribute('RA_obj', 'RA_obj', value=0, unit="deg", group='Basic', description="Celestial position RA")
        self.DEC_obj = Attribute('DEC_obj', 'DEC_obj', value=0, unit="deg", group='Basic', description="Celestial position DEC") 
        self.AZ_off = Attribute('AZ_off', 'AZ_off', value=0, unit="deg", group='Basic', description="Position offset AZ")
        self.EL_off = Attribute('EL_off', 'EL_off', value=0, unit="deg", group='Basic', description="Position offset EL") 

        self.sourcename= Attribute('SourceName', 'SourceName', value='', unit="", group='Basic', description="Source Name") 
    
    def read_config(self):
        self._Longitude = [float(v) for v in self.config['longitude'].split(':')]
        self._Latitude = [float(v) for v in self.config['latitude'].split(':')]
        self._Height = self.config['h']
        self._Atmosphere = self.config['atmosphere']
        self._PointingParameter = np.loadtxt(data_path(self.config['pointing_par']))  # Read parameters from new_pointing_par.txt

        # Selecting the virtual control device
        if self.config['hardware']=='ACU39':
            self.Hardware = acu39.Acu39Tel()
        elif self.config['hardware']=='FAKE':
            self.Hardware = virtualacu.VirtualTel(self.cfg_fil)
        else:
            logger.error('Unknown Hardware')
            sys.exit(0)

        # Ra-Dec to Az-El
        self._CoorGeo = conv_coord.CoordGeometry(iersfile=self.config['iers_fil'], ephfile=self.config['eph_fil'])
        
    #--------------------Display antenna status information--------------------
    def show_state(self):
        if self.state.value == 'EXIT':
            raise RuntimeError("Exiting, please check log!")
        if self.state.value == 'DISCONNECT':
            raise RuntimeError("Exiting, could not communicate with ACU!")
        '''
            XXXXXXX update AZ and EL current by reading from telescope hardware
        '''

        print('------ STATUS: {} -------'.format(self.state.value))
        print('Source:',self.sourcename.value)#20210228
        print('AZ_obj: {} AZ_off: {} AZ_current: {}'.format(self.AZ_obj.value, self.AZ_off.value, self.AZ_current.value))
        print('EL_obj: {} EL_off: {} EL_current: {}'.format(self.EL_obj.value, self.EL_off.value, self.EL_current.value))
        print('------------ RA and  DEC ------------')
        print('RA_obj: {}'.format(self.RA_obj.value))
        print('DEC_obj: {}'.format(self.DEC_obj.value))
        print('----------Point Model-------------------')
        print(self._PointingParameter)
        print('----------Pointing state ---------------')
        if self.Isready():
            print('Pointing ready')
        else:
            print('Pointing NOT ready')
        if len(self.Threads)>0:
            print('Control thread started')
        else:
            print('Control thread stopped')

        print('--------------------HARDWARE STATUS--------------------')
        self.Hardware.DumpStatus()

    def print_usage(self):
        print('The commands are ')
        print('Help/?              Print this help')
        print('Tell                Telescope state')
        print('AZEL AZ EL          Point telescope to given AZ EL')
        print('RADEC RA DEC        Keep telescope track to given RA DEC')
        print('Off RA_off DEC_off  Set offsets')
        print('Start               Start control loop')
        print('Halt                Stop telescope')
        print('Exit                Exit current program')
    def run(self, command):
        super(Telescope, self).run(command)

        cmds = command.split(' ')
        if cmds[0]=='help' or cmds[0] =='?':
            self.print_usage()
        elif cmds[0]=='Tell':
            self.ShowState()
        elif cmds[0]=='Halt':
            self.StopControlThread()
            logger.info('Control thread stopped')
        elif cmds[0]=='Start':
            self.StartControlThread()
            logger.info('Control thread started')  # rizhi
        elif cmds[0]=='Exit':
            #Do not modify this function, otherwise you will be dead
            os._exit(0)
        elif cmds[0]=='AZEL':
            if len(cmds) >= 3:
                az = float(cmds[1])
                el = float(cmds[2])
                self.TrackAZEL(az,el)
            else:
                logger.error('Missing operation variable')
        elif cmds[0]=='RADEC':
            if len(cmds) >= 3:
                ra = cmds[1]
                dec = cmds[2]
                self.TrackRADEC(ra,dec)
            else:
                logger.error('Missing operation variable')
        elif cmds[0]=='Off':
            if len(cmds)>=3:
                az_off = float(cmds[1])
                el_off = float(cmds[2])
                self.SetAZEL_off(az_off,el_off)
            else:
                logger.error('Missing operation variable')
        else:
            logger.error('command not found')

