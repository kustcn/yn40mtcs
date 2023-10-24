#!/usr/bin/env pyhton3.7
# -*- coding: utf-8 -*-
'''
Author : Huang Yuxiang, Li Kejia, Dai Wei, Wei Shoulin
Date   : Aug. 24th 2019
         Sep. 10th 2023
'''

import numpy as np
import logging

from yn40mtcs.core.config import ConfigClass
from yn40mtcs.core.utils import data_path
from yn40mtcs.core.constants import LOGGER_NAME

logger = logging.getLogger('{}.func.{}'.format(LOGGER_NAME, __name__))
class SourceList:
    '''
    get the catalogue entry of sourcelist
    '''
    def __init__(self,cfg_fil='default.cfg',filenum='0'):
        '''
        filenum = '0' : calibrators for pointing
                  '1' : pulsar list
                  '2' : VLBI schedule
        '''
        # execfile(cfgpath, {'this':self})
        config = ConfigClass(data_path(cfg_fil))
        if filenum=='0':
            self.filename = data_path(config.calibrator_list) # self.config.Rootpath + self.config.Calibrator_List
            logger.info('The file of "calibrator_list" is reading !!!')
        elif filenum=='1':
            self.filename = data_path(config.pulsar_list) # self.config.Rootpath + self.config.Pulsar_List
            logger.info('The file of "pulsar_list" is reading !!!')
        elif filenum=='2':
            self.filename = data_path(config.vlbi_schedule) # self.config.Rootpath + self.config.Vlbi_Schedule
            logger.info('The file of "vlbi_schedul" is reading !!!')
        #
        #self.Catalog = np.loadtxt(self.filename, dtype='str', comments='#', delimiter='\t')
        self.catalog = np.loadtxt(self.filename, dtype='str', comments='#',ndmin=2)
    #
    def number_src(self):
        row, _ = self.catalog.shape
        return row
    #
    def get_radec(self, idx, col1=1, col2=2):
        row = self.number_src()
        if (idx>=0) and (idx<row):
            return self.catalog[idx, col1], self.catalog[idx, col2]  # Ra(Type: string),Dec(Type: string)
    #
    def get_src_name(self, idx, col0=0):
        row = self.number_src()
        if (idx>=0) and (idx<row):
            return self.catalog[idx, col0]  # sourcename(Type: string)
    #
    def get_obser_time(self, idx, col3=4):
        row = self.number_src()
        if (idx>=0) and (idx<row):
            return self.catalog[idx, col3] #
    #
    def get_scan_name(self, idx, col4=1):
        row = self.number_src()
        if (idx>=0) and (idx<row):
            return self.catalog[idx, col4] #
    #
    def get_scan_num(self, idx, col5=0):
        row = self.number_src()
        if (idx>=0) and (idx<row):
            return self.catalog[idx, col5] #
    #
    def get_preob_time(self, idx, col6=6):
        row = self.number_src()
        if (idx>=0) and (idx<row):
            return self.catalog[idx, col6] #
    #
    def get_record_time(self, idx, col7=7):
        row = self.number_src()
        if (idx>=0) and (idx<row):
            return self.catalog[idx, col7] #
    #
    def get_valiad_time(self, idx, col8=8):
        row = self.number_src()
        if (idx>=0) and (idx<row):
            return self.catalog[idx, col8] #
    #
    def get_end_time(self, idx, col9=8):
        row = self.number_src()
        if (idx>=0) and (idx<row):
            return self.catalog[idx, col9] #
