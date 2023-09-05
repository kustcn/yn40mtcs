class Acu39Tel:
    def __init__(self):
        self.az=0
        self.el=0

    def PointTo(self, az, el):
        pass

    def GetCurrentPosition(self):
        return (self.az, self.el)
    
    def GetStauts(self):
        return self.status
    
    def SetStatus(self, status):
        return True