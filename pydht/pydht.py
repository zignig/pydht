import json
import random
import socket
import SocketServer
import threading
import time

from .bucketset import BucketSet
from .hashing import hash_function, random_id
from .peer import Peer
from .shortlist import Shortlist


import logging
logger = logging.getLogger(__name__)
# network spec
k = 20
alpha = 3
id_bits = 160
iteration_sleep = 0.1 # more aggressive iteration

class DHTRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        try:
            message = json.loads(self.request[0].strip())
            logger.debug(message)
            message_type = message["message_type"]
            if message_type == "ping":
                self.handle_ping(message)
            elif message_type == "pong":
                self.handle_pong(message)
            elif message_type == "find_node":
                self.handle_find(message)
            elif message_type == "find_value":
                self.handle_find(message, find_value=True)
            elif message_type == "found_nodes":
                self.handle_found_nodes(message)
            elif message_type == "found_value":
                self.handle_found_value(message)
            elif message_type == "store":
                self.handle_store(message)
            elif message_type == "register":
                self.handle_register(message)
        except KeyError, ValueError:
            pass
        client_host, client_port = self.client_address
        peer_id = message["peer_id"]
        new_peer = Peer(client_host, client_port, peer_id)
        self.server.dht.buckets.insert(new_peer)

    def handle_register(self,message):
        logger.info('register :'+json.dumps(message))
        id = message['value']['origin']
        key = message['value']['data']
        self.server.dht[str(id)] = key
        self.server.dht.keyspool.append((id,key))

    def handle_ping(self, message):
        client_host, client_port = self.client_address
        id = message["peer_id"]
        peer = Peer(client_host, client_port, id)
        peer.pong(socket=self.server.socket, peer_id=self.server.dht.peer.id, lock=self.server.send_lock)
        
    def handle_pong(self, message):
        logger.info('pong'+str(message))
        pass
        
    def handle_find(self, message, find_value=False):
        key = message["id"]
        id = message["peer_id"]
        client_host, client_port = self.client_address
        peer = Peer(client_host, client_port, id)
        response_socket = self.request[1]
        if find_value and (key in self.server.dht.data):
            value = self.server.dht.data[key]
            peer.found_value(id, value, message["rpc_id"], socket=response_socket, peer_id=self.server.dht.peer.id, lock=self.server.send_lock)
        else:
            nearest_nodes = self.server.dht.buckets.nearest_nodes(id)
            if not nearest_nodes:
                nearest_nodes.append(self.server.dht.peer)
            nearest_nodes = [nearest_peer.astriple() for nearest_peer in nearest_nodes]
            peer.found_nodes(id, nearest_nodes, message["rpc_id"], socket=response_socket, peer_id=self.server.dht.peer.id, lock=self.server.send_lock)

    def handle_found_nodes(self, message):
        rpc_id = message["rpc_id"]
        shortlist = self.server.dht.rpc_ids[rpc_id]
        del self.server.dht.rpc_ids[rpc_id]
        nearest_nodes = [Peer(*peer) for peer in message["nearest_nodes"]]
        shortlist.update(nearest_nodes)
        
    def handle_found_value(self, message):
        rpc_id = message["rpc_id"]
        shortlist = self.server.dht.rpc_ids[rpc_id]
        del self.server.dht.rpc_ids[rpc_id]
        shortlist.set_complete(message["value"])
        
    def handle_store(self, message):
        key = message["id"]
        logger.error('storing '+str(key))
        verified_doc = self.server.dht.reg.verify_doc(message['value'])
        if verified_doc:
            self.server.dht.data[key] = verified_doc 
            self.server.dht.reg.doc_store.insert_doc(str(key),verified_doc)
        else:
            raise ValueError


class DHTServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    def __init__(self, host_address, handler_cls):
        logger.info('create server')
        SocketServer.UDPServer.__init__(self, host_address, handler_cls)
        self.send_lock = threading.Lock()

class DHT(object):
    def __init__(self, host, port,registry,id=None, boot_host=None, boot_port=None):
        logger.info('create dht object')
        if not id:
            id = random_id()
        self.reg = registry
        #object swizzle , add DHT into registry
        registry.dht = self

        self.peer = Peer(unicode(host), port, id)
        self.id = id
        self.data = {}
        self.keyref = {}
        self.keyspool = []
        self.buckets = BucketSet(k, id_bits, self.peer.id)
        self.rpc_ids = {} # should probably have a lock for this
        try:
           logger.info('starting server on '+str(host)+':'+str(port))
           self.server = DHTServer(self.peer.address(), DHTRequestHandler)
        except:
           logger.critical('starting server on '+str(host)+':'+str(port))
           logger.critical('alternative port : '+str(port+1))
           self.peer = Peer(unicode(host), port+1, hash_function('magic_local'))
           self.server = DHTServer(self.peer.address(), DHTRequestHandler)
        self.server.dht = self
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.bootstrap(unicode(boot_host), boot_port)
        self.register(unicode(boot_host), boot_port)
    
    def iterative_find_nodes(self, key, boot_peer=None):
        shortlist = Shortlist(k, key)
        shortlist.update(self.buckets.nearest_nodes(key, limit=alpha))
        if boot_peer:
            rpc_id = random.getrandbits(id_bits)
            self.rpc_ids[rpc_id] = shortlist
            boot_peer.find_node(key, rpc_id, socket=self.server.socket, peer_id=self.peer.id)
        while (not shortlist.complete()) or boot_peer:
            nearest_nodes = shortlist.get_next_iteration(alpha)
            for peer in nearest_nodes:
                shortlist.mark(peer)
                rpc_id = random.getrandbits(id_bits)
                self.rpc_ids[rpc_id] = shortlist
                peer.find_node(key, rpc_id, socket=self.server.socket, peer_id=self.peer.id) ######
            time.sleep(iteration_sleep)
            boot_peer = None
        return shortlist.results()
        
    def iterative_find_value(self, key):
        shortlist = Shortlist(k, key)
        shortlist.update(self.buckets.nearest_nodes(key, limit=alpha))
        while not shortlist.complete():
            nearest_nodes = shortlist.get_next_iteration(alpha)
            for peer in nearest_nodes:
                shortlist.mark(peer)
                rpc_id = random.getrandbits(id_bits)
                self.rpc_ids[rpc_id] = shortlist
                peer.find_value(key, rpc_id, socket=self.server.socket, peer_id=self.peer.id) #####
            time.sleep(iteration_sleep)
        return shortlist.completion_result()
            
    def register(self, reg_host, reg_port):
        if reg_host and reg_port:
            logger.debug('registering to host %s %s',reg_host,str(reg_port))
            register_peer = Peer(reg_host, reg_port, 0)
            doc = self.reg.gen_doc(self.reg.node_id,self.reg.pub.as_pem())
            register_peer.register(self.reg.node_id,doc,socket=self.server.socket,peer_id=self.peer.id)

    def bootstrap(self, boot_host, boot_port):
        if boot_host and boot_port:
            logger.debug('bootstrapping host %s %s',boot_host,str(boot_port))
            boot_peer = Peer(boot_host, boot_port, 0)
            self.iterative_find_nodes(self.peer.id, boot_peer=boot_peer)

    def get(self, key):
        hashed_key = hash_function(key)
        doc = self.reg.doc_store.get_doc(hashed_key)
        if doc:
            return self.reg.verify_doc(doc)
        result = self.iterative_find_value(hashed_key)
        verified_doc = self.reg.verify_doc(result)
        if verified_doc:
            self.reg.doc_store.insert_doc(hashed_key,verified_doc)
            self.data[hashed_key] = verified_doc
            return verified_doc
        raise KeyError

    def __getitem__(self,key):
        return self.get(key)['data']
        
    def post_item(self,hashed_key,value):
        " raw post , with out encoding "
        nearest_nodes = self.iterative_find_nodes(hashed_key)
        generated_doc = value
        if not nearest_nodes:
            self.reg.doc_store.insert_doc(hashed_key,generated_doc)
        for node in nearest_nodes:
            node.store(hashed_key, generated_doc, socket=self.server.socket, peer_id=self.peer.id)

    def __setitem__(self, key, value):
        hashed_key = hash_function(key)
        nearest_nodes = self.iterative_find_nodes(hashed_key)
        generated_doc = self.reg.gen_doc(key,value)
        self.reg.doc_store.insert_doc(hashed_key,generated_doc)
        if not nearest_nodes:
            self.reg.doc_store.insert_doc(hashed_key,generated_doc)
        for node in nearest_nodes:
            node.store(hashed_key, generated_doc, socket=self.server.socket, peer_id=self.peer.id)
        
    def tick():
        pass
