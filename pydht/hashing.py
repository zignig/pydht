import hashlib
import random

id_bits = 128
# TODO investigate other hash functions
def hash_function(data):
    return int(hashlib.sha1(data).hexdigest(), 16)
    
def random_id(seed=None):
    if seed:
        random.seed(seed)
    return random.randint(0, (2 ** id_bits)-1)
    
