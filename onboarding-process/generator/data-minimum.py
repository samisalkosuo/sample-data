from time import time
import uuid    
import datetime
from time import time 
import random

#generates minimum sample data for IBM Process Mining
#includes only mandatory fields: Process ID,Start time,Activity

maxProcesses = 12345

print("Process ID,Start time,Activity")


def getTimestampString(timestamp):
    timestampString = timestamp.strftime("%d/%m/%Y %H:%M:%S")
    #timestamp.isoformat()
    return timestampString

def createNewProcess(startTime = int(time())):   
    processID = uuid.uuid4().hex
    activity = "Create new account"
    #startTime = int(time())
    timestamp = datetime.datetime.fromtimestamp(startTime)
    print("%s,%s,%s" % (processID, getTimestampString(timestamp), activity))

    #manual step duration
    duration = startTime + random.randint(900, 3600)
    startTime = duration


    validateNameAndAddressTime = startTime + random.randint(5, 60)
    dt = datetime.datetime.fromtimestamp(validateNameAndAddressTime)
    activity = "Validate name and address"
    print("%s,%s,%s" % (processID, getTimestampString(dt), activity))
    #success 99.5%
    if (random.randint(0, 1000) > 995 ):
        return


    securityClearanceTime = startTime + random.randint(5, 60)
    dt = datetime.datetime.fromtimestamp(securityClearanceTime)
    activity = "Security clearance"
    print("%s,%s,%s" % (processID, getTimestampString(dt), activity))
    #success 99.5%
    if (random.randint(0, 1000) > 995 ):
        return

    verifyAccountTime = startTime + random.randint(5, 60)
    dt = datetime.datetime.fromtimestamp(verifyAccountTime)
    activity = "Verify account"
    print("%s,%s,%s" % (processID, getTimestampString(dt), activity))
    #success 99.5%
    if (random.randint(0, 1000) > 995 ):
        return
    
    #get max
    maxTime = max(validateNameAndAddressTime,securityClearanceTime,verifyAccountTime)

    reviewCustomerTime = maxTime + random.randint(5, 60)
    dt = datetime.datetime.fromtimestamp(reviewCustomerTime)
    activity = "Review customer"
    print("%s,%s,%s" % (processID, getTimestampString(dt), activity))
    if (random.randint(0, 100) > 95 ):
        #5% fails
        return
    
    #manual reviews step duration
    lessThan1hour=random.randint(300, 3600)
    between1hourand2hours=random.randint(3600, 7200)
    morethan2hours=random.randint(7200, 15345)
    distribution = random.randint(0, 100)
    duration = reviewCustomerTime + lessThan1hour
    if distribution > 90 :
        duration = reviewCustomerTime + morethan2hours
    if distribution > 50:
        duration = reviewCustomerTime + between1hourand2hours

    #duration = startTime + random.randint(300, 5 * 3600)
    startTime = duration

    onboardCustomerTime = startTime + random.randint(5, 60)
    dt = datetime.datetime.fromtimestamp(onboardCustomerTime)
    activity = "Onboard new customer"
    print("%s,%s,%s" % (processID, getTimestampString(dt), activity))

    welcomeCustomerTime = onboardCustomerTime + random.randint(5, 60)
    dt = datetime.datetime.fromtimestamp(welcomeCustomerTime)
    activity = "Welcome new customer"
    print("%s,%s,%s" % (processID, getTimestampString(dt), activity))


currentProcess = 0
while currentProcess < maxProcesses:
    
    year = 2021#random.randint(2022, 60)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    hour = random.randint(8, 10)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    startTime = datetime.datetime(year, month, day, hour=hour, minute=minute, second=second)

    createNewProcess(startTime.timestamp())
    currentProcess = currentProcess + 1

