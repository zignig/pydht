#!/usr/bin/python -i

from pydht import DHT 
import json,uuid,yaml 
import M2Crypto
import register
import logging
import socket
import sys
import tools

import scheduler

# register logging 
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

def DEBUG():
    ch.setLevel(logging.DEBUG)

def ERROR():
    ch.setLevel(logging.ERROR)

def INFO():
    ch.setLevel(logging.INFO)

#load node
name_space = 'name_space'
sys.ps1 = name_space+'>>>'
reg = register.registration()
host,port = '',7000 
strap = 'bl3dr.com'
d = DHT(host,port,reg,id=reg.node_id,boot_host=strap,boot_port=port)
# disable scheduler 
scheduler.bind_jobs(d)

#nodes = d.iterative_find_nodes(2)
#print nodes

# recurse through structure path
def make_path(base,dict,path_dict):
    if type(dict) == type({}):
        k = dict.keys()
        for i in k:
            p = make_path(base+'.'+i,dict[i],path_dict)
            path_dict[base+'.'+i] = p 
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
    " python json turns int keys into strings"
    try:
        dodj_data = json.loads(open('data.txt').read())
        k = dodj_data.keys()
        data = {}
        for i in k:
            d.data[int(i)] = dodj_data[i]
    except:
        print 'fail'


global level,max_recursion
level = 1
max_recursion = 6 

def walk_test(path='.base'):
    global level , max_recursion
    try:
        t = d[path]
        print(path)
        if type(t) == type([]):
            for i in t:
                level = level + 1
                walk_test(path+'.'+i)
                level = level - 1
                if level > max_recursion:
                    break
    except:
        logger.error('walk fail on - '+path)

#load_data(d)

def save():
    f = open('data.txt','w')
    f.write(json.dumps(d.data))
    f.close()

if __name__ == "__main__":
    walk_test()
    pass
