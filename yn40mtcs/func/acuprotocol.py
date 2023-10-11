#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
'''
Author : Huang Yuxiang, Li Kejia
Date   : Aug. 23th 2019
'''

import struct
import sys
import logging
from yn40mtcs.core.constants import *

logger = logging.getLogger('{}.func.{}'.format(LOGGER_NAME, __name__))

class AcuProtcl:
    '''
        the communication protocol between ACU control computers, TCP/IP
    '''
    def __init__(self):
        self._CID = 'FS' # Communication Identifier
        self._FCS1 = 0 # Frame check Code

    #--------------------Track On--------------------
    def track_on(self, az0, az, el):
        '''
            Tracking
            protocol information: 标识    帧长   设备号  class    func     帧号       AZ             EL             校验码
                                  'FS'    18     1       0        '5'      0        1800000        300000
            hexadecimal format:   46 53   12 00  01      00       05       00       40 77 1b 00    e0 93 04 00    00 00
        '''
        logger.debug('az0={} az= {} el= {}  in {}'.format(str(az0),str(az),str(el),sys._getframe().f_code.co_name))
        _package0 = struct.pack('2s', self._CID)
        _FM_LENGTH = 18 # Frame Length
        _package1 = _package0 + struct.pack('H',_FM_LENGTH)
        _EQUIP_NUM = 1 # computer number: 1 ACU controling computer, 0 ACU remote-control computer
        _package2 = _package1 + struct.pack('b',_EQUIP_NUM)
        _FM_CLAS = 0 # Frame Class
        _package3 = _package2 + struct.pack('b',_FM_CLAS)
        _FM_FUNC = 5 #  Frame Function
        _package4 = _package3 + struct.pack('b',_FM_FUNC)

        # winding switching
        if (az0 >= 180.0 and az >= 180.0) or (az0 < 180.0 and az < 180.0):
            _WD_SWITCH = 0 # From +270 to +270 Or From -270 to -270
        if (az0 < 180.0) and (az >= 180.0):
            _WD_SWITCH = 1 # From -270 to +270
        if (az0 >= 180.0) and (az < 180.0):
            _WD_SWITCH = 2 # From +270 to -270
        # AZ and EL setting
        _package5 = _package4 + struct.pack('b',_WD_SWITCH)
        _AZ = az * 10000
        _package6 = _package5 + struct.pack('I',_AZ)
        _EL = el * 10000
        # package1 = struct.pack('I',_AZ)
        # print package1
        _package7 = _package6 + struct.pack('I',_EL) # Frame check Sequence
        # package2 = struct.pack('I',_EL)
        # print package2
        _package = _package7 + struct.pack('bb',self._FCS1,self._FCS1)

        # print _package
        def tohexstr(s):
            return ''.join('%02x' % ord(c) for c in s)
        logger.debug('_package= {} len= {} in {}'.format(tohexstr(_package),len(_package),sys._getframe().f_code.co_name))
        return _package

    #--------------------Stop tracking--------------------
    def stop(self):
        '''
            Stopping
            protocol information: 标识    帧长    设备号   class    func    帧号                       校验码
                                  'FS'    13      1        0        '3'     1
            hexadecimal format:   46 53   0d 00   01       00       03      01      00     00    00   42 5c
            +protocol information: 标识    帧长   设备号   class    func    帧号      ?      ?      ?    校验码
            +                      'FS'    13     1        0        '3'     2       ?      ?      ?
            +hexadecimal format:   46 53   0d 00  01       00       03      02      00     00     00   8f 79
        '''
        _package0 = struct.pack('2s', self._CID)
        _FM_LENGTH = 13 # Frame Length
        _package1 = _package0 + struct.pack('H',_FM_LENGTH)
        _EQUIP_NUM = 1 # computer number: 1 ACU controling computer, 0 ACU remote-control computer
        _package2 = _package1 + struct.pack('b',_EQUIP_NUM)
        _FM_CLAS = 0 # Frame Class
        _package3 = _package2 + struct.pack('b',_FM_CLAS)
        _FM_FUNC = 3 #  Frame Function
        _package4 = _package3 + struct.pack('b',_FM_FUNC)
        _VACM1 = 1
        _package5 = _package4 + struct.pack('b',_VACM1)
        _VACM2 = 0
        _package6 = _package5 + struct.pack('b',_VACM2)
        _package7 = _package6 + struct.pack('b',_VACM2)
        _package8 = _package7 + struct.pack('b',_VACM2)
        _package9 = _package8 + struct.pack('bb',self._FCS1,self._FCS1)

        _package10 = _package9 + struct.pack('2s', self._CID)
        _package11 = _package10 + struct.pack('H',_FM_LENGTH)
        _package12 = _package11 + struct.pack('b',_EQUIP_NUM)
        _package13 = _package12 + struct.pack('b',_FM_CLAS)
        _package14 = _package13 + struct.pack('b',_FM_FUNC)
        _VACM3 = 2
        _package15 = _package14 + struct.pack('b',_VACM3)
        _package16 = _package15 + struct.pack('b',_VACM2)
        _package17 = _package16 + struct.pack('b',_VACM2)
        _package18 = _package17 + struct.pack('b',_VACM2)
        _package = _package18 + struct.pack('bb',self._FCS1,self._FCS1)
        return _package

    #--------------------query--------------------
    def query(self):
        '''
            Querying
            protocol information: 标识    帧长    设备号  class   func   校验码
                                  'FS'    9       1       16      '1'
            hexadecimal format:   46 53   09 00   01      10      01     77 5c
        '''
        _package0 = struct.pack('2s', self._CID)
        _FM_LENGTH = 9 # Frame Length
        _package1 = _package0 + struct.pack('H',_FM_LENGTH)
        _EQUIP_NUM = 1 # computer number: \x01 ACU , \x00 ACU remote
        _package2 = _package1 + struct.pack('b',_EQUIP_NUM)
        _FM_CLAS = 16 # Frame Class \x10
        _package3 = _package2 + struct.pack('b',_FM_CLAS)
        _FM_FUNC = 1 #  Frame Function
        _package4 = _package3 + struct.pack('b',_FM_FUNC)
        _package = _package4 + struct.pack('bb',self._FCS1,self._FCS1)

        return _package

    #--------------------Stand By--------------------
    def standby(self):
        '''
            Standby
            protocol information: 标识    帧长    设备号  class   func   校验码
                                  'FS'    9       1       0       '1'
            hexadecimal format:   46 53   09 00   01      00      01     77 5c
        '''
        _package0 = struct.pack('2s', self._CID)
        _FM_LENGTH = 9 # Frame Length
        _package1 = _package0 + struct.pack('H',_FM_LENGTH)
        _EQUIP_NUM = 1 # computer number: \x01 ACU , \x00 ACU remote
        _package2 = _package1 + struct.pack('b',_EQUIP_NUM)
        _FM_CLAS = 0 # Frame Class \x10
        _package3 = _package2 + struct.pack('b',_FM_CLAS)
        _FM_FUNC = 1 #  Frame Function
        _package4 = _package3 + struct.pack('b',_FM_FUNC)
        _package = _package4 + struct.pack('bb',self._FCS1,self._FCS1)

        return _package

    #--------------------Normal Status Info--------------------
    def normal_status(self,status):
        '''
            Normal status information
            protocol information: 标识    帧长   设备号  class   func   帧号     ?    远控   伺服   内外圈     AZ
                                  'FS'    30     2       17      '1'    0      ?     0      1      1        1800000
            hexadecimal format:   46 53   1e 00  02      11      01     00     00    00     01     01       40 77 1b 00
            +protocol information: EL             AZ方向  EL方向  AZ速度  EL速度   AZ齿受力面   EL齿受力面  校验码
            +                      300000         0       0       0       0        33           33
            +hexadecimal format:   e0 93 04 00    00      00      00 00   00 00    21           21          3d 4f
        '''
        def tohexstr(s):
            return ''.join('%02x' % ord(c) for c in s)
        logger.debug('status_acu= {} len= {} in {}'.format(tohexstr(status),len(status),sys._getframe().f_code.co_name))
        _RES = struct.unpack('=2s',status[0:2])
        _LONGT = struct.unpack('=1H',status[2:4])
        #print('the frame length : %d' % longt)
        _EQUP = struct.unpack('=1B',status[4:5])
        #print('equipment coding : %d' % equp)
        _CLAS = struct.unpack('=1B',status[5:6])
        #print('The frame category code : %d' % clas)
        _FUNC = struct.unpack('=2c',status[6:8])
        #print('the frame function code : %d' % func)
        _VACM4 = struct.unpack('=1B',status[8:9])
        #print('Vaccum2 : %d' % vacm4)
        _TELCONTR = struct.unpack('=1B',status[9:10])
        #print('Remote command : %d' % Telcontr # remoting is \x03, not is \x00)
        _ACI = struct.unpack('=1s',status[10:11])
        #print('Antenna Control Interface : %s' % aci # Antenna poweroff is \x01, on is \x00)
        _INOUT = struct.unpack('=1B',status[11:12])
        #print('inside or out circle : %d' % inout # inside circle is \x00, outside circle is \x01)
        _AZ = struct.unpack('=1I',status[12:16])
        #print('AZ : %d' % az)
        _EL = struct.unpack('=1I',status[16:20])
        #print('EL : %d' % el)
        _RIGHTLEFT = struct.unpack('=1B',status[20:21])
        #print('turn right or left : %d' % rightleft # turn right is \x01, turn left is \x02, stop is \x00)
        _UPDOWN = struct.unpack('=1B',status[21:22])
        #print('turn up or down : %d' % updown # turn up is \x01, turn down is \x02, stop is \x00)
        _AZSPEED = struct.unpack('=1H',status[22:24])
        #print('the speed of AZ : %d' % azspeed)
        _ELSPEED = struct.unpack('=1H',status[24:26])
        #print('the speed of EL : %d' % elspeed)
        _AZ180 =struct.unpack('=1B',status[26:27])
        #print('the switch to AZ=180 : %d' % az180 # inside circle is \x12, outside circle is \x11, Antenna poweroff is \x21)
        _EL45 = struct.unpack('=1B',status[27:28])
        #print('the switch to EL=45 : %d' % el45 # <45 is \x12, >45 is \x12, Antenna poweroff is \x21)
        _VERF = struct.unpack('=2B',status[28:30])
        #print('ckeck code : %d%d' % verf)
        return (_AZ,_EL,_INOUT,_AZSPEED,_ELSPEED,_ACI)

    #--------------------Error Status Info--------------------
    def error_status(self,status):
        '''
            Error status information
            protocol information: 标识   帧长    设备号  class   func   帧号  校验码
                                  'FS'   10      2       2       '4'    3
            hexadecimal format:   46 53  0a 00   02      02      04     03    77 5c
        '''
        _RES = struct.unpack('=2s',status[0:2])
        _LONGT = struct.unpack('=1H',status[2:4])
        _EQUP = struct.unpack('=1B',status[4:5])
        _CLAS = struct.unpack('=1B',status[5:6])
        _FUNC = struct.unpack('=1B',status[6:7])
        _VACM5 = struct.unpack('=1B',status[7:8])
        _VERF = struct.unpack('=2B',status[8:10])
        #print 'check code : %d%d' % verf
        return False