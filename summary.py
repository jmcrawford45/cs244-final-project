from __future__ import division
import json
import glob
from collections import defaultdict
import numpy as np
from pylab import *
from util import getARecords


class SummaryBuilder(object):

	STEK_DB = 'all-steks.json'

	ERRORS = [
		'i/o timeout',
		'handshake failure',
		'connection refused',
		'EOF',
		'Other'
	]

	def __init__(self):
		self.stats = defaultdict(int)
		self.churn = defaultdict(int)
		self.success = set()

	# Compute the daily churn and store how many days
	# each IP was in the top 1M in the churn dict.
	def getChurn(self):
		prevSeen = set()
		self.dailyChurn = list()
		for f in sorted(glob.glob('*-stek.json'), reverse=True):
			seen = set()
			with open(f) as data:
				for raw in data:
					entry = json.loads(raw)
					seen.add(entry['ip'])
			self.dailyChurn.append(1-len(seen&prevSeen)/len(seen))
			prevSeen = seen
			for ip in seen:
				self.churn[ip] += 1
		self.consistentTop1M = [k for k,v in self.churn.items() if v == max(self.churn.values())]
		print 'Daily churn'.format(self.dailyChurn)
		self.plotChurn(self.dailyChurn)

	# Plot the percentage of sites leaving the top !M list from the previous day
	# Tested with self.plotChurn([0,0.02,.05, .0392, .05, .042, .054, .063])
	def plotChurn(self, data):
		plot(range(len(data)), data)
		ylabel('Sites leaving Alexa Top 1M List')
		xlabel('Days')
		title('Alexa Top 1M Daily Churn')
		axes().yaxis.set_major_formatter(FuncFormatter(lambda y, _: '{:.0%}'.format(y)))
		savefig('churn.png')

	def mockSTEKReuse(self):
		
		pass

	def plotSTEKReuse(self, data):
		pass

	def getKnownHashes():
		with open(STEK_DB, 'a+') as f:
			f.write()

	# Print the distribution of errors across known ERRORS
	def errorSummary(self):
		total_errors = sum(stats[e] for e in self.ERRORS)
		return ', '.join(['{} - {:.0%}'.format(e, stats[e]/total_errors) for e in self.ERRORS])	

	def handleError(self, entry):
		errorIdentified = False
		for e in self.ERRORS:
			if e in entry['error']:
				errorIdentified = True
				stats[e] += 1
		if not errorIdentified:
			print 'Unidentified error: {}'.format(error['entry'])
			stats[self.ERRORS[-1]] += 1

	def handleSuccess(self, entry):
		self.success.add(entry['ip'])
		if 'session_ticket' in entry['data']['tls']:
			print entry['ip'], entry['data']['tls']['session_ticket']
			stats['session_ticket'] += 1
		if 'session_id' in entry['data']['tls']['server_hello']:
			if entry['data']['tls']['server_hello']['session_id'] != "":
				stats['session_id'] += 1

	def exportStek(self):
		self.plotSTEKReuse()
		for f in sorted(glob.glob('*-stek.json'), reverse=True):
			with open(f) as data:
				for raw in data:
					entry = json.loads(raw)
					self.stats['tls_attempts'] += 1
					if entry['ip'] in self.consistentTop1M:
						if 'error' in entry:
							self.handleError(entry)
						else:
							self.handleSuccess(entry)

	def printSummary(self):
		dataset_total = len(self.consistentTop1M)
		dataset_days = max(self.churn.values())
		consistentAndSuccess = len(self.success & set(self.consistentTop1M))
		total_errors = sum(self.stats[e] for e in self.ERRORS)
		MEASUREMENTS = [
			# Churn
			('In total, {:,} TLS handshakes were collected across {:,} distinct domains'
				).format(self.stats['tls_attempts'],len(self.churn)),
			# How many domains are considered
			('Only {:,} domains remained in the Top Million for the entire {:,} days.'
				).format(dataset_total, dataset_days),
			# TLS support
			('Of these, {:,} ({:.0%}) completed a TLS handshake with a browser-trusted certificate.'
				).format(consistentAndSuccess, consistentAndSuccess/dataset_total),
			# Common failures
			('The distribution of the {:,} failed connections is as follows: {}'
				).format(total_errors, errorSummary()),
		]
		print MEASUREMENTS

	def run(self):
		self.getChurn()
		self.exportStek()
		self.printSummary()

# Create some test data
dx = .01
X  = np.arange(-2,2,dx)
Y  = exp(-X**2)

# Normalize the data to a proper PDF
Y /= (dx*Y).sum()

# Compute the CDF
CY = np.cumsum(Y*dx)

# Plot both
# plot(X,Y)
# plot(X,CY,'r--')

SummaryBuilder().run()