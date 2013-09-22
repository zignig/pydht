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

import readline,rlcompleter

readline.parse_and_bind('tab:complete')

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
        try:
            os.stat('keys')
        except:
            logging.info('create keys folder')
            os.mkdir('keys')
        try:
            os.stat('keys/private.pem')
            os.stat('keys/public.key')
        except:
            logging.info('generating new private key')
            key = M2Crypto.RSA.gen_key(1024,65537)
            key.save_key('keys/private.pem',cipher=None)
            #key.save_key('keys/private.pem')
            key.save_pub_key('keys/public.key')
        try:
            os.stat('keys/public.key')
            self.pub = M2Crypto.RSA.load_pub_key('keys/public.key') 
            self.node_id = int(hashlib.sha1(self.pub.as_pem()).hexdigest(),16)
            logging.info('set id')
        except:
            print('fail local key')
        print(self.node_id)    
    
    def load_priv(self):
        self.priv = M2Crypto.RSA.load_key('keys/private.pem')

        
    def gen_doc(self,doc):
        doc['origin'] = self.node_id
        enc_js = json.dumps(doc,sort_keys=True,indent=1)
        signer = M2Crypto.EVP.load_key('keys/private.pem')
        signer.sign_init()
        signer.sign_update(enc_js)
        sig = signer.sign_final()
        b64_sig = base64.b64encode(sig)
        doc['sig'] = b64_sig
        return doc
   
    def verify_doc(self,doc):
        print(doc)
        sdoc = doc.copy()
        if 'sig' in sdoc:
            sig = sdoc['sig']
            del sdoc['sig']
            print sdoc
            decoded_sig = base64.b64decode(sig)
            formatted_doc = json.dumps(sdoc,sort_keys=True,indent=1)
            resp = self.pub.verify(formatted_doc,decoded_sig)
            print resp
