import sqlite3
import time
import json
from datetime import datetime, timedelta
from SMITE import SMITE
from sqlite3 import Error
from db import db
from nodeGen import nodeGen
from threading import Thread

loadingBar=""
def main():
    db()
    AI=nodeGen()
    runAI(AI)
    #SMITE()
    
    #time.sleep(1)
    #Thread(target = MatchStats, args =()).start()
    
    #out=SMITE.getMatchdetails(1258056648).json()

def insertGods():
    gods =SMITE.getGods().json()
    print(gods[0]["godCard_URL"])
    for x in gods:
        temp=x["godCard_URL"].split("/")[-1][0:-4]
        sql="INSERT INTO gods VALUES('"+temp+"',"+str(x["id"])+")"
        print(sql)
        db.insert(sql)
def insertItems():
    items=SMITE.getItems().json()
    sql="drop table items"
    db.exicute(sql)
    sql= "CREATE TABLE items ('ActiveFlag' varchar(1), 'ChildItemId' SMALLINT , 'DeviceName' varchar(128), 'Glyph' varchar(1), 'IconId' SMALLINT, 'ItemId' SMALLINT NOT NULL PRIMARY KEY, 'ItemTier' SMALLINT, 'Price' SMALLINT, 'RootItemId' SMALLINT, 'StartingItem' boolean, 'Type' varchar(64), 'itemIcon_URL' varchar(255), 'ret_msg' varchar(64));"
    db.exicute(sql)
    for x in items:
        sql1="INSERT INTO items ('ActiveFlag', 'ChildItemId', 'DeviceName', 'Glyph', 'IconId', 'ItemId', 'ItemTier', 'Price', 'RootItemId', 'StartingItem', 'Type', 'itemIcon_URL', 'ret_msg')"
        sql2="VALUES ('"+str(x['ActiveFlag'])+"', "+str(x['ChildItemId'])+", '"+str(x['DeviceName'])+"', '"+str(x['Glyph'])+"', "+str(x['IconId'])+", "+str(x['ItemId'])+", "+str(x['ItemTier'])+", "+str(x['Price'])+", "+str(x['RootItemId'])+", "+str(x['StartingItem'])+", '"+str(x['Type'])+"', '"+str(x['itemIcon_URL'])+"', '"+str(x['ret_msg'])+"')"
        sql3=sql1+sql2
        sql3=sql3.replace("'s", "''s")              
        sql3=sql3.replace("s' ", "s'' ")
        db.insert(sql3)
    print("Updated table items")
def getGodesItems():
    map={}
    items={}
    itemsKeys=('ItemId','DeviceName' ,'Glyph', 'IconId', 'ItemTier' ,'Price', 'RootItemId', 'StartingItem')
    gods={}
    godsKeys=('id' ,'name')

    sql="SELECT ItemId,DeviceName ,Glyph, IconId, ItemTier ,Price, RootItemId, StartingItem from items"
    itemsDb=db.get(sql)
    for x in itemsDb:
        for i in range(0,len(itemsKeys)):
            items[itemsKeys[i]]=x[i]
    
    sql="SELECT id ,name from gods"
    gods=db.get(sql)
    for x in gods:
        for i in range(0,len(godsKeys)):
            items[godsKeys[i]]=x[i]

    map["items"]=items
    map["gods"]=gods
    
    return map
def recordMatchs(lastSave=True,day="20220627"):
    path= "lastSave.txt"
    monthLen={"1":31,"2":28,"3":31,"4":30,"5":31,"6":30,"7":31,"8":31,"9":30,"10":31,"11":30,"12":31}
    queueID= (426,435,448,445,10189,434,10189,504,451,10193,10197,503,441,450,10190,10152,438,429,446,460)

    if(lastSave):
        try:
            file=open(path, "r")
            day=str(file.read())
            file.close()
        except FileNotFoundError:
            file=open(path, "x")
            file.close
            print("Making File and start recording at: "+day)
    dayIs=(datetime.utcnow()-timedelta(1))
    while( not day==(dayIs.strftime("%G")+dayIs.strftime("%m")+dayIs.strftime("%d"))):
        with open(path,"w") as file:
            file.write(day)
            pass
        for x in queueID:
            lookUpMatchIdQueue(day,x)
        
        Year=day[0:4]
        YearInt=int(Year)
        Month=day[4:6]
        MonthInt=int(day[4:6])
        Day=day[6:8]
        DayInt= int(day[6:8])
                                            
        if(DayInt/monthLen[str(MonthInt)]==1or(YearInt%4==0 and DayInt/(monthLen[str(MonthInt)]+1)==1)):    #Deals with months and leap years            
           MonthInt=MonthInt+1
           DayInt=1
        else:
            DayInt=DayInt+1
        if(MonthInt/13==1):
            YearInt=YearInt+1
            MonthInt=1
        if(MonthInt<10):
            Month="0"+str(MonthInt)
        else:
            Month=str(MonthInt)
        if(DayInt<10):
            Day="0"+str(DayInt)
        else:
            Day=str(DayInt)
        day=Year+Month+Day

    print("Done recording matchs: ")
def lookUpMatchIdQueue(day,queueID):
    out=SMITE.getMatchidsbyQueue(day,-1, queueID).json()
   
    sql1= "INSERT INTO  matchIds(ID, date, queueID) VALUES"
    sql2=""
    for x in out:
        if x["Active_Flag"]=="n":
            sql2= sql2+"("+str(x["Match"])+", "+str(day)+", "+str(queueID)+"), "
            
    sql3=sql1+sql2[0:-2]+";"
    
    if(not sql3==sql1+";"):
        db.insert(sql3, ("UNIQUE constraint failed: matchIds.ID"))
    else:
        print("No data for: "+str(day)+" ID: "+str(queueID))
def MatchStats(lastSave=True,day="20220628"):

    sql=("select matchIds.ID from matchIds left join matchInfo on matchIds.ID= matchInfo.ID where matchInfo.ID is null")
    matchIdsRaw=db.get(sql)
    matchIds=[]
    for x in matchIdsRaw:
        if(matchIds==[]):
            matchIds=[x[0]]
        else:
            matchIds.append(x[0])
    
    devide=int((int(len(matchIds)/10)-1)/20)
    for i in range(0, int(len(matchIds)/10)-1):      #Goes through matchIds by chunks of 10
        request=[]
        str1=""
        for x in matchIds[i*10:(i+1)*10]:            #Puts 10 Ids into a string
            if(not x==None):
                str1=str1+str(x)+","
        str1=str1[0:-1]
        Thread(target = callAndInsert, args =(str1,x)).start() 
        bar=""
        for i2 in range(0,20):                       #Makes a loading bar that counts by 5% so I know if the methode is still running 
            if  i>i2*devide:
                bar=bar+"#"
            else:
                bar=bar+" "
        loadingBar=("["+bar+"]")                     #Sets the bar
        
    print("Done: ")
def callAndInsert(str1,x):
    request=SMITE.getMatchDetailsBatch(str1)     #Gets the Match Details for 10 Ids
    if request== None:
        print("Cant get match details")
    else:
        sql1="INSERT INTO matchInfo(ID, Account_Level, ActivePlayerId, GodId, ItemId1, ItemId2, ItemId3, ItemId4, ItemId5, ItemId6, ActiveId1, ActiveId2, ActiveId3, ActiveId4, Win_Status, ret_msg)"
        sql2="VALUES"
        for x in request:
            try:
                sql2=sql2+"( "+str(x['Match'])+", " +str(x['Account_Level'])+", "+str(x[ 'ActivePlayerId'])+", "+str(x[ 'GodId'])+", "+str(x[ 'ItemId1'])+", "+str(x[ 'ItemId2'])+", "+str(x['ItemId3'])+", "+str(x['ItemId4'])+", "+str(x['ItemId5'])+", "+str(x['ItemId6'])+", "+str(x['ActiveId1'])+", "+str(x['ActiveId2'])+", "+str(x['ActiveId3'])+", "+str(x['ActiveId4'])+", "+str(x['Win_Status'])+", '"+str(x['ret_msg'])+"'),"
            except TypeError:
                print("Empty")
        sql2=sql2[0:-1]
        sql2=sql2.replace("Player Privacy Flag set for this player.","")
        sql2=sql2.replace("Winner", "1")
        sql2=sql2.replace("Loser","0")
        sql3=sql1+sql2
        db.insert(sql3,("UNIQUE constraint failed: matchInfo.ID, matchInfo.Win_Status, matchInfo.GodId"))
def watchPlayer():
    pass
def runAI(AI):
    mapGodItem = getGodesItems()
    sql="select matchInfo.ID, matchInfo.GodId, matchInfo.ItemId1, matchInfo.ItemId2, matchInfo.ItemId3, matchInfo.ItemId4, matchInfo.ItemId5, matchInfo.ItemId6, matchInfo.ActiveId1, matchInfo.ActiveId2, matchInfo.ActiveId3, matchInfo.ActiveId4, matchInfo.Win_Status from matchInfo inner join matchIds on matchIds.ID=matchInfo.ID  where matchIds.queueID=426 order by matchInfo.ID desc limit 10;"
    data=db.get(sql)
    winCal=AI.analyzeGame(data)
    print(winCal)
    
    
    pass
main()