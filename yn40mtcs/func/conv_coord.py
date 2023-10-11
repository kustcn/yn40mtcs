#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# transform from ICRS to Observtor basing SOFA library and JPL DE405
"""
Author : Huang Yuxiang, Li Kejia, Wang Bojun
Date   : Nov. 25th 2018
Date   : Dec. 3th  2018
Date   : Aug. 22th 2019
"""


import numpy as np
import sys
import matplotlib.pylab as plt
from time import sleep
import time

from astropy.utils import iers
from astropy.utils.iers import IERS_A
import astropy.units
import astropy.time
from astropy.coordinates import SkyCoord,EarthLocation,AltAz

from . import sofaswig as sofa
from . import jplephswig as jpleph
from . import eop

from yn40mtcs.core.utils import data_path

iers.conf.auto_download = False

class CoordGeometry:
    def __init__(self, iersfile='iers.txt', ephfile='DE435.1950.2050'):
        self.fileEOP = data_path(iersfile)
        self.fileEPH = data_path(ephfile)
        self.EOP = eop.EOP(filepath=self.fileEOP)
        self.JPLEPH = jpleph.JPLEph(self.fileEPH)

        self.sofa=sofa.SOFA()
        iers.IERS_A_URL = data_path('finals2000A.all')
        iers_a = iers.IERS_A.open(iers.IERS_A_URL)
        iers.IERS.iers_table = iers.IERS_A.open(iers.IERS_A_URL)

    def radec2azel(self, COS, SC=[102,47,45.6,25,1,40.8,1974.0], MCOW=[800,25,0.5,50000], curtim='now', boldebug=False, backend='SOFA'):
        '''
        curtim: UTC time
        '''
        if backend=='ASTROPY':
            strlon = '%fd'%(SC[0]+SC[1]/60.+SC[2]/3600.)
            strlat = '%fd'%(SC[3]+SC[4]/60.+SC[5]/3600.)
            observing_location = EarthLocation(lat=strlat, lon=strlon, height=SC[6]*astropy.units.m)
            c3 = SkyCoord(COS, unit=(astropy.units.hour, astropy.units.deg), frame='icrs')
            if curtim=='now':
                observing_time = astropy.time.Time.now()
                # print("Current time: %s" % observing_time.value)
            else:
                loct = curtim.split(' ')
                locymd = loct[0].split('-')
                lochms = loct[1].split(':')
                strtime = '%s-%s-%sT%s:%s:%s'%(locymd[0], locymd[1], locymd[2], lochms[0], lochms[1], lochms[2])
                observing_time = astropy.time.Time(strtime, format='isot', scale='utc')

            aa = AltAz(location=observing_location, obstime=observing_time)
            jj = c3.transform_to(aa)
            az_astropy = jj.az.cdeg/100
            el_astropy = jj.alt.cdeg/100
            return az_astropy, el_astropy
        #--------------------SOFA backend

        sofa1= self.sofa
        ## Site Coordinate
        elon_d = SC[0]
        elon_m = SC[1]
        elon_s = SC[2]
        ephi_d = SC[3]
        ephi_m = SC[4]
        ephi_s = SC[5]
        ht = SC[6]
        sofa1.SetSite(elon_d,elon_m,elon_s,ephi_d,ephi_m,ephi_s,ht)
        if boldebug:
            print("--------------------Set Site Coordinate--------------------")
            sofa1.PrintSite()
            print(" ")

        # Set Meteorological Condition and Observational Wavelength
        pres = MCOW[0]
        temp = MCOW[1]
        humi = MCOW[2]
        wavl = MCOW[3] # micrometer
        sofa1.SetSiteCondition(pres,temp,humi,wavl)

        if boldebug:
            print("--------------------Set Condition of Site--------------------")
            sofa1.PrintSSC()
        
        # Set Catalog of Observational Source
        ralist = (COS.split())[0].split(':')
        declist =( COS.split())[1].split(':')
        ra_h = float(ralist[0])
        ra_m = float(ralist[1])
        ra_s = float(ralist[2])
        dec_d = float(declist[0])
        dec_m = float(declist[1])
        dec_s = float(declist[2])
        sofa1.ObservationCatalog(ra_h,ra_m,ra_s,dec_d,dec_m,dec_s)
        if boldebug:
            print("--------------------Set Catalog of Observational Source--------------------")
            sofa1.PrintObsC()

        # Catalog Correction of Observational Source
        pmra = 0 #-354.45e-3
        pmdec = 0 #595.35e-3
        rv = 0.0
        px = 0.0
        sofa1.ObsCorrection(pmra,pmdec,rv,px)

        # Set time (Julian Date)
        sofa1.CurrentTimeInit()
        if curtim=='now':
            # sofa1.SetTime()
            observing_time = astropy.time.Time.now()
            # print("Current time: %s" % observing_time.value)
            observing_time = str(observing_time)
            loct=observing_time.split(' ')
            locymd=loct[0]
            lochms=loct[1]
            arg=[float(v) for v in locymd.split('-')]+[float(v) for v in lochms.split(':')]
            sofa1.InputTime(*arg)
        else:
            loct=curtim.split(' ')
            locymd=loct[0]
            lochms=loct[1]
            arg=[float(v) for v in locymd.split('-')]+[float(v) for v in lochms.split(':')]
            sofa1.InputTime(*arg)

        sofa1.JulianDate_UTC()
        if boldebug:
            sofa1.PrintTime()
            sofa1.PrintInputTime()
            sofa1.PrintJDUTC()

        jd1 = sofa1.GetJD1()
        jd2 = sofa1.GetJD2()
        utc=jd1-2400000.5+jd2

        # Reference System Correction
        dut1, pmx, pmy, cipx, cipy=self.EOP.getEOP(utc)
        sofa1.CoordinateCorrection(pmx,pmy,cipx,cipy,dut1)
        if boldebug:
            print("--------------------Correction of Reference System--------------------")
            sofa1.PrintCooCor()

        # Celestial Intermediate Pole and Origion
        sofa1.TerrestrialTime()
        if boldebug:
            sofa1.PrintTT()

        tdb1=sofa1.GetTDB1()
        tdb2=sofa1.GetTDB2()
        if boldebug:
            print("Utc=",jd1, jd2,"    TDB=",tdb1, tdb2)

        sofa1.CIP_CIO()
        if boldebug:
            print('CIO=')
            sofa1.PrintCIO()

        # Read JPL DE405 file
        ncent = 12
        pv = np.linspace(1,24,24)
        j = 0
        jpl = self.JPLEPH
        for ntarg in [6,5,11,3]:
            flag = jpl.Calculate(tdb1,tdb2,ntarg,ncent)
            for i in range(6):
                pv[i+j]=jpl.GetValue(i)
            j = j+6

        p_v = pv.reshape(8,3)
        if boldebug:
            print('Saturn, Jupiter, Sun, Earth position and velocity')
            print('from', self.fileEPH)
            print(p_v)
        pv00 = p_v[0:2][:]
        pv11 = p_v[2:4][:]
        pv22 = p_v[4:6][:]
        pb11 = p_v[6:8][:]

        # Create the 2D Array of C++ double
        pv0 = sofa.Create2DArray23()
        pv1 = sofa.Create2DArray23()
        pv2 = sofa.Create2DArray23()
        pb1 = sofa.Create2DArray23()
        for i1 in range(3):
            for j1 in range(2):
                sofa.SetElem2DArray23(pv0,j1,i1,pv00[j1][i1])
                sofa.SetElem2DArray23(pv1,j1,i1,pv11[j1][i1])
                sofa.SetElem2DArray23(pv2,j1,i1,pv22[j1][i1])
                sofa.SetElem2DArray23(pb1,j1,i1,pb11[j1][i1])

        #pb1 earth position-velocity
        #pv0 saturn position-velocity
        #pv1 Jupiter position-velocity
        #pv2 sun position velocity
        if boldebug:
            print('--------------------Earth position-velocity--------------------')
            print(pb11)
            print('--------------------Saturn position-velocity-------------------')
            print(pv00)
            print('--------------------Jupiter position-velocity------------------')
            print(pv11)
            print('----------------------Sun position-velocity--------------------')
            print(pv22)

        sofa1.TerrestialEphemeris(pb1,pv0,pv1,pv2)
        Az = sofa1.Getaz()
        El = sofa1.Getel()
        if boldebug:
            print('Az(deg)=',Az, 'El(deg)=', El)

        return Az, El

if __name__=='__main__':
    print('testing conv_coord.py')
    cos = '05:34:32.00 22:00:58.00'
    name = 'crab'
    sc = [102, 47, 45.384, 25, 1, 38.388, 1974.0]
    m = [0, 0, 0, 1]
    if sys.argv[1]=='True':
        coodgeo=CoordGeometry()
        plt.ion()
        fig = plt.figure()
        # plt.title(name)
        plt11 = []
        plt12 = []
        plt13 = []
        plt21 = []
        plt22 = []
        plt23 = []
        ax1 = fig.add_subplot(231)
        ax2 = fig.add_subplot(232)
        ax3 = fig.add_subplot(233)
        ax4 = fig.add_subplot(234)
        ax5 = fig.add_subplot(235)
        ax6 = fig.add_subplot(236)
        f = open('astropy_sofa.dat','w')
        f.writelines('source\taz_astropy\tel_astropy\taz_sofa\tel_sofa\taz_delta\tel_delta\n')
        for i in range(150000):
            obstime = str(astropy.time.Time.now())
            start = time.clock()
            az0, el0 = coodgeo.radec2azel(COS=cos,SC=sc,MCOW=m,curtim=obstime,boldebug=False) # curtim='2013/04/02 23:15:43.5' sys.argv[1]
            stop = time.clock()
            sofatime = start - stop
            # print "Fix time astropy az=",az, 'el=',el
            start1 = time.clock()
            az1, el1 = coodgeo.radec2azel(COS=cos,SC=sc,MCOW=m,curtim=obstime,boldebug=False,backend='ASTROPY') # curtim='2013/04/02 23:15:43.5'
            stop1 = time.clock()
            astrotime = start1 - stop1
            az = az0*1000 - int(az0*1000)
            el = el0*1000 - int(el0*1000)
            az1 = az1*1000 - int(az0*1000)
            el1 = el1*1000 - int(el0*1000)
            d_az = az - az1
            d_el = el - el1
            ftxt = '%s\t%s\t%d\t%d\t%f\t%f\t%f\t%f\t%f\t%f\t%f\t%f' % (obstime,name,int(az0*1000),int(el0*1000),az,el,az1,el1,d_az,d_el,sofatime,astrotime)
            f.writelines(ftxt)
            f.writelines('\n')
            plt11.append(az)
            plt12.append(az1)
            plt13.append(d_az)
            plt21.append(el)
            plt22.append(el1)
            plt23.append(d_el)
            ax1.clear()
            ax2.clear()
            ax3.clear()
            ax4.clear()
            ax5.clear()
            ax6.clear()
            ax1.plot(plt11)
            ax2.plot(plt12)
            ax3.plot(plt13)
            ax4.plot(plt21)
            ax5.plot(plt22)
            ax6.plot(plt23)
            ax1.set_title('AZ_sofa')
            ax2.set_title('AZ_astropy')
            ax3.set_title('AZ_delta')
            ax4.set_title('EL_sofa')
            ax5.set_title('EL_astropy')
            ax6.set_title('EL_delta')
            sleep(0.2)
            plt.show()
            plt.pause(0.05)
            # print "Fix time sofa az=",az, 'el=',el
            # for i in range(0,10):
            #     print ""
            # az, el = coodgeo.radec2azel(COS=cos,SC=sc,MCOW=m,curtim='now') # , boldebug=sys.argv[1])
            # print "Now az=",az, 'el=',el
        f.close()

