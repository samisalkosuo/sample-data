import random
from utils import *
import datetime
import sys
from time import time 



fileName = "../data/phonenumbers.csv"
phoneNumbers = []

TOTAL_INSERT_SQLS=1
if len(sys.argv) == 2:
    TOTAL_INSERT_SQLS = int(sys.argv[1])

#random sqls
if TOTAL_INSERT_SQLS == -1:
    TOTAL_INSERT_SQLS = random.choice(list(range(23)))

#read all phone numbers 
with open(fileName, 'r', encoding='utf-8', errors='replace') as f:
    phoneNumbers = f.read().splitlines()  # or f.readlines(), then strip later

def timestampToString(unix_timestamp: int) -> str:
    """
    Converts a Unix timestamp (in seconds) into a
    string formatted as YYYY-MM-DD HH:MM:SS (UTC).
    """
    # Convert Unix timestamp to a UTC datetime object
    dt_utc = datetime.datetime.fromtimestamp(unix_timestamp)
    # Format the datetime object as a string
    return dt_utc.strftime('%Y-%m-%d %H:%M:%S')

#create CDR insert SQL
#print(TOTAL_INSERT_SQLS)

#create CDR for the last hour


durations1 = list(range(60))
durations2 = list(range(120))
durations3 = list(range(300))
durations4 = list(range(600))
durations5 = list(range(1200))
durations6 = list(range(3600))
durationList = [durations1,durations2,durations3,durations4,durations5,durations6]


for i in range(TOTAL_INSERT_SQLS):
    durationsList1 = random_choice_distribution(durationList,"gaussian")
    callDuration = random_choice_distribution(durationsList1,"gaussian")
    endTime = int(time())
    startTime = endTime - callDuration
    anumber = random.choice(phoneNumbers)
    bnumber = random.choice(phoneNumbers)
    while bnumber == anumber:
        bnumber = random.choice(phoneNumbers)
    #insert into 
    print(f"insert into calldetailrecord (anumber,bnumber,starttime,endtime,duration) values('{anumber}','{bnumber}','{timestampToString(startTime)}','{timestampToString(endTime)}',{callDuration});");#,end = ""
    # print(callDuration)
    # print(startTime)

#print("")
