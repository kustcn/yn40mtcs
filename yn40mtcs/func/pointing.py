#!/usr/bin/env python3.7
# _*_ coding: utf-8 _*_
'''
Author : Huang Yuxiang, Men Yunpeng, Lee Kejia, Dai Wei, Wei Shoulin
Date   : Aug. 24th 2019
         Sep. 10th 2023
'''

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import random
import pyvisa as visa
import time
from time import sleep
import sys
import os
from astropy.time import Time
import threading
import logging
import pickle
import zmq


from yn40mtcs.core.constants import LOGGER_NAME
from yn40mtcs.device.telescope import Telescope
from yn40mtcs.func.sourcelist import SourceList

logger = logging.getLogger('{}.func.{}'.format(LOGGER_NAME, __name__))
class Point:
    def __init__(self,midpath):

        # Instantiate class 'Telescope' and TCP/IP Connecting
        self._Tele = Telescope(cfgpath='data/default.cfg')
        self.middir = midpath
        self._Scan = self.middir + self._Tele.config.scan_fil
        self._Cal = self.middir + self._Tele.config.cal_fil
        self._srclst = SourceList()
        self._INST = self._Tele.config.pm_addr # 'TCPIP::178.1.16.32::INSTR'
        
        # Start thread background
        self._Tele.StartControlThread()
        logger.info('Control thread started')

        #ZMQ Init
        self.context = zmq.Context()
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.sndhwm = 1000
        self.publisher.bind("tcp://*:5528")

    #--------------------Initializing powermeter nrp-z21--------------------
    def set_power_meter(self):
        # visa.log_to_screen()
        logging.disable(logging.DEBUG) #avoid binary issues
        self._rm = visa.ResourceManager('@py')
        self._powmeter = self._rm.open_resource(self._INST)
        self._powmeter.write(u'*rst\n')
        sleep(5)
        self._powmeter.write(u'sens:aver:stat on\n')
        self._powmeter.write(u'sens:aver:count:auto off\n')
        self._powmeter.write(u'sens:aver:count 40\n')
        sleep(1)
        self._powmeter.write(u'sens:pow:AvG:aper 100e-3\n')
        self._powmeter.write('trig:sour imm\n')
        sleep(1)
        self._powmeter.write(u'init:cont on\n')
        sleep(2)
        logging.disable(logging.NOTSET)
        return self._powmeter

    #--------------------Get power level of IF signal--------------------
    def _get_power_level(self,pwm):
        logging.disable(logging.DEBUG) #avoid binary issues
        fv=float(pwm.query('fetch?'))
        #fv=random.randint(0,1000)
        logging.disable(logging.NOTSET)
        return fv

    #--------------------Cross Scanning--------------------
    def cross_scan(self, sourcename, powmeter, az_scan=0.2, el_scan=0.2, shape=(120,120)):

        # initial viable
        vdaz = np.array([])
        vdel = np.array([])
        vpowl = np.array([])
        vaz = np.array([])
        vel = np.array([])
        azsrc = np.array([]) #
        elsrc = np.array([]) #
        azconv = np.array([])
        elconv = np.array([])
        vdaz_fit = np.array([])
        vdaz_pow_fit = np.array([])
        vdel_fit = np.array([])
        vdel_pow_fit = np.array([])
        time_azel = [] #
        time_consume = []

        vdaz = []
        vdel = []
        vpowl = []
        vaz = []
        vel = []
        vdaz_fit = []
        vdaz_pow_fit = []
        vdel_fit = []
        vdel_pow_fit = []

        # viewing********* Feb. 26th 2020
        for idx in range(0,self._srclst.number_src()):
            if sourcename == self._srclst.get_src_name(idx):
                _ra,_dec = self._srclst.get_radec(idx)
                _srcradec = _ra + ' ' + _dec
        with self._Tele._lock:
            if self._Tele.status in ['IDLE','LIMIT','TRACKAZEL','TRACKRADEC']:
                self._Tele.sourcename = sourcename # 20210228
                self._Tele.status = 'TRACKRADEC' # TrackRADEC(_ra,_dec)
            else:
                return False

        sleep(0.1)
        with self._Tele._lock:
            if self._Tele.status in ['IDLE','LIMIT','TRACKAZEL','TRACKRADEC']:
                EL_init = self._Tele.EL
                AZ_init = self._Tele.AZ
                
                offset_rate = 0.99 # 20230915 Huang
                self._Tele.SetAZEL_off(-az_scan*offset_rate/np.cos(np.deg2rad(EL_init)),0.0)
                GMtime = time.gmtime()
                Fortime = str(GMtime.tm_year) + '-' + str(GMtime.tm_mon) + '-' + str(GMtime.tm_mday) + ' ' \
                        + str(GMtime.tm_hour) + ':' + str(GMtime.tm_min+12) + ':' + str(GMtime.tm_sec)
                _sc = self._Tele._Longitude + self._Tele._Latitude + [self._Tele._Height]
                _AZ, _EL = self._Tele._CoorGeo.radec2azel(_srcradec, SC=_sc, MCOW=self._Tele.config['atmosphere'], \
                        curtim=Fortime, backend=self._Tele.config['coord_converter'])
                _dAZ, _dEL = self._Tele.PointingModel(self._Tele._PointingParameter, _AZ, _EL)
                AZ = _AZ + _dAZ
                EL = _EL + _dEL
                if EL<8.2:
                    return 'EL LIMIT'
            else:
                return False

        logger.debug('sourcename={},_ra={},_dec={}'.format(sourcename,_ra,_dec))
        
        while True:
            with self._Tele._lock:
                if self._Tele.status=='LIMIT':
                    logger.info('******LIMITING******')
                    return 'EL LIMIT'
                EL_init = self._Tele.EL
                if self._Tele.Isready(0.02*3600/np.cos(np.deg2rad(EL_init))):
                    break
                self._Tele.ShowState()
                #ZMQ
                guistage = 'SLEW'
                guititle = 'SLEW Pointing scanning for source: {}   AZ=({})({}) EL=({})({})'.format(
                    sourcename, self._Tele.AZ_obj, self._Tele.AZ_current, self._Tele.EL_obj, self._Tele.EL_current)
                self.publisher.send_multipart(
                    [b"F", pickle.dumps([guistage, guititle])])
            sleep(1)
        
        # initial plot and file ************************* Nov 18th 2019
        _f = open(self._Scan,'a') # file scan.dat
        _fscan = open(self._Cal,'a') # file cal.dat
        logger.debug('recording in file<{}>'.format(self._Cal))
        plt.close('all')
        fig = plt.figure(figsize=(12,9))
        fig.suptitle('Pointing scanning for source: ' + sourcename)
        fig1 = plt.subplot(321)
        fig2 = plt.subplot(322)
        fig3 = plt.subplot(323)
        fig4 = plt.subplot(324)
        fig5 = plt.subplot(325)
        fig6 = plt.subplot(326)
        fig1.grid(1)
        fig2.grid(1)
        fig3.grid(1)
        fig4.grid(1)
        fig5.grid(1)
        fig6.grid(1)
        fig.tight_layout()
        fig.subplots_adjust(top=0.95)
        plt.ion()
    	
        # Scanning AZ as 0 ~ az_scan ~ 0 ~ -az_scan ~ 0
        scan_az = np.linspace(-az_scan,az_scan,shape[0])
        scan_az = np.append(scan_az,np.linspace(az_scan,-az_scan,shape[0]))

        sleep(5)
        num = 0
        for az_delta in scan_az/np.cos(np.deg2rad(EL_init)):
            time_start = time.time()
            num += 1
            el_delta = 0
            with self._Tele._lock:
                self._Tele.SetAZEL_off(az_delta,el_delta)
            sleep(0.15)
            with self._Tele._lock:
                el_current = self._Tele.EL_current

            EL_init = el_current
            while True:
                with self._Tele._lock:
                    if self._Tele.Status=='LIMIT':
                        logger.debug('******LIMITING******')
                        return 'EL LIMIT'
                    if self._Tele.Isready(0.015*3600/np.cos(np.deg2rad(el_current))):
                        sleep(0.12)
                        #with self._Tele._lock:
                        strtime = Time.now()
                        az_src = self._Tele.AZ
                        el_src = self._Tele.EL
                        az_conv = self._Tele.AZ_conv
                        el_conv = self._Tele.EL_conv
                        az_current = self._Tele.AZ_current
                        el_current = self._Tele.EL_current
                        powlev = self._get_power_level(powmeter)
                        break
                sleep(0.001)

            time_azel.append(strtime)
            az_dlt = az_current - az_src
            if az_dlt>10.:
                az_dlt = az_dlt - 360.
            elif az_dlt<-10.:
                az_dlt = az_dlt + 360.
            el_dlt = el_current - el_src
            tmp = '%s\t%s\t%f\t%f\t%f\t%f\t%f' % (strtime,sourcename,az_src,el_src,az_current,el_current,powlev)
            _f.writelines(tmp)
            _f.writelines('\n')

            vaz = np.append(vaz, az_current)
            vel = np.append(vel, el_current)
            azsrc = np.append(azsrc, az_src)
            elsrc = np.append(elsrc, el_src)
            azconv = np.append(azconv, az_conv)
            elconv = np.append(elconv, el_conv)
            vdaz = np.append(vdaz, az_dlt)
            vdel = np.append(vdel, el_dlt)
            vpowl = np.append(vpowl, powlev)
            vdaz_fit = np.append(vdaz_fit, az_dlt)
            vdaz_pow_fit = np.append(vdaz_pow_fit, powlev)
            
            fig1.cla()
            fig2.cla()
            fig3.cla()
            fig5.cla()
            fig1.grid(1)
            fig2.grid(1)
            fig3.grid(1)
            fig5.grid(1)
            fig1.set_xlabel('AZ(Deg)')
            fig1.set_ylabel('EL(Deg)')
            fig2.set_xlabel('Number')
            fig2.set_ylabel('Power(dBm)')
            fig1.plot(vdaz, vdel)
            fig2.plot(vpowl)
            fig3.plot(vdaz_fit, vdaz_pow_fit)
            time_stop = time.time()
            time_consume.append(time_stop-time_start)
            fig5.plot(time_consume)
            #ZMQ
            guistage = 'AZ+' if num<len(scan_az)/2 else 'AZ-'
            guititle = '{} Pointing scanning for source: {}'.format(guistage,sourcename)
            self.publisher.send_multipart([b"F", pickle.dumps([guistage, guititle, vdaz, vdel, vpowl, vdaz_fit, vdaz_pow_fit, time_consume,shape])])
            plt.pause(0.01)
            plt.show()
        
        # Scanning EL as 0 ~ el_scan ~ 0 ~ -el_scan ~ 0
        scan_el = np.linspace(el_scan,-el_scan,shape[1])
        scan_el = np.append(scan_el,np.linspace(-el_scan,el_scan,shape[1]))
    	
        num = 0
        with self._Tele._lock:
            self._Tele.SetAZEL_off(0.0,el_scan)
        sleep(15)
        time_consumeAZ=time_consume[:]
        for el_delta in scan_el:
            time_start = time.time()
            num += 1
            az_delta = 0
            with self._Tele._lock:
                self._Tele.SetAZEL_off(az_delta,el_delta)
            sleep(0.15)
            with self._Tele._lock:
                el_current = self._Tele.EL_current
            while True:
                with self._Tele._lock:
                    if self._Tele.Status=='LIMIT':
                        logger.debug('******LIMITING******')
                        return 'EL LIMIT'
                    if self._Tele.Isready(0.015*3600/np.cos(np.deg2rad(el_current))):
                        sleep(0.12)
                        strtime = Time.now()
                        az_src = self._Tele.AZ
                        el_src = self._Tele.EL
                        az_conv = self._Tele.AZ_conv
                        el_conv = self._Tele.EL_conv
                        az_current = self._Tele.AZ_current
                        el_current = self._Tele.EL_current
                        powlev = self._GetPowerLevel(powmeter)
                        break
                sleep(0.001)

            time_azel.append(strtime)
            az_dlt = az_current - az_src
            el_dlt = el_current - el_src
            tmp1 = '%s\t%s\t%f\t%f\t%f\t%f\t%f' % (strtime,sourcename,az_src,el_src,az_current,el_current,powlev)
            _f.writelines(tmp1)
            _f.writelines('\n')

            vaz = np.append(vaz, az_current)
            vel = np.append(vel, el_current)
            azsrc = np.append(azsrc, az_src)
            elsrc = np.append(elsrc, el_src)
            azconv = np.append(azconv, az_conv)
            elconv = np.append(elconv, el_conv)
            vdaz = np.append(vdaz, az_dlt)
            vdel = np.append(vdel, el_dlt)
            vpowl = np.append(vpowl, powlev)
            vdel_fit = np.append(vdel_fit, el_dlt)
            vdel_pow_fit = np.append(vdel_pow_fit, powlev)
            
            fig1.cla()
            fig2.cla()
            fig4.cla()
            fig6.cla()
            fig1.grid(1)
            fig2.grid(1)
            fig4.grid(1)
            fig6.grid(1)
            fig1.set_xlabel('AZ(Deg)')
            fig1.set_ylabel('EL(Deg)')
            fig2.set_xlabel('Number')
            fig2.set_ylabel('Power(dBm)')
            fig1.plot(vdaz, vdel)
            fig2.plot(vpowl)
            fig4.plot(vdel_fit, vdel_pow_fit)
            time_stop = time.time()
            time_consume.append(time_stop-time_start)
            fig6.plot(time_consume)
            #ZMQ
            guistage = 'EL-' if num<len(scan_el)/2 else 'EL+'
            guititle = '{} Pointing scanning for source: {}'.format(guistage,sourcename)
            self.publisher.send_multipart([b"F", pickle.dumps(
                [guistage, guititle, vdaz, vdel, vpowl, vdel_fit, vdel_pow_fit, time_consume,vdaz_fit,vdaz_pow_fit,time_consumeAZ])])
            plt.pause(0.01)
            plt.show()

        with self._Tele._lock:
            self._Tele.Status='IDLE'
        sleep(5)

        vdaz_pow_fit = vdaz_pow_fit.astype('float64')
        vdel_pow_fit = vdel_pow_fit.astype('float64')
        
        az_2_fit = self.fit(vdaz_fit,vdaz_pow_fit,0,0.05,1,0,0,0,0,0,0,0,0,0,0)
        el_2_fit = self.fit(vdel_fit,vdel_pow_fit,0,0.05,1,0,0,0,0,0,0,0,0,0,0)
        if az_2_fit == 'False' or el_2_fit == 'False':
            _f.close()
            _fscan.close()
            sleep(3)
            plt.close('all')
            return '1' # abnormal fitting
        else:
            vdaz_pow_fit1 = 10**(vdaz_pow_fit[0:shape[0]] / 10) # 511
            vdaz_pow_fit1 -= vdaz_pow_fit1.min()
            vdaz_pow_fit1 /= vdaz_pow_fit1.max()
            vdaz_fit1 = vdaz_fit[0:shape[0]] # 514
            vdaz_pow_fit2 = 10**(vdaz_pow_fit[shape[0]:] / 10) # 516
            vdaz_pow_fit2 -= vdaz_pow_fit2.min()
            vdaz_pow_fit2 /= vdaz_pow_fit2.max()
            vdaz_fit2 = vdaz_fit[shape[0]:] # 519
            vdel_pow_fit1 = 10**(vdel_pow_fit[0:shape[1]] / 10) # 521
            vdel_pow_fit1 -= vdel_pow_fit1.min()
            vdel_pow_fit1 /= vdel_pow_fit1.max()
            vdel_fit1 = vdel_fit[0:shape[0]] # 524
            vdel_pow_fit2 = 10**(vdel_pow_fit[shape[1]:] / 10) # 526
            vdel_pow_fit2 -= vdel_pow_fit2.min()
            vdel_pow_fit2 /= vdel_pow_fit2.max()
            vdel_fit2 = vdel_fit[shape[0]:] # 529

            az1_1_fit = self.fit(vdaz_fit1,vdaz_pow_fit1,0,0.05,1,0,0,0,0,0,0,0,0,0,0)
            az2_1_fit = self.fit(vdaz_fit2,vdaz_pow_fit2,0,0.05,1,0,0,0,0,0,0,0,0,0,0)
            el1_1_fit = self.fit(vdel_fit1,vdel_pow_fit1,0,0.05,1,0,0,0,0,0,0,0,0,0,0)
            el2_1_fit = self.fit(vdel_fit2,vdel_pow_fit2,0,0.05,1,0,0,0,0,0,0,0,0,0,0)
            if az1_1_fit == 'False' or az2_1_fit == 'False' or el1_1_fit == 'False' or el2_1_fit == 'False':
                _f.close()
                _fscan.close()
                sleep(3)
                plt.close('all')
                return '1' # abnormal fitting
            else:
                vdaz_pow_fitfit1,azopt1,azcov1 = az1_1_fit
                vdaz_pow_fitfit2,azopt2,azcov2 = az2_1_fit
                vdel_pow_fitfit1,elopt1,elcov1 = el1_1_fit
                vdel_pow_fitfit2,elopt2,elcov2 = el2_1_fit
                fig3.cla()
                fig4.cla()
                fig5.cla()
                fig6.cla()
                fig3.plot(vdaz_fit1,vdaz_pow_fit1, 'b')
                fig4.plot(vdel_fit1,vdel_pow_fit1, 'b')
                fig5.plot(vdaz_fit2,vdaz_pow_fit2, 'b')
                fig6.plot(vdel_fit2,vdel_pow_fit2, 'b')
                fig3.plot(vdaz_fit1,vdaz_pow_fitfit1, 'r', label='<AZ+>offset(arcsec): {}'.format(int(azopt1[0]*3600)))
                fig4.plot(vdel_fit1,vdel_pow_fitfit1, 'r', label='<EL->offset(arcsec): {}'.format(int(elopt1[0]*3600)))
                fig5.plot(vdaz_fit2,vdaz_pow_fitfit2, 'r', label='<AZ->offset(arcsec): {}'.format(int(azopt2[0]*3600)))
                fig6.plot(vdel_fit2,vdel_pow_fitfit2, 'r', label='<EL+>offset(arcsec): {}'.format(int(elopt2[0]*3600)))
                fig3.grid(1)
                fig4.grid(1)
                fig5.grid(1)
                fig6.grid(1)
                fig3.legend()
                fig4.legend()
                fig5.legend()
                fig6.legend()
                
                #ZMQ
                guistage = 'FIT'
                guititle = 'Pointing scanning for source: {}'.format(sourcename)
                self.publisher.send_multipart([b"F", pickle.dumps([guistage, guititle, vdaz_fit, vdaz_pow_fit1, vdel_fit, vdel_pow_fit1, vdaz_pow_fit2, vdel_pow_fit2,\
                                                                   vdaz_fit1, vdaz_pow_fitfit1, vdel_fit1, vdel_pow_fitfit1, vdaz_fit2, vdaz_pow_fitfit2, vdel_fit2, vdel_pow_fitfit2, azopt1,azopt2,elopt1,elopt2,shape])])
                plt.pause(5)

    	        # os.system('pause')
                if np.sqrt(np.mean((vdaz_pow_fit1 - vdaz_pow_fitfit1)**2)) > 0.3 \
                        or np.sqrt(np.mean((vdel_pow_fit1 - vdel_pow_fitfit1)**2)) > 0.3:
                    print('Bad fitting! Drop data!!!')
                    tmp = 'Bad fitting\n'
                    _f.writelines(tmp)
                    _f.close()
                    _fscan.close()
                    sleep(3)
                    plt.close('all')
                    return '1' # abnormal fitting
                else:
                    indx1 = np.argmin(np.abs(vdaz_fit1 - azopt1[0])) # 2020-0125 predcit location of source to location of source
                    time1 = time_azel[indx1]
                    az_premdl1 = azconv[indx1]
                    el_premdl1 = elconv[indx1]
                    scanaz1 = azopt1[0] # vdaz_fit1[indx1]
                    scanel1 = 0.0
                    az_fit1 = vaz[indx1]
                    el_fit1 = vel[indx1]
                    powl1 = vpowl[indx1]
                    indx2 = np.argmin(np.abs(vdaz_fit2 - azopt2[0])) #
                    scanaz2 = azopt2[0] # vdaz_fit2[indx2]
                    indx2 += shape[0]
                    time2 = time_azel[indx2]
                    az_premdl2 = azconv[indx2]
                    el_premdl2 = elconv[indx2]
                    scanel2 = 0.0
                    az_fit2 = vaz[indx2]
                    el_fit2 = vel[indx2]
                    powl2 = vpowl[indx2]
                    indx3 = np.argmin(np.abs(vdel_fit1 - elopt1[0]))
                    scanaz3 = 0.0
                    scanel3 = elopt1[0] # vdel_fit1[indx3]
                    indx3 += (2*shape[0])
                    time3 = time_azel[indx3]
                    az_premdl3 = azconv[indx3]
                    el_premdl3 = elconv[indx3]
                    az_fit3 = vaz[indx3]
                    el_fit3 = vel[indx3]
                    powl3 = vpowl[indx3]
                    indx4 = np.argmin(np.abs(vdel_fit2 - elopt2[0]))
                    scanel4 = elopt2[0] #vdel_fit2[indx4]
                    indx4 += (2*shape[0] + shape[1])
                    time4 = time_azel[indx4]
                    az_premdl4 = azconv[indx4]
                    el_premdl4 = elconv[indx4]
                    scanaz4 = 0.0
                    az_fit4 = vaz[indx4]
                    el_fit4 = vel[indx4]
                    powl4 = vpowl[indx4]

    	            # print meanaz,meanel,azopt,elopt,azopt.shape,elopt.shape
                    '''
                        az_premdl1: don't adding pointing model
                        el_premdl1: same as above
                        scanaz1:    deviation value
                        scanel1:    same as above
                        az_fit1:    closest to the best
                        el_fit1:    same as above
                        "corresponding values at the same point all above"

                    '''
                    tmp2 = '%s\taz+\t%s\t%f\t%f\t%f\t%f\t%f\t%f\t%f\t%1.12f\t%f\n' \
                        % (sourcename,str(time1),powl1,az_premdl1,el_premdl1,scanaz1,scanel1,az_fit1,el_fit1,azcov1[0][0],azopt1[1])
                    _fscan.writelines(tmp2)
                    tmp3 = '%s\taz-\t%s\t%f\t%f\t%f\t%f\t%f\t%f\t%f\t%1.12f\t%f\n' \
                        % (sourcename,str(time2),powl2,az_premdl2,el_premdl2,scanaz2,scanel2,az_fit2,el_fit2,azcov2[0][0],azopt2[1])
                    _fscan.writelines(tmp3)
                    tmp4 = '%s\tel-\t%s\t%f\t%f\t%f\t%f\t%f\t%f\t%f\t%1.12f\t%f\n' \
                        % (sourcename,str(time3),powl3,az_premdl3,el_premdl3,scanaz3,scanel3,az_fit3,el_fit3,elcov1[0][0],elopt1[1])
                    _fscan.writelines(tmp4)
                    tmp5 = '%s\tel+\t%s\t%f\t%f\t%f\t%f\t%f\t%f\t%f\t%1.12f\t%f\n' \
                        % (sourcename,str(time4),powl4,az_premdl4,el_premdl4,scanaz4,scanel4,az_fit4,el_fit4,elcov2[0][0],elopt2[1])
                    _fscan.writelines(tmp5)

                    timesign = str(time1).split()[1].split('.')[0]
                    work_dir = os.getcwd()
                    fig_dir = self._Tele.config.Rootpath2 + self.middir + 'fitting_fig' + '/'
                    if not os.path.exists(fig_dir):
                        os.mkdir(fig_dir)
                    folder = fig_dir
                    pngname = folder + timesign + '_' + str(int(az_src)) + '_' + str(int(el_src)) + '_' + sourcename + '.png'
                    plt.savefig(pngname)
                    _f.close()
                    _fscan.close()
                    sleep(3)
                    plt.close('all')
                    return '1'

    #--------------------fitting scanned profile of source--------------------
    def fit(self,x,y,mean,sigma,amp,a,b,c,d,e,f,g,h,k,l):
        try:
            popt,pcov = curve_fit(self.gaus,x,y,p0=[mean,sigma,amp,a,b,c,d,e,f,g,h,k,l])
        except Exception as msg:
            print('Exception: %s' % msg)
            return 'False'
        else:
            return self.gaus(x,*popt),popt,pcov
    #------------------------Gaussian fitting function------------------------
    def gaus(self,x,x0,sig,amp,a,b,c,d,e,f,g,h,k,l):
    	return amp * np.exp(-0.5*(x-x0)*(x-x0)/(sig*sig)) + a*x**9 + b*x**8 + c*x**7 + d*x**6 + e*x**5 + f*x**4 + g*x**3 + h*x**2 + k*x + l