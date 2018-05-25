import datetime
import glob
import requests
import re
import wget
from subprocess import call
import errno
import os
import io
import time


DEBUG = False
DATA_SET_URL = 'https://scans.io/series/alexa-dl-top1mil'
DATA_BASE_URL = 'https://scans.io/zsearch/'
COMPRESSION_EXT = '.lz4'

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

def debug(s):
	if DEBUG:
		print s

def getARecords():
	all_days = 'alexa-top1m-a-zgrab.*.csv'
	#Cache for debug
	matches = sorted(glob.glob('*-alexa-top1m-a-zgrab.csv'), reverse=True)
	if matches:
		return matches[0]


	resource_re = re.compile('(' + DATA_BASE_URL + '.*-' + all_days + COMPRESSION_EXT + ')')
	response = requests.get(DATA_SET_URL).content
	m = resource_re.search(response)
	if m:
		debug('Fetching: {}'.format(m.groups()[0]))
		file_name = wget.download(m.groups()[0])
		call(['unlz4', file_name])
		new_name = '{}-alexa-top1m-a-zgrab.csv'.format(s)
		call(['mv',  file_name.rstrip(COMPRESSION_EXT), new_name])
		return new_name

@RateLimited(100)
def printIp(ip):
	print ip

# Returns the Alexa Top n hosts (Max 1000000)
def getIps(n):
	entries = None
	a_records_file = getARecords()
	debug('Using IPs from file: {}'.format(a_records_file))
	with io.open(a_records_file, encoding='utf-8') as f:
		entries = f.readlines()
	debug(len(entries))
	for i in range(0,min(len(entries), n)):
		row = entries[i].split(',')
		if len(row) >= 2:
			printIp(row[0])

getIps(100)