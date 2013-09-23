#!/usr/bin/python 

import register
import logging 

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)

logger.addHandler(ch)


reg = register.registration()
reg.load_priv()

logging.info('base test')
logging.info('')
a = reg.gen_doc('hello')
print reg.verify_doc(a)

#breaker()
#logging.info('base test with altered data')
#logging.info('')
#a = reg.gen_doc('this is a test a longer test')
#a['data'] = 'fnord'
#print reg.verify_doc(a)

keys = reg.key_store.dump()
logging.info(keys)
