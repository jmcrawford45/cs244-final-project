import json
import glob
from collections import defaultdict
import numpy as np
from pylab import *

stats = defaultdict(int)
churn = defaultdict(int)

def exportStek():
	for f in sorted(glob.glob('*-stek.json'), reverse=True):
		with open(f) as data:
			for raw in data:
				entry = json.loads(raw)
				stats['total'] += 1
				churn[entry['ip']] += 1
				if 'error' in entry and 'i/o timeout' in entry['error']:
					stats['timeout'] += 1
				elif 'error' in entry:
					stats['other error'] += 1
				elif 'session_ticket' in entry['data']['tls']:
					print entry['ip'], entry['data']['tls']['session_ticket']
					stats['session_ticket'] += 1
				elif 'session_id' in entry['data']['tls']['server_hello']:
					if entry['data']['tls']['server_hello']['session_id'] != "":
						stats['session_id'] += 1
	print stats

def extractData():
	consistentTop1M = [k for k,v in churn.items() if v == max(churn.values())]
	for f in sorted(glob.glob('*-stek.json'), reverse=True):
		with open(f) as data:
			for raw in data:
				entry = json.loads(raw)
				if entry['ip'] in consistentTop1M:
					#do somethings

# Create some test data
dx = .01
X  = np.arange(-2,2,dx)
Y  = exp(-X**2)

# Normalize the data to a proper PDF
Y /= (dx*Y).sum()

# Compute the CDF
CY = np.cumsum(Y*dx)

# Plot both
plot(X,Y)
plot(X,CY,'r--')

exportStek()