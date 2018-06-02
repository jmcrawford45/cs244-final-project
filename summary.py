from __future__ import division
import json
import glob
from collections import defaultdict
import numpy as np
from pylab import *
from util import getARecords, getSiteRankings, extractStek
from plotter import *
from datetime import datetime, timedelta
from dateutil.parser import parse

SECONDS_PER_DAY = 60*60*24

class StekHost(object):

	def __init__(self, host):
		self.host = host
		self.steks = defaultdict(list)
		self.lifetimes = list()

	def getMaxLifetime(self):
		if lifetimes:
			return max(self.lifetimes)
		return timedelta(seconds=0)

	def computeLifetimes(self):
		for stek, times in self.steks.items():
			maxTime = max(times)
			minTime = min(times)
			self.lifetimes.append(maxTime-minTime)

	def addStek(self, stek, ts):
		self.steks[stek].append(ts)

class StekHostDict(defaultdict):
	def __missing__(self, key):
		res = self[key] = StekHost(key)
		return res


class SummaryBuilder(object):

	STEK_DB = 'all-steks.json'

	ERRORS = [
		'i/o timeout',
		'handshake failure',
		'connection refused',
		'EOF',
		'Other'
	]
	FIGURE_3_CATEGORIES = [
		'No ticket',
		'days <= 1',
		'1 < days <= 3',
		'3 < days <= 7',
		'7 < days <= 10',
		'days > 10',
	]

	FIGURE_3_BAR_NAMES = [
		'Alexa 100',
		'Alexa 1K',
		'Alexa 10K',
		'Alexa 100K',
		'Alexa 1M'
	]



	def __init__(self):
		self.stats = defaultdict(int)
		self.churn = defaultdict(int)
		self.success = set()
		self.steks = StekHostDict()
		self.rankings = getSiteRankings()
		self.maxLifetimes = defaultdict(lambda: timedelta(seconds=0))

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
		plotChurn(self.dailyChurn)

	def computeLifetimes(self):
		for host in self.steks.values():
			host.computeLifetimes()
		

	def getKnownHashes():
		with open(self.STEK_DB, 'a+') as f:
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
			stek = entry['data']['tls']['session_ticket']['value']
			ts = parse(entry['timestamp'])
			self.steks[entry['ip']].addStek(stek, ts)
			stats['session_ticket'] += 1
		if 'session_id' in entry['data']['tls']['server_hello']:
			if entry['data']['tls']['server_hello']['session_id'] != "":
				stats['session_id'] += 1

	def exportStek(self):
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
		measurements = [
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
		print measurements

	def plotFigure1(self):
		pass

	def plotFigure2(self):
		pass

	def plotFigure3(self):
		dayLifetimes = [td.total_seconds()/SECONDS_PER_DAY for td in self.maxLifetimes.values()]
		plotSTEKCDF(dayLifetimes)

	def plotFigure4(self):
		pass

	def run(self):
		self.getChurn()
		self.exportStek()
		for host in self.steks().values():
			host.computeLifetimes()
			self.maxLifetimes[host.host] = host.getMaxLifetime()
		self.plotFigure1()
		self.plotFigure2()
		self.plotFigure3()
		self.plotFigure4()
		self.printSummary()

SummaryBuilder().run()