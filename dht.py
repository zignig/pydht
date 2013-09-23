#!/usr/bin/python -i

from pydht import DHT 
import json,uuid,yaml 
import M2Crypto
import register
import logging

# register logging 
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


#load node
reg = register.registration()

host,port = '',7000
strap = 'bl3dr.com'
d = DHT(host,port,reg,id=reg.node_id,boot_host=strap,boot_port=port)
#post the public key up by it's own hash
d[str(reg.node_id)] = reg.gen_doc(reg.pub.as_pem())


nodes = d.iterative_find_nodes(2)
print nodes

# recurse through structure path
def make_path(base,dict,path_dict):
    if type(dict) == type({}):
        k = dict.keys()
        for i in k:
            p = make_path(base+'/'+i,dict[i],path_dict)
            path_dict[base+'/'+i] = p 
        return k 
    else:
        print 'data:',base,dict
        path_dict[base] = dict
        return dict 

# load structure file
def load_structure(d,file_path='structure.yml'):
    structure = yaml.load(open(file_path))
    path_dict = {}
    make_path('',structure,path_dict)
    for i in path_dict.keys():
        print i
        d[i] = path_dict[i]
    return path_dict


#path_dict = load_structure(d)

def load_data(d):
    try:
        " python json turns int keys into strings"
        dodj_data = json.loads(open('data.txt').read())
        k = dodj_data.keys()
        data = {}
        for i in k:
            d.data[int(i)] = dodj_data[i]
    except:
        print 'fail'


#load_data(d)

def save():
    f = open('data.txt','w')
    f.write(json.dumps(d.data))
    f.close()

