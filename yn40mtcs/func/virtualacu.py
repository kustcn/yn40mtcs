#!/usr/bin/env pyhton2.7
# -*- coding: utf-8 -*-
'''
Author : Huang Yuxiang, Li Kejia
Date   : Aug. 23th 2019
'''

import sys
import logging
from socket import *

from yn40mtcs.core.device import Device
from yn40mtcs.func import acuprotocol # communication protocol between ACU computers
from yn40mtcs.core.constants import *
from yn40mtcs.core.config import ConfigClass
from yn40mtcs.core.utils import data_path

logger = logging.getLogger('{}.func.{}'.format(LOGGER_NAME, __name__))

class VirtualTel(object):
    '''
        Virtual antenna interface module
        communication mode: sockets, TCP/IP protocl
    '''
    def __init__(self, cfg_fil):
        self._AZ=0.0
        self._EL=0.0
        self._AZSPEED=0.0
        self._ELSPEED=0.0
        self._UPDOWN=0
        self._INOUT=0
        self._ACI='0'
        self.status=STATE_NAMES[STATE.HEALTH.value] #'HEALTH', 'STANDBY', 'ERROR', 'POWEROFF'
        self.config = cfg_fil
        self.acu_prtcl = acuprotocol.AcuProtcl()
        
        self._Longitude = [float(v) for v in self.config.longitude.split(':')]
        self._Latitude = [float(v) for v in self.config.latitude.split(':')]
        
        self.sock = None
        self.connect()

    def connect(self):
        self.serv_addr = self.config.acu_addr
        self.port = self.config.acu_port
        self.buf_size = self.config.acu_buffer_size # Network connection parameters
        self.ADDR = (self.serv_addr, self.port)
        self.sock = socket(AF_INET, SOCK_STREAM) # instantiate python-class 'socket'
        self.sock.settimeout(5)
        self.sock.connect(self.ADDR) # Network connecting

    def __del__(self):
        if self.sock:
            self.sock.close()

    def dump_status(self):
        print('AZ=', self._AZ)
        print('EL=', self._EL)
        print('INOUT=', self._INOUT)
        print('AZ Speed=', self._AZSPEED)
        print('EL Speed=', self._ELSPEED)
        print('Status:', self.status)

    def point_to(self, az, el):
        '''
            Generate a communication message from the position Angle
            Angle: Azimuth、Elevation
        '''
        def tohexstr(s):
            return ''.join('%02x' % ord(c) for c in s)
        if ((self.status =='HEALTH') or (self.status=='POWEROFF')): #XXXXX Remove poweroff for real application
            az0 = self._AZ
            commandopt = self.acu_prtcl.track_on(az0, az, el)
            #with self._lock:
            self.sock.send(commandopt)
            status_acu = self.sock.recv(30)
            logger.debug('status_acu= {} len= {} in {}'.format(tohexstr(status_acu),len(status_acu),sys._getframe().f_code.co_name))
            _STATUS = self.acu_prtcl.normalstatus(status_acu)
            self._AZ = _STATUS[0][0]/10000.0
            self._EL = _STATUS[1][0]/10000.0
            self._INOUT = _STATUS[2][0]
            self._AZSPEED = _STATUS[3][0]/10000.0
            self._ELSPEED = _STATUS[4][0]/10000.0
            if _STATUS[5][0]== '\x00':
                self.status='HEALTH'
            elif _STATUS[5][0]== '\x01':
                self.status='POWEROFF'
            return True
        else:
            return False

    def get_status(self):
        '''
            status: communication information from ACU control computer
            judge The running state of the telescope
        '''
        command_query = self.set_status('QUERY')
        self.sock.send(command_query)
        status_acu = self.sock.recv(30)

        #Check if status is good
        len_stat= len(status_acu)
        if len_stat==10:
            self.status='ACU_ERR' # FAULT
            return False

        elif len_stat==30:
            _STATUS = self.acu_prtcl.normal_status(status_acu)
            self._AZ = _STATUS[0][0]/10000.0
            self._EL = _STATUS[1][0]/10000.0
            self._INOUT = _STATUS[2][0]
            self._AZSPEED = _STATUS[3][0]/10000.0
            self._ELSPEED = _STATUS[4][0]/10000.0
            if _STATUS[5][0]== '\x00':
                self.status='HEALTH'
                return True
            elif _STATUS[5][0]== '\x01':
                self.status='POWEROFF'
                return True

        elif len_stat==9:
            self.status='STANDBY'
            return True

    def set_status(self, stat):
        '''
            setting in remote control computer
            state: 'STANDBY', 'STOP', 'QUERY'
        '''
        self.status=stat
        if self.status=='STANDBY':
            _PACKAGE = self.acu_prtcl.standby()
            return _PACKAGE
        elif self.status=='QUERY':
            _PACKAGE = self.acu_prtcl.query()
            return _PACKAGE
        elif self.status=='STOP':
            _PACKAGE = self.acu_prtcl.stop()
            return _PACKAGE

if __name__ == '__main__':
    test1 = VirtualTel()
    print(test1.point_to(301.001,56.72))

