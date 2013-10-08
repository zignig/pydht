#!/usr/bin/python -i
#  generate ids and keys for joining the network
# simon kirkby
# 201309211719
# tigger@interthingy.com

import M2Crypto
import json,string,os
import logging 
import hashlib
import base64
import sqlite3
import StringIO
import time
import os,sys
import traceback

import readline,rlcompleter

base_schema = ""
readline.parse_and_bind('tab:complete')

logger = logging.getLogger(__name__)

class doc_store:
    "sqlite storage for known docs"
    base_schema = """
    CREATE TABLE docs (key text,doc text,timestamp int);
    """

    def __init__(self,path='public_keys',name='docs.sdb'):
        db_path = path+os.sep+name
        try:
            os.stat(db_path)
            self.path = db_path
            self.key_db = sqlite3.connect(db_path)
        except:
            logger.info('create doc store '+db_path)
            self.path = db_path
            self.key_db = sqlite3.connect(db_path)
            c = self.key_db.cursor()
            c.executescript(self.base_schema)
            self.key_db.commit()

    def dump(self):
        c = self.key_db.cursor()
        c.execute('select * from docs')
        r = c.fetchall()
        return r 

    def insert_doc(self,key,doc):
        "disabled for now"
        return 
        data = doc['data']
        key2 = doc['key']
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute('insert into docs (key,doc,timestamp) values (?,?,?)',(str(key),json.dumps(doc),time.time()))
        conn.commit()
        conn.close()

    def get_doc(self,key):
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute('select doc from docs where key = ?',(str(key),))
        doc = c.fetchone()
        conn.commit()
        conn.close()
        if doc == None:
            return None
        return json.loads(str(doc[0]))

    def expire(self):
        " get rid of old docs"
        logger.error('expire not written')
