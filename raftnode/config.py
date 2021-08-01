from random import randrange
from os import getenv

LEADER = 0
CANDIDATE = 1
FOLLOWER = 2
LOW_TIMEOUT = getenv('LOW_TIMEOUT', 100)
HIGH_TIMEOUT = getenv('HIGH_TIMEOUT', 1500)

REQUESTS_TIMEOUT = 50
HB_TIME = getenv('HB_TIME', 50)
MAX_LOG_WAIT = getenv('MAX_LOG_WAIT', 1500)

def random_timeout():
    '''
    return random timeout number
    '''
    return randrange(LOW_TIMEOUT, HIGH_TIMEOUT) / 1000

def chunks(l, n):
    n = max(1, n)
    return (l[i:i+n] for i in range(0, len(l), n))