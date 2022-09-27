import requests
import time
import datetime 
import os
import json

from db import db
from threading import Thread
from hashlib import md5
from dotenv import load_dotenv




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
        
        cls.session = Thread(target = cls.session, args =()).start()
        cls.limit= 0
    @classmethod
    def session(cls):
        print("Loading sessions")
        path= "cashe//seshionTime.txt"
        lastConn =None
        defaultSleep=15*60
        sleepTime=defaultSleep
        db()
        
        timeNow=int (time.time())
        sql="DELETE FROM sessions WHERE time<"+str(timeNow-sleepTime)
        
        db.exicute(sql)
        sql="SELECT time FROM sessions"
        resualt= db.get(sql)        
        if not resualt==[]:
            lastConn=resualt[-1][0]
          
        if(lastConn in range(timeNow-sleepTime, timeNow)):
            sleepTime= (lastConn-timeNow) % sleepTime                         #Finds the remander time left in seshion from prevuse run
            
        while(cls.retryConn):
            if sleepTime==defaultSleep:
                raw= cls.makeSession()
                cls.sessionId=str(raw['session_id'])
            else:
                sql="SELECT session FROM sessions"
                raw= db.get(sql)
                cls.sessionId=str(raw[-1][0])
                cls.sessionLoaded=True
            sql= "DELETE FROM sessions WHERE session= '"+cls.sessionId+"'"
            db.exicute(sql)
            sql="INSERT INTO sessions VALUES('"+str(cls.sessionId)+"',"+str(timeNow)+")"
            db.insert(sql)
            time.sleep(sleepTime)
            sleepTime=defaultSleep
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
    def getGods(cls):
        out =requests.get(cls.site+"/getgods"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getgods")+"/"+cls.sessionId+"/"+cls.genUtc()+"/1")
        return out
    @classmethod
    def getItems(cls):
         out =requests.get(cls.site+"/getitems"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getitems")+"/"+cls.sessionId+"/"+cls.genUtc()+"/1")
         return out
    @classmethod
    def getMotd(cls):
        out =requests.get(cls.site+"/getmotd"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getmotd")+"/"+cls.sessionId+"/"+cls.genUtc())
        return out
    @classmethod
    def getTopMatches(cls):
        out =requests.get(cls.site+"/gettopmatches"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("gettopmatches")+"/"+cls.sessionId+"/"+cls.genUtc())
        return out
    @classmethod
    def getMatchidsbyQueue(cls,date,hour,queueId):
        out =requests.get(cls.site+"/getmatchidsbyqueue"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getmatchidsbyqueue")+"/"+cls.sessionId+"/"+cls.genUtc()+"/"+str(queueId)+"/"+str(date)+"/"+str(hour))
        return out
    @classmethod
    def getMatchDetailsBatch(cls,str1):
        request=None
        try:
            request =requests.get(cls.site+"/getmatchdetailsbatch"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getmatchdetailsbatch")+"/"+cls.sessionId+"/"+cls.genUtc()+"/"+str1).json()
            
        except:
            print(str1)
            print(cls.site+"/getmatchdetailsbatch"+cls.responseFormat+"/"+cls.devId+"/"+cls.getSignature("getmatchdetailsbatch")+"/"+cls.sessionId+"/"+cls.genUtc()+"/"+str1)
        
        return request
    @classmethod
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
    

    #Checks if it is the session is still up
    def check(func):
        def wrapper(*args, **kwargs):
            return func(*args,**kwargs)
        return wrapper



