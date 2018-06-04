from pylab import *
from datetime import timedelta
from collections import Counter

PLOT_BASE = 'writeup/figures/'
CDF_MARKS = 24.
# Plot the percentage of sites leaving the top 1M list from the previous day
# Tested with self.plotChurn([0,0.02,.05, .0392, .05, .042, .054, .063])
def plotChurn(data):
	cla()
	plot(range(len(data)), data)
	ylabel('Sites leaving Alexa Top 1M List')
	xlabel('Days')
	title('Alexa Top 1M Daily Churn')
	axes().yaxis.set_major_formatter(FuncFormatter(lambda y, _: '{:.0%}'.format(y)))
	savefig('{}churn.pdf'.format(PLOT_BASE))

def getBarBottom(layers, categories, i, bar_names):
	bar_begin = np.zeros(len(bar_names))
	for j in range(len(categories)):
		if j < i:
			bar_begin += layers[categories[j]] 
	return bar_begin

# Formatting of arguments documented in mockSTEKReuse
# Expects a collection of 1 normalized vectors of size
# len(bar_names) * len(categories)
def plotSTEKReuse(data, bar_names, categories):
	cla()
	if not data:
		return mockSTEKReuse()
	colors = [
		'r',
		'b',
		'g',
		'c',
		'y',
		'm',
	]
	bars = list()
	ind = np.arange(len(bar_names)) * 5
	layers = dict()
	for c in categories:
		layers[c] = np.array([bar[c] for bar in data])
	for i in range(len(categories)):
		bar_begin = getBarBottom(layers, categories, i, bar_names)
		bars.append(plt.bar(ind, layers[categories[i]], width=2, bottom=bar_begin, color=colors[i]))
	plt.xticks(ind, bar_names, rotation=-60)
	axes().yaxis.set_major_formatter(FuncFormatter(lambda y, _: '{:.0%}'.format(y)))
	legend(bars, categories,bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
	tight_layout()
	savefig('{}stek_stacked.pdf'.format(PLOT_BASE))


def  genBoundedNormalSample(mu, sigma, n, lo, hi):
	res = np.random.normal(mu, sigma, n)
	for i,datum in enumerate(res):
		if datum < lo:
			res[i] = lo
		if datum > hi:
			res[i] = hi
	return res

# Expects a list of floats where each element is a STEK lifetime in days
def plotSTEKCDF(data=None, num_bins=14*24):
	cla()
	if not data:
		data = genBoundedNormalSample(3,2,250000,0,14)
	# Create some test data
	counts, bin_edges = np.histogram (data, bins=num_bins, normed=True)
	cdf = np.cumsum (counts)
	p = plot(bin_edges[1:], cdf/cdf[-1], marker='D', markevery=int(num_bins/CDF_MARKS))

	ylabel('Consistent Alexa1M TLS Only')
	xlabel('Max STEK lifetime (in days)')
	legend(p, ['Alexa1M Hosts'], loc='lower right')
	grid(True)
	savefig('{}max_stek_cdf.pdf'.format(PLOT_BASE))

# Expects a list of floats where each element is a STEK lifetime in days
def plotMinutelyCDF(
		data=None, advertised=None, num_bins=14*24,
		is_stek=True):
	cla()
	file_name = '{}stek_minutely_cdf' if is_stek else '{}id_minutely_cdf'
	if not data:
		data = genBoundedNormalSample(200,150,250000,0,1440)
	if is_stek:
		advertised = genBoundedNormalSample(180,200,250000,0,1440)
	# Create some test data
	counts, bin_edges = np.histogram(data, bins=num_bins, normed=True)
	cdf = np.cumsum (counts)

	p0 = plot(bin_edges[1:], cdf/cdf[-1], marker='D', markevery=int(num_bins/CDF_MARKS))
	p1 = None
	if is_stek:
		counts, bin_edges = np.histogram(advertised, bins=num_bins, normed=True)
		cdf = np.cumsum (counts)
		p1 = plot(bin_edges[1:], cdf/cdf[-1], marker='o', markevery=int(num_bins/CDF_MARKS))
	ylabel('Consistent Alexa1M HTTPS Only')
	xlabel('Max successful resumption delay (in minutes)')
	if is_stek:
		legend(p1, ['Advertised lifetime hints'], loc='lower right')
	tight_layout()
	grid(True)
	savefig(file_name.format(PLOT_BASE))


# Return a 1 normalized n element sample with weight vector w
def normalizedSample(v, n, w):
	res = Counter(np.random.choice(v, n, w))
	for k,v in res.items():
		res[k] = v/float(n)
	return res

def mockSTEKReuse():
	weights = [
		[2,2,3,3,4,4],
		[2,2,3,3,4,5],
		[1,2,3,4,5,6],
		[1,2,5,5,5,6],
		[1,1,1,4,5,6],
	]
	categories = [
		'No ticket',
		'days <= 1',
		'1 < days <= 3',
		'3 < days <= 7',
		'7 < days <= 10',
		'days > 10',
	]
	bar_names = [
		'Alexa 100',
		'Alexa 1K',
		'Alexa 10K',
		'Alexa 100K',
		'Alexa 1M'
	]
	top100 = normalizedSample(categories, 100, weights[0])
	top1K = normalizedSample(categories, 1000, weights[1])
	top10K = normalizedSample(categories, 10000, weights[2])
	top100K = normalizedSample(categories, 100000, weights[3])
	top1M = normalizedSample(categories, 1000000, weights[4])

	plotSTEKReuse([
		top100,
		top1K,
		top10K,
		top100K,
		top1M
	], bar_names, categories)