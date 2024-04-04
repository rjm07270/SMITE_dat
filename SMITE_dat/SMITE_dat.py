from concurrent.futures import ThreadPoolExecutor, as_completed, thread
#import imp
from PyQt5 import QtWidgets, QtCore, QtGui
from math import fabs
from pyexpat import features
import sqlite3
import time
import json
from datetime import datetime, timedelta
from SMITE import SMITE
from db import db
from nodeGen import nodeGen
from threading import Thread
from GameOverlay import GameOverlay
import sys

print("Loading Moduals")
def main():
    db()
    #AI=nodeGen()
    #AI.testCuda()
    #runAI(AI)
    app = QtWidgets.QApplication(sys.argv)
    ex = GameOverlay()
    sys.exit(app.exec_())

    #SMITE()
    #watchPlayer()    #make sure you test this out you are here
    #print("Loaded Moduals")
    #print(SMITE.getGods())
    #print(SMITE.testsession())
    #print(SMITE.getMatchidsbyQueue(20230628,-1,435))
    #recordMatchs()
    #MatchStats()
    #out=SMITE.getMatchdetails(1329004787)    #fix your shit the date is wrong with your methode to pull queues
    #out=SMITE.getMatchDetailsBatch("1329004787,1329004787,1329004787,1329004787,1329004787,1329004787,1329004787")
    #print(out)
    
    

def insertGods():
    gods =SMITE.getGods()
    print(gods[0]["godCard_URL"])
    for x in gods:
        temp=x["godCard_URL"].split("/")[-1][0:-4]
        sql="INSERT INTO gods VALUES('"+temp+"',"+str(x["id"])+")"
        print(sql)
        db.insert(sql)
def insertItems():
    items=SMITE.getItems()
    sql="drop table items"
    db.execute(sql)
    sql= "CREATE TABLE items ('ActiveFlag' varchar(1), 'ChildItemId' SMALLINT , 'DeviceName' varchar(128), 'Glyph' varchar(1), 'IconId' SMALLINT, 'ItemId' SMALLINT NOT NULL PRIMARY KEY, 'ItemTier' SMALLINT, 'Price' SMALLINT, 'RootItemId' SMALLINT, 'StartingItem' boolean, 'Type' varchar(64), 'itemIcon_URL' varchar(255), 'ret_msg' varchar(64));"
    db.execute(sql)
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
from datetime import datetime, timedelta

def recordMatchs(lastSave=False, day="20231208"):         #Seems like at some point smite dropped their data so the date had to be changed
    path = "lastSave.txt"
    queueID = (426, 435, 448, 445, 10189, 434, 10189, 504, 451, 10193, 10197, 503, 441, 450, 10190, 10152, 438, 429, 446, 460)

    if lastSave:
        try:
            with open(path, "r") as file:
                day = file.read()
        except FileNotFoundError:
            five_days_ago = datetime.now() - timedelta(days=5)
            day = five_days_ago.strftime("%Y%m%d")
            with open(path, "x") as file:
                print("Making File and start recording at: " + day)

    current_day = datetime.utcnow() - timedelta(1)
    current_day_str = current_day.strftime("%Y%m%d")

    while day != current_day_str:
        with open(path, "w") as file:
            file.write(day)

        for x in queueID:
            lookUpMatchIdQueue(day, x)

        # Convert the day string back to a datetime object
        day_datetime = datetime.strptime(day, "%Y%m%d")

        # Add one day
        next_day = day_datetime + timedelta(days=1)

        # Convert the datetime object back to a string
        day = next_day.strftime("%Y%m%d")

    print("Done recording matches: ")

def lookUpMatchIdQueue(day,queueID):
    out=SMITE.getMatchidsbyQueue(day,-1, queueID)
   
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

def MatchStats(lastSave=True, day="20230628"):
    sql=("select matchIds.ID from matchIds left join matchInfo on matchIds.ID= matchInfo.ID where matchInfo.ID is null LIMIT "+str(10*(SMITE.maxRequests-SMITE.requestCount))+";")
    matchIdsRaw=db.get(sql)
    matchIds=[]
    for x in matchIdsRaw:
        if(matchIds==[]):
            matchIds=[x[0]]
        else:
            matchIds.append(x[0])                
    with ThreadPoolExecutor(max_workers=12) as executor:               
        futures = []
        for i in range(0, int(len(matchIds)/10)-1):      #Goes through matchIds by chunks of 10
            str1=""
            for x in matchIds[i*10:(i+1)*10]:            #Puts 10 Ids into a string
                if(not x==None):
                    str1=str1+str(x)+","
            str1=str1[0:-1]
            futures.append(executor.submit(callAndInsert, str1, x))  # Submit the function to the executor

        results = []
        insertSQL = """
            INSERT INTO matchInfo(
                ID, Account_Level, ActivePlayerId, GodId, ItemId1, ItemId2, ItemId3, 
                ItemId4, ItemId5, ItemId6, ActiveId1, ActiveId2, ActiveId3, ActiveId4, 
                Win_Status, ret_msg
            ) VALUES
            """
        BigSQL = insertSQL                                  #This string will hold multiable statments to merge small sql entrys
        for i, future in enumerate(as_completed(futures)):  # as the threads complete
            
            resultTemp = future.result()
            if resultTemp is not None:
                
                BigSQL = BigSQL + resultTemp + ","  # collect the results       
            
                        
                if(not (db.islocked and BigSQL == insertSQL)):
                    BigSQL = BigSQL[:-1] + ";"
                    db.insert((BigSQL), ("UNIQUE constraint failed: matchInfo.ID, matchInfo.Win_Status, matchInfo.GodId"))
                    BigSQL = insertSQL
                
            progress = (i + 1) / len(futures) # update the loading bar
            bar = '#' * int(progress * 20) + ' ' * (20 - int(progress * 20))    
            
            sys.stdout.write(f'\rprogress: [{bar}] {progress * 100:.1f}%')
            sys.stdout.flush()
        if(not BigSQL == insertSQL):
            BigSQL = BigSQL[:-1] + ";"
            db.execute(BigSQL, ("UNIQUE constraint failed: matchInfo.ID, matchInfo.Win_Status, matchInfo.GodId"))
            
    print("Done: ")                 
def callAndInsert(str1, x):
    request = SMITE.getMatchDetailsBatch(str1)  # Gets the Match Details for 10 Ids
    if request is None:
        print("Can't get match details")
        return
    
    cleanRequests = str1.split(",")
    # Define the SQL insert statement
    sql = ""
    errorFlag= False
    # Prepare the values for the insert statement
    values = []
    for x in request:
        try:
            if all(x[key] is not None for key in ["Win_Status", "GodId", "Match"]) and int(x['ActivePlayerId']) != 0:
                values.append((
                    x['Match'], x['Account_Level'], x['ActivePlayerId'], x['GodId'],
                    x['ItemId1'], x['ItemId2'], x['ItemId3'], x['ItemId4'], x['ItemId5'],
                    x['ItemId6'], x['ActiveId1'], x['ActiveId2'], x['ActiveId3'], x['ActiveId4'],
                    str(x['Win_Status']).replace("Winner", "1").replace("Loser", "0"),
                    f"'{x['ret_msg']}'"
                ))
            
                
        except TypeError:
            print("Empty")
            errorFlag=True #If their is an error than I did not get a request baack so I do not want to delete the ID becuse wrong IDs still return somthing from the server
            

    # Convert the values to SQL format
    values_sql = ", ".join(
        f"({', '.join(map(str, value))})"
        for value in values
    )   
    sql += values_sql   # Combine the SQL insert statement with the values                  
    # Execute the SQL insert statement
    #db.insert(sql, ("UNIQUE constraint failed: matchInfo.ID, matchInfo.Win_Status, matchInfo.GodId"))
    if sql=="" and not errorFlag:
        delete_sql = f"""
            DELETE FROM matchIds
            WHERE ID IN ({', '.join(map(str, cleanRequests))})
            """
        db.execute(delete_sql)
    return sql    

def watchPlayer():
    # Example arguments for each method
    search_player = "stoppedchain240"
    player_id = 712558766
    match_id = 1342722749

    # Calling the searchPlayers method and printing the response
    search_players_response = SMITE.searchPlayers(search_player)
    print("Search Players Response:", search_players_response)
    print()
    # Calling the getMatchHistory method and printing the response
    match_history_response = SMITE.getMatchHistory(player_id)
    print("Match History Response:", match_history_response)
    print()
    # Calling the getPlayerStatus method and printing the response
    player_status_response = SMITE.getPlayerStatus(player_id)
    #print("Player Status Response:", player_status_response)
    print()
    # Calling the getDemoDetails method and printing the response
    demo_details_response = SMITE.getDemoDetails(match_id)
    print("Demo Details Response:", demo_details_response)
    pass

def runAI(AI):
    mapGodItem = getGodesItems()
    sql="select matchInfo.ID, matchInfo.GodId, matchInfo.ItemId1, matchInfo.ItemId2, matchInfo.ItemId3, matchInfo.ItemId4, matchInfo.ItemId5, matchInfo.ItemId6, matchInfo.ActiveId1, matchInfo.ActiveId2, matchInfo.ActiveId3, matchInfo.ActiveId4, matchInfo.Win_Status from matchInfo inner join matchIds on matchIds.ID=matchInfo.ID  where matchIds.queueID=426 ORDER BY by matchInfo.ID desc limit 10;"
    data=db.get(sql)
    winCal=AI.analyzeGame(data)
    print(winCal)
    pass
main()