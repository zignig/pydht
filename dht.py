#!/usr/bin/python -i

from pydht import DHT 
import json,uuid


try:
    os.stat('node_id.txt')
    node_id = json.loads((open('node_id.txt').read()))
except:
    node_id = uuid.uuid4().int
    f = open('node_id.txt','w')
    f.write(json.dumps(node_id))
    f.close()

host,port = '',7000
strap = 'bl3dr.com'
d = DHT(host,port,id=node_id,boot_host=strap,boot_port=port)
nodes = d.iterative_find_nodes(2)
print nodes

def load_data(d):
    " python json turns int keys into strings"
    dodj_data = json.loads(open('data.txt').read())
    k = dodj_data.keys()
    data = {}
    for i in k:
        data[int(i)] = dodj_data[i]
    d.data = data

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

