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

class key_store:
    "sqlite storage for known keys"
    base_schema = """
    CREATE TABLE keys (node_id text,pub_key text,pub_doc,timestamp int,score int);
    CREATE TABLE nodes (node_tripple text,timestamp int,quality int);
    """

    def __init__(self,path='public_keys',name='keys.sdb'):
        db_path = path+os.sep+name
        try:
            os.stat(db_path)
            self.path = db_path
            self.key_db = sqlite3.connect(db_path)
        except:
            logger.info('create key store '+db_path)
            self.path = db_path
            self.key_db = sqlite3.connect(db_path)
            c = self.key_db.cursor()
            c.executescript(self.base_schema)
            self.key_db.commit()
            logger.info('loading public keys')
            self.load_keys()
       

    def load_keys(self):
        li = os.listdir('public_keys/')
        for i in li:
            if i[-3:] == 'key':
                logger.info('loading key '+i)
                kn,kk = self.load_key('public_keys/'+i)
                self.insert_key(kn,kk)
        self.key_db.commit()

    def load_key(self,path='public_keys/germinate.key'):
        germ_key = M2Crypto.RSA.load_pub_key(path)
        germ_pem = germ_key.as_pem()
        germ_node = str(int(hashlib.sha1(germ_key.as_pem()).hexdigest(),16))
        return germ_node,germ_pem

    def insert_key(self,node_id,pub_key,score=1):
        conn = sqlite3.connect(self.path)
        c = conn.cursor()
        c.execute('insert into keys (node_id,pub_key,score) values (?,?,?)',(node_id,pub_key,score))
        conn.commit()
        conn.close()

    def find_key(self,key):
        logger.debug('check database for key '+str(key))
        c = self.key_db.cursor()
        c.execute('select * from keys where node_id = ? and score > 0',(str(key),))
        key_struct = c.fetchone()
        if key_struct == None:
            return key_struct,False
        else:
            logger.debug('found key in database '+str(key))
            #logger.error('find_key : need to check quality etc of key')
            logger.debug('key structure :'+json.dumps(key_struct))
            key_as_file = M2Crypto.BIO.MemoryBuffer(str(key_struct[1]))
            key_obj = M2Crypto.RSA.load_pub_key_bio(key_as_file)
            logger.debug(key_obj)
            return key_obj,True

    def dump(self):
        c = self.key_db.cursor()
        c.execute('select * from keys')
        r = c.fetchall()
        return r 

def password_callback(*args,**kwds):
    return 

class registration:
    """
    check for keys
    generate sha
    register  to the network
    """
    def __init__(self,path='.'):
        self.key = None
        self.temp_keys = {}
        self.keystack = []
        try:
            os.stat('keys')
        except:
            logger.info('create keys folder')
            os.mkdir('keys')
        try:
            os.stat('keys/private.pem')
            os.stat('keys/public.key')
        except:
            logger.info('generating new private key')
            key = M2Crypto.RSA.gen_key(1024,65537)
            key.save_key('keys/private.pem',cipher=None)
            #key.save_key('keys/private.pem')
            key.save_pub_key('keys/public.key')
        try:
            os.stat('keys/public.key')
            self.pub = M2Crypto.RSA.load_pub_key('keys/public.key') 
            self.node_id = int(hashlib.sha1(self.pub.as_pem()).hexdigest(),16)
            logger.info('set id '+str(self.node_id))
        except:
            logger.error('fail local key')
        self.key_store = key_store()

    
    def load_priv(self):
        self.priv = M2Crypto.RSA.load_key('keys/private.pem')

    def gen_doc(self,key,doc):
        logger.info('generate doc')
        made_doc = {}
        made_doc['origin'] = self.node_id
        made_doc['key'] = key
        made_doc['data'] = doc
        made_doc['timestamp'] = time.ctime()
        enc_js = json.dumps(made_doc,sort_keys=True,indent=1)
        logger.debug('doc to sign :'+enc_js)
        signer = M2Crypto.EVP.load_key('keys/private.pem')
        signer.sign_init()
        signer.sign_update(enc_js)
        sig = signer.sign_final()
        b64_sig = base64.b64encode(sig)
        logger.debug(hashlib.sha1(enc_js).hexdigest())
        made_doc['sig'] = b64_sig
        logger.debug('base sig : '+b64_sig)
        return made_doc 
   
    def fetch_key(self,origin):
        try:
            k = self.dht[str(origin)]
            logger.info('found key from network '+str(origin))
            key_as_file = M2Crypto.BIO.MemoryBuffer(str(k['data']))
            key_obj = M2Crypto.RSA.load_pub_key_bio(key_as_file)
            self.temp_keys[origin] = key_obj 
            self.dht.reg.key_store.insert_key(str(origin),k['data'])
            return key_obj
        except:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            logger.critical(exc_type)
            logger.critical(exc_value)
            logger.critical(exc_traceback)
            logger.error('key find fail on '+ str(origin))
            raise MissingKey
            
    def check_origin(self,origin):
        logger.debug('check key '+str(origin))
        key,status = self.key_store.find_key(origin)
        if status == True:
            logger.info('key '+str(origin)+' exists')
            return key
        else:
            if origin in self.temp_keys:
                return self.temp_keys[origin]
            else:
                logger.error('no key , fetching  '+str(origin))
                return  self.fetch_key(origin)
            raise MissingKey 

    def verify_doc(self,doc):
        logger.debug('verify doc')
        if doc == None:
            return None
        sdoc = doc.copy()
        if 'sig' in sdoc:
            sig = sdoc['sig']
            del sdoc['sig']
            logger.debug('has sig  : '+sig)
            dec_sig = base64.b64decode(sig)
            logger.debug(doc)
            if 'origin' in sdoc:
                key = self.check_origin(sdoc['origin'])
                formatted_doc = json.dumps(sdoc,sort_keys=True,indent=1)
                logger.debug('doc to check :'+formatted_doc)
                logger.debug(hashlib.sha1(formatted_doc).hexdigest())
                verify_evp = M2Crypto.EVP.PKey()
                verify_evp.assign_rsa(key,capture=0)
                verify_evp.verify_init()
                verify_evp.verify_update(formatted_doc) 
                result = verify_evp.verify_final(dec_sig)
                if result == 1:
                    logger.info('Correctly Decoded')
                    return doc
                else:
                    logger.error('Failed verify')
                    logger.error(formatted_doc)

            raise ValueError
        raise ValueError
