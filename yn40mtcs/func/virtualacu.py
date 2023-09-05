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

logger = logging.getLogger(LOGGER_NAME)

class VirtualTel(object):
    '''
        Virtual antenna interface module
        communication mode：sockets，TCP/IP protocl
    '''
    def __init__(self, config):
        self._AZ=0.0
        self._EL=0.0
        self._AZSPEED=0.0
        self._ELSPEED=0.0
        self._UPDOWN=0
        self._INOUT=0
        self._ACI='0'
        self.status='Health' #'Health', 'Standby', 'Error', 'Poweroff'
        self.config = config
        self.acu_prtcl = acuprotocol.AcuProtcl()
        
        self._Longitude = [float(v) for v in self.config.Longitude.split(':')]
        self._Latitude = [float(v) for v in self.config.Latitude.split(':')]
        
        self.sock = None
        self.Connect()
        #self._lock = threading.Lock()

    def Connect(self):
        self.serv_addr = self.config.Host_Addr
        self.port = self.config.Host_Port
        self.buf_size = self.config.Buffer_Size # Network connection parameters
        self.ADDR = (self.serv_addr, self.port)
        self.sock = socket(AF_INET, SOCK_STREAM) # instantiate python-class 'socket'
        self.sock.settimeout(5)
        self.sock.connect(self.ADDR) # Network connecting

    def __del__(self):
        if self.sock:
            self.sock.close()

    def DumpStatus(self):
        print('AZ=', self._AZ)
        print('EL=', self._EL)
        print('INOUT=', self._INOUT)
        print('AZ Speed=', self._AZSPEED)
        print('EL Speed=', self._ELSPEED)
        print('Status:', self.status)

    def PointTo(self, az, el):
        '''
            Generate a communication message from the position Angle
            Angle: Azimuth、Elevation
        '''
        # self._AZ=az
        # self._EL=el
        '''
        commented by daiwei 20210111
        if self.GetStatus():
            if ((self.status =='Health') or (self.status=='Poweroff')): #XXXXX Remove poweroff for real application
                az0 = self._AZ
                commandopt = self.acu_prtcl.track_on(az0, az, el)
                #with self._lock:
                self.sock.send(commandopt)
                status_acu = self.sock.recv(30)
                return True
            else:
                return False
        else:
            return False
        '''
        #added by daiwei 20210111
        def tohexstr(s):
            return ''.join('%02x' % ord(c) for c in s)
        if ((self.status =='Health') or (self.status=='Poweroff')): #XXXXX Remove poweroff for real application
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
                self.status='Health'
            elif _STATUS[5][0]== '\x01':
                self.status='Poweroff'
            return True
        else:
            return False
        #aded by daiwei

    def GetStatus(self):
        '''
            status: communication information from ACU control computer
            judge The running state of the telescope
        '''
        commandquery = self.SetStatus('query')
        #with self._lock:
        #Send to machine
        self.sock.send(commandquery)
        #Receive
        status_acu = self.sock.recv(30)

        #Check if status is good
        lenstat= len(status_acu)
        if lenstat==10:
            self.status='Acu Error' # FAULT
            return False

        elif lenstat==30:
            _STATUS = self.acu_prtcl.normalstatus(status_acu)
            self._AZ = _STATUS[0][0]/10000.0
            self._EL = _STATUS[1][0]/10000.0
            self._INOUT = _STATUS[2][0]
            self._AZSPEED = _STATUS[3][0]/10000.0
            self._ELSPEED = _STATUS[4][0]/10000.0
            if _STATUS[5][0]== '\x00':
                self.status='Health'
                return True
            elif _STATUS[5][0]== '\x01':
                self.status='Poweroff'
                return True

        elif lenstat==9:
            self.status='Standby'
            return True

    def SetStatus(self, stat):
        '''
            setting in remote control computer
            state: 'standby', 'stop', 'query'
        '''
        self.status=stat
        if self.status=='standby':
            _PACKAGE = self.acu_prtcl.standby()
            return _PACKAGE
        elif self.status=='query':
            _PACKAGE = self.acu_prtcl.query()
            return _PACKAGE
        elif self.status=='stop':
            _PACKAGE = self.acu_prtcl.stop()
            return _PACKAGE

if __name__ == '__main__':
    test1 = VirtualTel()
    print(test1.PointTo(301.001,56.72))

