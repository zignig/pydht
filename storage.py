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
import redis

import readline,rlcompleter

base_schema = ""
readline.parse_and_bind('tab:complete')

logger = logging.getLogger(__name__)

class doc_store:
    time_out = 86400
    repli_set = 'replicate'
    score_set = 'score'
    def __init__(self,path='docs'):
        self.r = redis.Redis()
        self.path = path
                
    def insert_doc(self,key,doc):
        full_path = self.path+':'+str(key)
        self.r.set(full_path,json.dumps(doc))
        self.r.zadd(self.repli_set,key,time.time())
        self.r.expire(full_path,self.time_out)

    def tap(self,key):
        self.r.zadd(self.repli_set,key,time.time())

    def before(self,span=3600):
        cur_time = time.time()
        start_time = cur_time-span 
        docs = self.r.zrangebyscore(self.repli_set,0,time.time()-span)
        return docs
     
    def replicate(self,age=3600):
        re_rep = self.before(age)
        for i in re_rep[0:20]:
            doc = self.get_doc(i)
            if doc:
                logger.critical(doc)
                self.dht_obj.dht.post_item(long(i),doc) 
                self.tap(i)
  
    def get_doc(self,key):
        full_key = self.path+':'+str(key)
        if self.r.exists(full_key):
            doc = self.r.get(full_key)
            return json.loads(str(doc))
        else:
            return None

    def dump(self):
        return self.r.keys(self.path+':*')
