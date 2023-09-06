from ast import With
from asyncio import threads
from concurrent.futures import thread
import requests
import time
import datetime
from datetime import timedelta 
import os
import json
import threading

from db import db
from threading import Thread
from hashlib import md5
from dotenv import load_dotenv


def check(func):
    def wrapper(cls, *args, **kwargs):
        runFunc=False   #test to see if we should run the funchion so threads do not have to wait for each funchion to complete
        with cls.lock:
            if( cls.requestCount < cls.maxRequests):
            
                if not cls.sessionLoaded:
                    Thread(target=cls.session).start()
                    print('Session not loaded, starting thread')
                
                    counter = 0
                    while cls.sessionId is None and counter < cls.maxRequests:
                        print('Waiting for session ID...')
                        time.sleep(1)
                        counter += 1
                       
                    if(cls.sessionLoaded and cls.requestCount < cls.maxRequests):
                        cls.requestCount=cls.requestCount+1
                        runFunc=True
                    
                elif (not cls.sessionId==None):
                    cls.requestCount=cls.requestCount+1
                    if(cls.requestCount%100):                           #This wrapper can get hit a lot with a lot of dirrent calls so we only update the disk every few requests
                        sql = """
                        UPDATE sessions
                        SET request_count = """+str(cls.maxRequests - cls.requestCount)+"""
                        WHERE session = (
                            SELECT session
                            FROM sessions
                            ORDER BY time DESC
                            LIMIT 1
                        );
                        """
                        db.execute(sql)
                    runFunc=True

            else:
                sql = """
                UPDATE sessions
                SET request_count = """+str(cls.maxRequests - cls.requestCount)+"""
                WHERE session = (
                    SELECT session
                    FROM sessions
                    ORDER BY time DESC
                    LIMIT 1
                );
                """
                db.execute(sql)
        if  runFunc:
            out = func(cls, *args, **kwargs)
            if isinstance(out, list):
                if len(out) > 0:
                    tester = out[0]["ret_msg"]
                # Perform action for lists
            elif isinstance(out, dict):
                tester = out["ret_msg"]
            else:
                print("Do that again IDK what happened")
            return out 
        else:
            print("Refuaing to run methode likly out of requests or sessions :( ")
    return wrapper


class SMITE(object):
    """description of class"""
    #grab info from smite API
    @classmethod
    def __init__(cls):
        load_dotenv()
        cls.site="https://api.smitegame.com/smiteapi.svc" #smite API
        cls.responseFormat="Json"                 #formate returned by the API
    
        cls.sessionId = None
        cls.sessionLoaded=False
        cls.retryConn = True
        cls.devId=os.getenv('devId')
        cls.authKey=os.getenv('authKey')
        cls.loadingBar=""
                                                                     
        cls.requestCount= 0
        cls.maxRequests=7500
        cls.lock = threading.Lock()
        if cls.devId==None or  cls.authKey ==None:
            print("Missing feilds in env file")
         

    @classmethod
    def session(cls):
        cls.sessionLoaded = False
        print("Loading sessions")                                          # Indicate that sessions are being loaded
        path = "cashe//seshionTime.txt"                                    # Define the path to the session time cache file
        lastConn = None                                                    # Initialize lastConn to None
        defaultSleep = 15 * 60                                             # Define the default sleep time as 15 minutes
        sleepTime = defaultSleep                                           # Initialize sleepTime to the default sleep time
        db()                                                               # Initialize the database
        timeNow = int(time.time())                                         # Get the current time as an integer
        sql = "DELETE FROM sessions WHERE time<" + str(timeNow - sleepTime) # Delete any sessions from the database that are older than the sleep time
        db.execute(sql)
        sql = "SELECT time FROM sessions"                                  # Select the time from the sessions in the database
        result = db.get(sql)
        if not result == []:                                               # If there are any sessions in the database
            lastConn = result[-1][0]                                       # Get the time of the last session
        if lastConn in range(timeNow - sleepTime, timeNow):                # If the last session is within the sleep time
            sleepTime = (lastConn - timeNow) % sleepTime                   # Calculate the remaining sleep time
        while cls.retryConn:                                               # While retryConn is True
            if sleepTime == defaultSleep:                                  # If the sleep time is the default sleep time
                raw = cls.makeSession()                                    # Make a new session
                cls.sessionId = str(raw['session_id'])                     # Get the session ID from the new session
                cls.maxRequests = 7500
            else:
                sql = "SELECT session, request_count FROM sessions"                       # Select the session from the sessions in the database
                raw = db.get(sql) 
                cls.sessionId = str(raw[-1][0])                            # Get the session ID from the last session
                cls.maxRequests= int(str(raw[-1][1])) 
            out = cls.testsession()
            if(out.status_code==200):
                if not ("successful test" in str(out.content)):
                    print(out.content)
                else:
                    cls.sessionLoaded = True

                
            sql = "DELETE FROM sessions WHERE session= '" + cls.sessionId + "'" # Delete the session with the current session ID from the database
            db.execute(sql)
            if(not cls.sessionId is None):
                sql = "INSERT INTO sessions VALUES('" + str(cls.sessionId) + "', '" + str(timeNow) + "', " + str(cls.maxRequests) + ")" # Insert the current session ID and time into the database
                db.insert(sql)
            else:
                cls.sessionLoaded = False
                out = cls.ping()
                print(out.status_code)
                if(out.status_code==200):
                    print("API refused to give session check max session count of 30 and request count of 7500")
                    print("Will retry connection at 00:00 UTC time")
                    now_utc = datetime.utcnow()                         # Calculate the current UTC time
                    start_of_day_utc = datetime(now_utc.year, now_utc.month, now_utc.day) + timedelta(days=1)  # Calculate the start of the next day in UTC time
                    time_difference = (start_of_day_utc - now_utc).total_seconds()  # Calculate the time difference between now and the start of the next day
                    time.sleep(time_difference)                         # Sleep the thread until the start of the next day in UTC time
                else:
                    print("dumping error from the ping request to the server")
                    print("Status Code {out.status_code}")  
                    print(out.json())
                    
            if(cls.sessionId is None):
                print("Their is no Session ID")
            time.sleep(sleepTime)                                          # Sleep for the sleep time
            sleepTime = defaultSleep                                       # Reset the sleep time to the default sleep time


    #Test sessions
    @classmethod
    def ping(cls):
        out=requests.get(cls.site+"/ping"+cls.responseFormat)
        return out
          
    @classmethod
    def testsession(cls):
        variables = [cls.site, cls.responseFormat, cls.devId, cls.getSignature("testsession"), cls.sessionId, cls.genUtc()]
        variable_names = ["site", "responseFormat", "devId", "getSignature", "sessionId", "genUtc"]
        flag =False

        for var, name in zip(variables, variable_names):
            if var is None:
                print(f"{name} is None")
                flag=True                 
        print(cls.site+"/testsession"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("testsession")+"/"+cls.sessionId+"/"+cls.genUtc())
        if not flag:
            out =requests.get(cls.site+"/testsession"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("testsession")+"/"+cls.sessionId+"/"+cls.genUtc())

        return out
    
    
    @classmethod
    @check
    def getGods(cls):
        out =requests.get(cls.site+"/getgods"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getgods")+"/"+cls.sessionId+"/"+cls.genUtc()+"/1")
        return out.json()
    @classmethod
    @check
    def getItems(cls):
         out =requests.get(cls.site+"/getitems"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getitems")+"/"+cls.sessionId+"/"+cls.genUtc()+"/1")
         return out.json()
    @classmethod
    @check
    def getMotd(cls):
        out =requests.get(cls.site+"/getmotd"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getmotd")+"/"+cls.sessionId+"/"+cls.genUtc())
        return out.json()

    @classmethod
    @check
    def getTopMatches(cls):
        out =requests.get(cls.site+"/gettopmatches"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("gettopmatches")+"/"+cls.sessionId+"/"+cls.genUtc())
        return out.json()

    @classmethod
    @check
    def getMatchidsbyQueue(cls,date,hour,queueId):
        #print(cls.site+"/getmatchidsbyqueue"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getmatchidsbyqueue")+"/"+cls.sessionId+"/"+cls.genUtc()+"/"+str(queueId)+"/"+str(date)+"/"+str(hour))
        out =requests.get(cls.site+"/getmatchidsbyqueue"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getmatchidsbyqueue")+"/"+cls.sessionId+"/"+cls.genUtc()+"/"+str(queueId)+"/"+str(date)+"/"+str(hour))
        return out.json()

    @classmethod
    @check
    def getMatchDetailsBatch(cls,str1):
        request=None
        try:
            #teststr= cls.site+"/getmatchdetailsbatch"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getmatchdetailsbatch")+"/"+cls.sessionId+"/"+cls.genUtc()+"/"+str1
            #print(teststr)
            request =requests.get(cls.site+"/getmatchdetailsbatch"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getmatchdetailsbatch")+"/"+cls.sessionId+"/"+cls.genUtc()+"/"+str1).json()
            
        except:
            print(str1)
            print(cls.site+"/getmatchdetailsbatch"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getmatchdetailsbatch")+"/"+cls.sessionId+"/"+cls.genUtc()+"/"+str1)
        
        return request

    @classmethod
    @check
    def getMatchdetails(cls,matchId):
        print(cls.site+"/getmatchdetailsbatch"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getmatchdetailsbatch")+"/"+cls.sessionId+"/"+cls.genUtc()+"/"+str(matchId))
        out =requests.get(cls.site+"/getmatchdetailsbatch"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getmatchdetailsbatch")+"/"+cls.sessionId+"/"+cls.genUtc()+"/"+str(matchId))
        return (out.json())
           
    @classmethod
    def makeSession(cls):
        hash = cls.getSignature("createsession")
        raw = requests.get(cls.site+"/createsession"+cls.responseFormat+"/"+cls.devId+"/"+hash+"/"+cls.genUtc()) 
        out=raw.json()
        if not out['ret_msg'] == 'Approved':
            print(out['ret_msg'])
            print("Pinging server: "+ str(cls.ping().json()))
        else:
            cls.sessionLoaded=True
        return out
                                           
    @classmethod     
    def getSignature(cls,command):
        utcTime= cls.genUtc()
        str1=str(cls.devId)+command+str(cls.authKey)+utcTime
        str2=str1.encode("utf-8")
        hash = md5(str2).hexdigest()
        return hash
    
    
    @classmethod        
    def genUtc(cls):
        dayIs=datetime.datetime.utcnow()
        return dayIs.strftime("%G")+dayIs.strftime("%m")+dayIs.strftime("%d")+dayIs.strftime("%H")+dayIs.strftime("%M")+dayIs.strftime("%S")
     






