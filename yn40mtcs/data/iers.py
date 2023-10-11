#!/usr/bin/env python3.7
# -*- coding: utf-8 -*-
'''
    from "finals2000A.all" to "iers.txt"
    Author : Huang Yuxiang, Li Kejia, Dai Wei, Wei Shoulin
    Date   : Nov. 8th 2019
             Sep. 10th 2023
'''


if __name__ =='__main__':
    eop = 'finals2000A.all'
    iers = 'iers.txt'
    f_eop = open(eop,'r')
    with open(iers,'w') as f_iers:
        for i in range(18602):
            line = f_eop.readline()
            # line = line.split('')
            line1 = '%s %s %s %s %s %s' % (line[7:15],line[18:27],line[38:46],line[58:68],line[100:106],line[119:125])
            f_iers.writelines(line1)
            f_iers.writelines('\n')
    f_eop.close()