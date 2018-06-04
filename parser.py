import datetime
import glob
import requests
import re
import wget
from subprocess import call
import errno
import os
import io
from util import RateLimited, debug, getARecords
import argparse

OUT_FILE = 'whitelist.txt'

# Outputs the Alexa Top n hosts (Max 1000000)
def getIps(n):
	entries = None
	a_records_file = getARecords()
	debug('Using IPs from file: {}'.format(a_records_file))
	with open(a_records_file) as f:
		entries = f.readlines()
	debug(len(entries))
	with open(OUT_FILE, 'w') as f:
		for i in range(0,min(len(entries), n)):
			row = entries[i].split(',')
			if len(row) >= 2:
				f.write(row[0]+'\n')


parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('N', type=int, default=1000000,
	help='How many top 1M sites to sample')
args = parser.parse_args()
getIps(args.N)