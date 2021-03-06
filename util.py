import time
import struct
import datetime
import glob
import re
import requests
import wget
from subprocess import call
from collections import defaultdict
import numpy as np
import json
DEBUG = True

DATA_SET_URL = 'https://scans.io/series/alexa-dl-top1mil'
DATA_BASE_URL = 'https://scans.io/zsearch/'
COMPRESSION_EXT = '.lz4'
HASH_FILE = 'known_hashes.txt'
INT_SIZE = 4
# Default - RFC 5077
KEY_LEN = 16


# Extract the session key identifier if possible from the ticket
def extractStek(ticket):
    nssId = 'NSS!'
    if nssId in ticket:
        start = ticket.index(nssId) + len(nssId)
        try:
            return list(ticket[start: start + KEY_LEN])
        except Exception, e:
            return list(ticket)
    candidates = list(ticket)
    try:
        prefix_len = KEY_LEN
        candidates.append(
            struct.unpack('{}s'.format(KEY_LEN), ticket[:prefix_len])[0]
        )
    except Exception, e:
        debug(e)
    # LibreSSL - ssl_session_st
    try:
        prefix_len = KEY_LEN + 2 * INT_SIZE 
        candidates.append(
            struct.unpack('ii{}s'.format(KEY_LEN), ticket[:prefix_len])[2]
        )
    except Exception, e:
        debug(e)
    #OpenSSL - ssl_session_st
    try:
        prefix_len = 2 * INT_SIZE + 64 + KEY_LEN
        # Todo: Confirm second size_t is 32 bits
        candidates.append(
            struct.unpack('ii64s{}s'.format(KEY_LEN), ticket[:prefix_len])[3]
        )
    except Exception, e:
        debug(e)
    #GNUTLS - session_ticket.{hc}
    try:
        prefix_len = INT_SIZE + KEY_LEN
        # Todo: Confirm first ssize_t is 32 bits
        candidates.append(
            struct.unpack('i{}s'.format(KEY_LEN), ticket[:prefix_len])[1]
        )
    except Exception, e:
        debug(e)
    #mbedTLS - ssl_ticket.c
    try:
        candidates.append(
            struct.unpack('4s', ticket[:4])[0]
        )
    except Exception, e:
        debug(e)
    return candidates

def getKnownHashes():
    with open(HASH_FILE, 'a+') as f:
        f.seek(0)
        return [l.split(',')[0] for l in f.readlines()]

def recordHash(h, name):
    with open(HASH_FILE, 'a') as f:
        f.write('{},{}\n'.format(h, name))

def getScansIOFile(all_days, local_name):
    now = datetime.datetime.now()
    s = now.strftime('%Y%m%d')
    match_re =  local_name.format('*')
    #Cache for debug
    matches = sorted(glob.glob(match_re), reverse=True)
    file_re = '({}[^><]*?-{}{})'.format(DATA_BASE_URL, all_days, COMPRESSION_EXT)
    hash_re = '.*?<code>(.*?)</code>'
    resource_re = re.compile('{}{}'.format(file_re, hash_re), re.DOTALL)
    response = requests.get(DATA_SET_URL).content
    m = resource_re.search(response)
    if m and m.groups()[1] not in getKnownHashes():
        debug('Fetching: {}'.format(m.groups()[0]))
        file_name = wget.download(m.groups()[0])
        new_name = local_name.format(s)
        call(['/usr/local/bin/unlz4', file_name, new_name])
        recordHash(m.groups()[1], m.groups()[0])
        return new_name
    return matches[0]


def getARecords():
    return getScansIOFile('alexa-top1m-a-zgrab.*?.csv', '{}-alexa-top1m-a-zgrab.csv')

# Return a map from IP to rank
def getSiteRankings():
    rank_file = getScansIOFile('alexa-top1m-www-alookups.*?.json', '{}-alexa-top1m-www-alookups.json')
    res = defaultdict(lambda: 1000000)
    with open(rank_file) as ranks:
        for raw in ranks:
            entry = json.loads(raw)
            if 'alexa_rank' in entry:
                rank = entry['alexa_rank']
                if 'altered_name' in entry:
                    res[entry['altered_name']] = rank
                if 'name' in entry:
                    res[entry['name']] = rank
                if 'data' in entry and 'ipv4_addresses' in entry['data']:
                    for addr in entry['data']['ipv4_addresses']:
                        res[addr] = rank
    return res 

    

def debug(s):
	if DEBUG:
		print s

def normalize(v):
    norm=np.linalg.norm(v, ord=1)
    if norm==0:
        return v
    return v/norm

def RateLimited(maxPerSecond):
    minInterval = 1.0 / float(maxPerSecond)
    def decorate(func):
        lastTimeCalled = [0.0]
        def rateLimitedFunction(*args,**kargs):
            elapsed = time.clock() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait>0:
                time.sleep(leftToWait)
            ret = func(*args,**kargs)
            lastTimeCalled[0] = time.clock()
            return ret
        return rateLimitedFunction
    return decorate