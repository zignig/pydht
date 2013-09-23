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
            logging.info('set id '+str(self.node_id))
        except:
            logging.error('fail local key')
    
    def load_priv(self):
        self.priv = M2Crypto.RSA.load_key('keys/private.pem')

    def gen_doc(self,doc):
        logging.info('generate doc')
        made_doc = {}
        made_doc['origin'] = self.node_id
        made_doc['data'] = doc
        enc_js = json.dumps(made_doc,sort_keys=True,indent=1)
        logging.debug('doc to sign :'+enc_js)
        signer = M2Crypto.EVP.load_key('keys/private.pem')
        signer.sign_init()
        signer.sign_update(enc_js)
        sig = signer.sign_final()
        b64_sig = base64.b64encode(sig)
        logging.debug(hashlib.sha1(enc_js).hexdigest())
        made_doc['sig'] = b64_sig
        logging.debug('base sig : '+b64_sig)
        return made_doc 
   
    def fetch_key(self,origin):
        logging.debug('fetch key '+str(origin))
        path = 'public_keys/'+str(origin)+'.key'
        try:
            os.stat(path)
            key = M2Crypto.RSA.load_pub_key(path)
            logging.debug('found key '+str(origin))
            return True,key
        except:
            logging.error('key fail for :'+str(origin))
            logging.error('FETCH key out of DHT')
            return False,''

    def check_origin(self,origin):
        logging.debug('check key '+str(origin))
        if origin in self.known_keys:
            logging.debug('known origin '+str(origin))
            return self.known_keys[origin]
        else:
            status,key = self.fetch_key(origin)
        if status:
            self.known_keys[origin] = key
            return key
        else:
            raise ValueError

    def verify_doc(self,doc):
        logging.debug('verify doc')
        sdoc = doc.copy()
        if 'sig' in sdoc:
            sig = sdoc['sig']
            del sdoc['sig']
            logging.debug('has sig  : '+sig)
            dec_sig = base64.b64decode(sig)
            if 'origin' in sdoc:
                key = self.check_origin(sdoc['origin'])
                formatted_doc = json.dumps(sdoc,sort_keys=True,indent=1)
                logging.debug('doc to check :'+formatted_doc)
                logging.debug(hashlib.sha1(formatted_doc).hexdigest())
                verify_evp = M2Crypto.EVP.PKey()
                verify_evp.assign_rsa(key,capture=0)
                verify_evp.verify_init()
                verify_evp.verify_update(formatted_doc) 
                logging.debug('final verify')
                result = verify_evp.verify_final(dec_sig)
                logging.info(result)
                if result == 1:
                    logging.info('Correctly Decoded')
                    return doc
                else:
                    logging.error('Failed verify')
            raise ValueError
