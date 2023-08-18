import time
import threading
import sqlite3
from sqlite3 import Error

import threading
import sqlite3
from sqlite3 import Error




def lockedup(func):                           
    def wrapper(cls, *args, **kwargs):
        with cls.lock:
            cls.islocked = True
            out =  func(cls, *args, **kwargs)
            cls.islocked = False
            return out 
    return wrapper              

class db(object):
    """description of class"""
    @classmethod
    def __init__(cls):
        cls.conn = sqlite3.connect('D:\\SMIT_DB\\SMITE.db', check_same_thread=False)
        cls.lock = threading.Lock()
        cls.islocked = False #tells threads that are putting in entrys to turn them into chunks for faster writes

    @classmethod
    @lockedup
    def execute(cls,sql):
        cursor=cls.conn.cursor()
        try:
            cursor.execute(sql)
            cls.conn.commit()
        except Error as e:
            print("Error with: "+sql)
            print("Error: "+str(e))

    @classmethod   
    @lockedup
    def insert(cls,sql, ignore=()):   
        cursor=cls.conn.cursor()               
        try:
            cursor.execute(sql)
            cls.conn.commit()
        except Error as e:
            if(not str(e) in ignore):     #sometimes when the program stops their can be a condishion to wher only haft the data is written creating this error #TODO need to clear errors
                print("Error with: "+sql)
                print("Error: "+str(e))

    @classmethod
    @lockedup
    def get(cls,sql):
        cursor=cls.conn.cursor()
        try:
            cursor.execute(sql)
            cls.conn.commit()
        except Error as e:
            print("Error with: "+sql)
            print("Error: "+str(e))
        out=cursor.fetchall()
        return out



