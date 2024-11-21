class Event:
    time = "0000"
    duration = 0
    name = ""
    dkp = 0
    recurring = False

    def __init__(self, time, duration, name, dkp, recurring):
        self.updateEvent(time, duration, name, dkp, recurring)

    def formatForFile(self):
        recurStr = "True" if self.recurring else "False"
        string = self.time + "," + str(self.duration) + "," + self.name + "," + str(self.dkp) + "," + recurStr + "\n"
        return string
    
    def updateEvent(self, time, duration, name, dkp, recurring):
        self.time = time
        self.duration = duration
        self.name = name
        self.dkp = dkp
        self.recurring = recurring
