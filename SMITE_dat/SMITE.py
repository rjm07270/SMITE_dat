from asyncio import threads
from concurrent.futures import thread
import requests
import time
import datetime 
import os
import json
import threading

from db import db
from threading import Thread
from hashlib import md5
from dotenv import load_dotenv


def check(func):
    def wrapper(cls, *args, **kwargs):
        print('Inside wrapper')
        if( cls.requestCount <= cls.maxRequests):
            if not cls.sessionLoaded:
                print('Session not loaded, starting thread')
                Thread(target=cls.session).start()
                counter = 0
                while cls.sessionId is None and counter < cls.maxRequests:
                    print('Waiting for session ID...')
                    time.sleep(1)
                    counter += 1
                if(cls.sessionLoaded and counter < cls.maxRequests):
                    cls.requestCount=cls.requestCount+1
                    return func(cls, *args, **kwargs)
                    
            elif (not cls.sessionId==None):
                print('Session loaded, calling function directly')
                cls.requestCount=cls.requestCount+1
                return func(cls, *args, **kwargs)
        else:
              sql = """
                UPDATE sessions
                SET request_count = <cls.requestCount>
                WHERE session_number = (
                    SELECT session_number
                    FROM sessions
                    ORDER BY session_date DESC
                    LIMIT 1
                );
                """
              db.execute(sql)

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
                sql = "SELECT session FROM sessions"                       # Select the session from the sessions in the database
                raw = db.get(sql)
                cls.sessionId = str(raw[-1][0])                            # Get the session ID from the last session
                cls.maxRequests= int(str(raw[-1][0]))
                cls.sessionLoaded = True                                   # Indicate that the session has been loaded
            sql = "DELETE FROM sessions WHERE session= '" + cls.sessionId + "'" # Delete the session with the current session ID from the database
            db.execute(sql)
            sql = "INSERT INTO sessions VALUES('" + str(cls.sessionId) + "'," + str(timeNow) + "'," + str(cls.maxRequests) +")" # Insert the current session ID and time into the database
            db.insert(sql)
            time.sleep(sleepTime)                                          # Sleep for the sleep time
            sleepTime = defaultSleep                                       # Reset the sleep time to the default sleep time


    #Test sessions
    @classmethod
    def ping(cls):
        out=requests.get(cls.site+"/ping"+cls.responseFormat)
        return out
          
    @classmethod
    def testsession(cls):
        print(cls.site+"/testsession"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("testsession")+"/"+cls.sessionId+"/"+cls.genUtc())
        out =requests.get(cls.site+"/testsession"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("testsession")+"/"+cls.sessionId+"/"+cls.genUtc())
        return out
    
    
    @classmethod
    @check
    def getGods(cls):
        out =requests.get(cls.site+"/getgods"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getgods")+"/"+cls.sessionId+"/"+cls.genUtc()+"/1")
        return out
    @classmethod
    @check
    def getItems(cls):
         out =requests.get(cls.site+"/getitems"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getitems")+"/"+cls.sessionId+"/"+cls.genUtc()+"/1")
         return out
    @classmethod
    @check
    def getMotd(cls):
        out =requests.get(cls.site+"/getmotd"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getmotd")+"/"+cls.sessionId+"/"+cls.genUtc())
        return out

    @classmethod
    @check
    def getTopMatches(cls):
        out =requests.get(cls.site+"/gettopmatches"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("gettopmatches")+"/"+cls.sessionId+"/"+cls.genUtc())
        return out

    @classmethod
    @check
    def getMatchidsbyQueue(cls,date,hour,queueId):
        out =requests.get(cls.site+"/getmatchidsbyqueue"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getmatchidsbyqueue")+"/"+cls.sessionId+"/"+cls.genUtc()+"/"+str(queueId)+"/"+str(date)+"/"+str(hour))
        return out

    @classmethod
    @check
    def getMatchDetailsBatch(cls,str1):
        request=None
        try:
            # Print each part of the string
            print("cls.site: ", cls.site)
            print("cls.responseFormat: ", cls.responseFormat)
            print("cls.devId: ", cls.devId)
            print("cls.getSignature('getmatchdetailsbatch'): ", cls.getSignature("getmatchdetailsbatch"))
            print("cls.sessionId: ", cls.sessionId)
            print("cls.genUtc(): ", cls.genUtc())
            print("str1: ", str1)
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
        return out
           
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
     






