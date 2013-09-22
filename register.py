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
        self.known_keys = {}
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
        made_doc = {}
        made_doc['origin'] = self.node_id
        made_doc['data'] = doc
        enc_js = json.dumps(made_doc,sort_keys=True,indent=1)
        signer = M2Crypto.EVP.load_key('keys/private.pem')
        signer.sign_init()
        signer.sign_update(enc_js)
        sig = signer.sign_final()
        b64_sig = base64.b64encode(sig)
        made_doc['sig'] = b64_sig
        return made_doc 
   
    def fetch_key(self,origin):
        logging.info('fetch key '+str(origin))
        path = 'public_keys/'+str(origin)+'.key'
        try:
            os.stat(path)
            key = M2Crypto.RSA.load_pub_key(path)
            return True,key
        except:
            logging.error(path)
            return False,''

    def check_origin(self,origin):
        logging.info('checking for '+str(origin))
        if origin in self.known_keys:
            print('known origin')
            return self.known_keys['origin']
        else:
            status,key = self.fetch_key(origin)
        if status:
            self.known_keys[origin] = key
            return key
        else:
            raise ValueError

    def verify_doc(self,doc):
        print(doc)
        sdoc = doc.copy()
        if 'sig' in sdoc:
            sig = sdoc['sig']
            logging.info('has sig '+sig)
            dec_sig = base64.b64decode(sig)
            del sdoc['sig']
            if 'origin' in sdoc:
                key = self.check_origin(sdoc['origin'])
            formatted_doc = json.dumps(sdoc,sort_keys=True,indent=1)
            logging.info(formatted_doc)
            verify_evp = M2Crypto.EVP.PKey()
            verify_evp.assign_rsa = key
            verify_evp.verify_init()
            verify_evp.verify_update(formatted_doc)
            result = verify_evp.verify_final(dec_sig)
            print result
            if result == 1:
                logging.info('Correctly Decoded')
                return doc
            else:
                logging.error('Failed verify')
