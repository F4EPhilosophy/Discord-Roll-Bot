class User:
    id = -1
    nickName = ""
    discordName = ""
    extraRolls = 0
    dkp = 0

    def __init__(self, id, nickName, discordName, extraRolls, dkp):
        self.updateUser(id, nickName, discordName, extraRolls, dkp)

    def formatForFile(self):
        string = str(self.id) + "," + self.nickName + "," + self.discordName + "," + str(self.extraRolls) + "," + str(self.dkp) + "\n"
        return string
    
    def updateUser(self, id, nickName, discordName, extraRolls, dkp):
        self.id = id
        self.nickName = nickName if nickName != None else discordName
        self.discordName = discordName
        self.extraRolls = extraRolls
        self.dkp = dkp