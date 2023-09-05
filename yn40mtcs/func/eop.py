import numpy as np

from yn40mtcs.core.utils import data_path

class EOP(object):
    def __init__(self, filepath= data_path('iers.txt')):
        # tel1=tel.Telescope()
        self.iers=np.loadtxt(filepath)
        self.vmjd=self.iers[:,0]
        self.vpmx=self.iers[:,1]
        self.vpmy=self.iers[:,2]
        self.vut1utc=self.iers[:,3]
        self.vdx=self.iers[:,4]
        self.vdy=self.iers[:,5]

    def getEOP(self, mjd):
        pmx=np.interp(mjd, self.vmjd, self.vpmx)
        pmy=np.interp(mjd, self.vmjd, self.vpmy)
        ut1utc=np.interp(mjd, self.vmjd, self.vut1utc)
        dx=np.interp(mjd, self.vmjd, self.vdx)
        dy=np.interp(mjd, self.vmjd, self.vdy)
        return  ut1utc, pmx, pmy,dx*1e-3,dy*1e-3

if __name__=='__main__':
    eop=EOP()
    print(eop.getEOP(56385))
