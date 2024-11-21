def withinTimeRange(currHour, currMinute, checkHour, checkMinute, topRange, bottomRange):
    topRange = wrapTime(checkHour, checkMinute + topRange)
    bottomRange = wrapTime(checkHour, checkMinute + bottomRange)
    if bottomRange[0] > topRange[0]:
        currHour += 24
        topRange[0] += 24
    elif bottomRange[0] < currHour or bottomRange[0] == currHour and bottomRange[1] <= currMinute:
        if topRange[0] > currHour or topRange[0] == currHour and topRange[1] >= currMinute:
            return True
    return False

def wrapTime(hour, minute):
    if minute >= 60:
        minute -= 60
        hour += 1
    elif minute < 0:
        minute += 60
        hour -= 1
    if hour >= 24:
        hour -= 24
    elif hour <= 0:
        hour += 24
    return hour, minute

def clamp(n, min, max): 
    if n < min: 
        return min
    elif n > max: 
        return max
    else: 
        return n 