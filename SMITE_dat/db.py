import time
import threading
import sqlite3
from sqlite3 import Error

class db(object):
    """description of class"""
    @classmethod
    def __init__(cls):
        cls.conn = sqlite3.connect('D:\\SMIT_DB\\SMITE.db', check_same_thread=False)
        cls.queue=[]
    @classmethod    
    def exicute(cls,sql):
        cls.queued()
        cursor=cls.conn.cursor()
        try:
            cursor.execute(sql)
            cls.conn.commit
        except Error as e:
            print("Error with: "+sql)
            print("Error: "+str(e))
        cls.queue.remove(threading.get_ident())
    @classmethod    
    def insert(cls,sql, ignore=()):
        cls.queued()
        cursor=cls.conn.cursor()               
        try:
            cursor.execute(sql)
            cls.conn.commit()
        except Error as e:
            if(not str(e) in ignore):
                print("Error with: "+sql)
                print("Error: "+str(e))
        cls.queue.remove(threading.get_ident())
    @classmethod
    def get(cls,sql):
        cls.queued()
        cursor=cls.conn.cursor()
        try:
            cursor.execute(sql)
            cls.conn.commit
        except Error as e:
            print("Error with: "+sql)
            print("Error: "+str(e))
        out=cursor.fetchall()
        cls.queue.remove(threading.get_ident())
        return out
    @classmethod
    def queued(cls):
        threadId =threading.get_ident()
        wait=False
        if(len(cls.queue) == 0):
            cls.queue=[threadId]
        else:
           cls.queue.append(threadId)
           wait=True
        while wait:
            time.sleep(0.1)
            if(cls.queue[0]==threadId):
                wait=False


