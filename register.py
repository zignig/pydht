#  generate ids and keys for joining the network
# simon kirkby
# 201309211719
# tigger@interthingy.com

import M2Crypto
import json,string,os
import logging
import hashlib

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
            key = M2Crypto.RSA.load_key('keys/private.pem')
            self.key = key
        except:
            logging.info('generating new public key')
            key = M2Crypto.RSA.gen_key(1024,65537)
            key.save_key('keys/private.pem',cipher=None)
            self.key = key
        try:
            os.stat('keys/public.key')
        except:
            self.key.save_pub_key('keys/public.key')
            logging.info('generating public key')
            self.public = key.pub()
        print(self.key)    

reg = registration()
