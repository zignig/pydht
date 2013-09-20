#!/usr/bin/python -i

from pydht import DHT 
import json,uuid,yaml 


try:
    os.stat('node_id.txt')
    node_id = json.loads((open('node_id.txt').read()))
except:
    node_id = uuid.uuid4().int
    f = open('node_id.txt','w')
    f.write(json.dumps(node_id))
    f.close()

# recurse through structure path
def make_path(base,dict,path_dict):
    if type(dict) == type({}):
        k = dict.keys()
        for i in k:
            p = make_path(base+'/'+i,dict[i],path_dict)
            path_dict[base+'/'+i] = p 
        return k 
    else:
        print 'fail:',base,dict
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

host,port = '',7000
strap = 'bl3dr.com'
d = DHT(host,port,id=node_id,boot_host=strap,boot_port=port)
nodes = d.iterative_find_nodes(2)
print nodes

path_dict = load_structure(d)

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

load_data(d)

glob = {}

def add(key,value):
	glob[key] = 1
	d['glob'] = glob.keys()
	d[key] = value

def save():
    f = open('data.txt','w')
    f.write(json.dumps(d.data))
    f.close()

