from time import time
from tracemalloc import start
import uuid    
import datetime
from time import time 
import random

#generates  sample data for IBM Process Mining
#includes  mandatory fields: Process ID,Start time,Activity
#and end time
#and role: Employee, System, Manager
roleEmployee="Employee"
roleManager="Manager"
roleSystem="System"
#and resources
users=["Oscar","Amalia","Jonah","Cara","Natalia","George","Hilary"]
managers=["Olivia","Kiara","Zac"]
system1="CP4BA & CP4I"
system2="Custom Application 1"
system3="Custom Application 2"

print("Process ID,Start time,End time,Activity,Role,Resource")


def getTimestampString(timestamp):
    timestampString = timestamp.strftime("%m/%d/%Y %H:%M:%S")
    #timestamp.isoformat()
    return timestampString

def printActivity(processID,activityName,startTime,durationSecondsMin,durationSecondsMax,role,resource):
    startTimestamp = datetime.datetime.fromtimestamp(startTime)

    #manual step duration
    endtime = startTime + random.randint(durationSecondsMin, durationSecondsMax)
    endTimestamp = datetime.datetime.fromtimestamp(endtime)
    print("%s,%s,%s,%s,%s,%s" % (processID, getTimestampString(startTimestamp), getTimestampString(endTimestamp), activityName,role,resource))
    #return activity end time + random transition duration to next activity
    return endtime + random.randint(1, 10)

def createNewProcess(startTime = int(time())):   
    processID = uuid.uuid4().hex


    activity = "Create new account"
    durationMin=300#2min
    durationMax=600#10min
    distribution = random.randint(0, 100)
    if distribution > 27 :
        durationMin=600
        durationMax=2000
    if distribution > 66 :
        durationMin=2000
        durationMax=4000
    startTime = printActivity(processID,activity,startTime,durationMin,durationMax,roleEmployee,random.choice(users))
    #print(getTimestampString(datetime.datetime.fromtimestamp(activityEndTime)))

    activity = "Validate name and address"
    startTime1 = printActivity(processID,activity,startTime,5,60,roleSystem,system1)
    #about 0.5% fails activity
    if (random.randint(0, 1000) > 995 ):
        return

    activity = "Security clearance"
    startTime2 = printActivity(processID,activity,startTime,5,60,roleSystem,system1)
    #about 0.5% fails activity
    if (random.randint(0, 1000) > 995 ):
        return

    activity = "Verify account"
    startTime3 = printActivity(processID,activity,startTime,5,60,roleSystem,system1)
    #about 0.5% fails activity
    if (random.randint(0, 1000) > 995 ):
        return

    startTime = max(startTime1,startTime2,startTime3)

    activity = "Review customer"
    #manual reviews step duration
    durationMin=120#2min
    durationMax=600#10min
    distribution = random.randint(0, 100)
    if distribution > 50 :
        durationMin=600
        durationMax=1800
    if distribution > 75 :
        durationMin=1800
        durationMax=3600
    if distribution > 85 :
        durationMin=3600
        durationMax=7200
    if distribution > 90 :
        durationMin=7200
        durationMax=10000
    if distribution > 99 :
        durationMin=10000
        durationMax=20000

    startTime = printActivity(processID,activity,startTime,durationMin,durationMax,roleManager,random.choice(managers))
    #5% fails review
    if (random.randint(0, 100) > 95 ):
        return

    activity = "Onboard new customer"
    startTime = printActivity(processID,activity,startTime,5,60,roleSystem,system2)

    activity = "Welcome new customer"
    startTime = printActivity(processID,activity,startTime,5,60,roleSystem,system3)




maxProcesses = 12345
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

