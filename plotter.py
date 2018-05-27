from pylab import *


# Plot the percentage of sites leaving the top 1M list from the previous day
# Tested with self.plotChurn([0,0.02,.05, .0392, .05, .042, .054, .063])
def plotChurn(data):
	plot(range(len(data)), data)
	ylabel('Sites leaving Alexa Top 1M List')
	xlabel('Days')
	title('Alexa Top 1M Daily Churn')
	axes().yaxis.set_major_formatter(FuncFormatter(lambda y, _: '{:.0%}'.format(y)))
	savefig('churn.png')