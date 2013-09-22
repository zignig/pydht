#!/usr/bin/python 

import register
import logging 

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

reg = register.registration()
reg.load_priv()

a = reg.gen_doc('this is a longer test')
print(a)
print reg.verify_doc(a)
