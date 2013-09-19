#!/usr/bin/python -i

from pydht import DHT 

host,port = '',7000
strap = 'bl3dr.com'
d = DHT(host,port,boot_host=strap,boot_port=port)
nodes = d.iterative_find_nodes(2)
print nodes

glob = {}
try: 
	d['server']
	print d['server']
except:
	d['server'] = 'http://couch.bl3dr.com/zignig'

def add(key,value):
	glob[key] = 1
	d['glob'] = glob.keys()
	d[key] = value
