import datetime
import glob
import requests
import re
import wget
from subprocess import call
import errno
import os
import io
from util import RateLimited, debug


DATA_SET_URL = 'https://scans.io/series/alexa-dl-top1mil'
DATA_BASE_URL = 'https://scans.io/zsearch/'
COMPRESSION_EXT = '.lz4'
HASH_FILE = 'known_hashes.txt'

def getKnownHashes():
	with open(HASH_FILE, 'r+') as f:
		return [l.split(',')[0] for l in f.readlines()]

def recordHash(h, name):
	with open(HASH_FILE, 'a+') as f:
		f.write('{},{}\n'.format(h, name))

def getARecords():
	now = datetime.datetime.now()
	s = now.strftime('%Y%m%d')
	all_days = 'alexa-top1m-a-zgrab.*?.csv'
	#Cache for debug
	matches = sorted(glob.glob('*-alexa-top1m-a-zgrab.csv'), reverse=True)
	file_re = '({}.*?-{}{})'.format(DATA_BASE_URL, all_days, COMPRESSION_EXT)
	hash_re = '.*?<code>(.*?)</code>'
	resource_re = re.compile('{}{}'.format(file_re, hash_re), re.DOTALL)
	response = requests.get(DATA_SET_URL).content
	m = resource_re.search(response)
	if m and m.groups()[1] not in getKnownHashes():
		debug('Fetching: {}'.format(m.groups()[0]))
		file_name = wget.download(m.groups()[0])
		call(['unlz4', file_name])
		new_name = '{}-alexa-top1m-a-zgrab.csv'.format(s)
		call(['mv',  file_name.rstrip(COMPRESSION_EXT), new_name])
		recordHash(m.groups()[1], m.groups()[0])
		return new_name
	return matches[0]

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

getIps(1)