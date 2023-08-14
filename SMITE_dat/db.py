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
            return func(cls, *args, **kwargs) 
    return wrapper              

class db(object):
    """description of class"""
    @classmethod
    def __init__(cls):
        cls.conn = sqlite3.connect('D:\\SMIT_DB\\SMITE.db', check_same_thread=False)
        cls.lock = threading.Lock()

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
            if(not str(e) in ignore):
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



