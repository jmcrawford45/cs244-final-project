from __future__ import division
import json
import glob
from collections import defaultdict
import numpy as np
from util import *
from datetime import datetime, timedelta
from dateutil.parser import parse
from base64 import b64decode

SECONDS_PER_DAY = 60*60*24
SECONDS_PER_MINUTE = 60
DATA_RE = 'all-steks.json'

class StekHost(object):

	def __init__(self, host):
		self.host = host
		self.steks = defaultdict(list)
		self.lifetimes = list()
		self.stekIssuer = False
		self.advertised = timedelta(seconds=0)

	def getMaxLifetime(self):
		if self.lifetimes:
			return max(self.lifetimes)
		return timedelta(seconds=0)

	def computeLifetimes(self):
		for stek, times in self.steks.items():
			maxTime = max(times)
			minTime = min(times)
			self.lifetimes.append(maxTime-minTime)

	def addStek(self, stek, ts):
		self.stekIssuer = True
		for st in extractStek(b64decode(stek)):
			for ek in st:
				self.steks[ek].append(ts)

	def getAdvertisedLifetime(self):
		if not self.advertisedLifetime:
			return timedelta(seconds=0)
		return self.advertisedLifetime

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
		self.lifetimeHints = defaultdict(lambda: timedelta(seconds=0))
		self.sessionIdSupport = defaultdict(lambda: False)
		self.sessionTicketSupport = defaultdict(lambda: False)
		self.stekResumeLifetimes = defaultdict()
		self.stekResumes = StekHostDict()
		self.sessionResumeLifetimes = defaultdict()
		self.sessionResumes = StekHostDict()
		self.entry_count = 0

	# Compute the daily churn and store how many days
	# each IP was in the top 1M in the churn dict.
	def getChurn(self):
		prevSeen = set()
		self.dailyChurn = list()
		for f in sorted(glob.glob(DATA_RE), reverse=True):
			seen = set()
			with open(f) as data:
				for raw in data:
					self.entry_count += 1
					if self.entry_count % 100000 == 0:
						print '{} entries processed'.format(self.entry_count)
					entry = json.loads(raw)
					seen.add(entry['ip'])
			self.dailyChurn.append(1-len(seen&prevSeen)/len(seen))
			prevSeen = seen
			for ip in seen:
				self.churn[ip] += 1
		self.consistentTop1M = [k for k,v in self.churn.items() if v == max(self.churn.values())]
		print 'churn'
		print self.dailyChurn
		# plotChurn(self.dailyChurn)

	def computeLifetimes(self):
		for host in self.steks.values():
			host.computeLifetimes()
		

	def writeSteks(self):
		with open(self.STEK_DB, 'a+') as f:
			for host in self.steks.values():
				f.write(json.dumps({
						'ip': host.host,
						'steks': host.steks,
						'advertised': host.advertised,
						'stekIssuer': host.stekIssuer 
					}))

	# Print the distribution of errors across known ERRORS
	def errorSummary(self):
		total_errors = sum(self.stats[e] for e in self.ERRORS)
		return ', '.join(['{} - {:.0%}'.format(e, self.stats[e]/total_errors) for e in self.ERRORS])	

	def handleError(self, entry):
		errorIdentified = False
		for e in self.ERRORS:
			if e in entry['error']:
				errorIdentified = True
				self.stats[e] += 1
		if not errorIdentified:
			self.stats[self.ERRORS[-1]] += 1

	def handleSuccess(self, entry):
		self.success.add(entry['ip'])
		if 'session_ticket' in entry['data']['tls']:
			stek = entry['data']['tls']['session_ticket']['value']
			ts = parse(entry['timestamp'])
			self.steks[entry['ip']].addStek(stek, ts)
			self.steks[entry['ip']].advertised = timedelta(seconds=int(entry['data']['tls']['session_ticket'].get('lifetime_hint', 0)))
			self.stats['session_ticket'] += 1
			self.sessionTicketSupport[entry['ip']] = True
		if 'session_id' in entry['data']['tls']['server_hello']:
			if entry['data']['tls']['server_hello']['session_id'] != "":
				self.stats['session_id'] += 1
				self.sessionIdSupport[entry['ip']] = True

	def exportStek(self):
		self.entry_count = 0
		for f in sorted(glob.glob(DATA_RE), reverse=True):
			with open(f) as data:
				for raw in data:
					self.entry_count += 1
					if self.entry_count % 100000 == 0:
						print '{} entries processed'.format(self.entry_count)
					entry = json.loads(raw)
					self.stats['tls_attempts'] += 1
					if entry['ip'] in self.consistentTop1M:
						if entry['ip'] not in self.steks:
							self.steks[entry['ip']] = StekHost(entry['ip'])
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
				).format(total_errors, self.errorSummary()),
			# Feature support
			('Of the {:,} hosts considered, {:.0%} supported session resumption via session IDs and {:.0%} supported session resumption via session tickets.'
				).format(dataset_total, len(self.sessionIdSupport)/dataset_total, len(self.sessionTicketSupport)/dataset_total)
		]
		print measurements

	def getFigure3BarIndex(self, rank):
		if rank <= 100:
			return 0
		elif rank <= 1000:
			return 1
		elif rank <= 10000:
			return 2
		elif rank <= 100000:
			return 3
		return 4

	def getFigure3CategoryIndex(self, stek_host):
		if not stek_host.stekIssuer:
			return 0
		else:
			maxLifetime = stek_host.getMaxLifetime()
			if maxLifetime <= timedelta(days=1):
				return 1
			elif maxLifetime <= timedelta(days=3):
				return 2
			if maxLifetime <= timedelta(days=7):
				return 3
			if maxLifetime <= timedelta(days=10):
				return 4
		return 5

	def classifyStekReuse(self):
		res = [[0 for col in range(len(self.FIGURE_3_CATEGORIES))] for row in range(len(self.FIGURE_3_BAR_NAMES))]
		for host, stek_host in self.steks.items():
			row = self.getFigure3BarIndex(self.rankings[host])
			col = self.getFigure3CategoryIndex(stek_host)
			res[row][col] += 1
		res = [normalize(np.array(l)) for l in res]
		return res

	def plotFigure1(self):
		minuteLifetimes = [td.total_seconds()/SECONDS_PER_MINUTE for td in self.sessionResumeLifetimes.values()]
		# if minuteLifetimes:
		# 	return plotMinutelyCDF(data=minuteLifetimes, is_stek=False)
		debug('No data found for figure 1')

	def plotFigure2(self):
		minuteLifetimes = [td.total_seconds()/SECONDS_PER_MINUTE for td in self.lifetimeHints.values()]
		print 'figure 2'
		print minuteLifetimes
		# if minuteLifetimes:
		# 	return plotMinutelyCDF(data=minuteLifetimes, is_stek=True)
		debug('No data found for figure 2')


	def plotFigure3(self):
		dayLifetimes = [td.total_seconds()/SECONDS_PER_DAY for td in self.lifetimeHints.values()]
		print 'figure 3'
		print dayLifetimes
		# plotSTEKCDF(dayLifetimes)

	def plotFigure4(self):
		print 'figure 4'
		print self.classifyStekReuse()
		# plotSTEKReuse(
		# 	self.classifyStekReuse(),
		# 	self.FIGURE_3_BAR_NAMES,
		# 	self.FIGURE_3_CATEGORIES
		# )

	def run(self):
		self.getChurn()
		self.exportStek()
		for host in self.consistentTop1M:
			host = self.steks[host]
			host.computeLifetimes()
			self.maxLifetimes[host.host] = host.getMaxLifetime()
			self.lifetimeHints[host.host] = host.advertised
		for host in self.stekResumes.values():
			host.computeLifetimes()
			self.stekResumeLifetimes[host.host] = host.getMaxLifetime()
		for host in self.sessionResumes.values():
			host.computeLifetimes()
			self.sessionResumeLifetimes[host.host] = host.getMaxLifetime()
		# self.writeSteks()
		# self.plotFigure1()
		self.plotFigure2()
		self.plotFigure3()
		self.plotFigure4()
		self.printSummary()

SummaryBuilder().run()