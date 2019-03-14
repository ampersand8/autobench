#!/usr/bin/env python3
import argparse
import copy
import math
import pprint
import glob
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from cycler import cycler
import decimal

parser = argparse.ArgumentParser(description='Calculate the standard deviations for all hdrhistograms')
parser.add_argument('--testcase', help='<Required> Name', dest='testcase', required=True)
parser.add_argument('--out', nargs='?', help='Output directory', dest='outdir', default='', required=False)

args = parser.parse_args()
outdir = args.outdir
testcase = args.testcase

def getFilenames(directory):
	return glob.glob(directory + "/??.hgrm")

def loadHistograms(filenames):
    records = dict()
    for histogram_filename in filenames:
        rawrecords = [line.rstrip('\n') for line in open(histogram_filename, 'r')]
        myrecords = dict()
        for record in rawrecords[2:]:
            fields = record.split()
            myrecords[fields[1]] = float(fields[0])
        records[histogram_filename] = copy.deepcopy(myrecords)
    return records

def calcAverages(records):
    average = dict()
    for filename, myrecords in records.items():
        for percentile, value in myrecords.items():
            if percentile not in average:
                average[percentile] = 0.0
            average[percentile] += float(value)
    
    count = len(records)
    for percentile, value in average.items():
        average[percentile] = average[percentile] / count
    return average

def calcAllSquaredDeviations(records, average):
    deviations = dict()
    for filename, myrecords in records.items():
        tempdeviations = dict()
        for percentile, value in myrecords.items():
            tempdeviations[percentile] = abs(value-average[percentile]) ** 2
        deviations[filename] = copy.deepcopy(tempdeviations)
    return deviations

def getStandardDeviationsPerFile(ideviations):
    std_deviation = dict()
    for filename, deviations in ideviations.items():
        count = len(deviations)
        sum = 0
        for percentile, deviation in deviations.items():
            sum += deviation
        std_deviation[filename] = math.sqrt(sum / count)
    return std_deviation

def getStandardDeviationsPerPercentile(ideviations):
    sums = dict()
    count = len(ideviations.values())
    std_deviations = dict()
    for filename, deviations in ideviations.items():
        for percentile, deviation in deviations.items():
            if percentile not in sums:
                sums[percentile] = 0
            sums[percentile] += deviation
    
    for percentile, sum in sums.items():
        std_deviations[percentile] = math.sqrt(sum / count)

    return std_deviations

def writeCommaSeparatedList(filename, idict):
	with open(filename, 'w') as f:
		for key, value in idict.items():
			f.write(key + ', ' + str(value) + '\n')

fig, axs = plt.subplots()
ax = axs
ax.set_prop_cycle(cycler(color=['r','b', 'g']))

for system in ['256', '1024', '5120']:
	histogramdir = 'pings/ping_' + system
	filenames = getFilenames(histogramdir)
	records = loadHistograms(filenames)
	average = calcAverages(records)
	deviations = calcAllSquaredDeviations(records, average)
	standardDeviationsPerPercentile = getStandardDeviationsPerPercentile(deviations)
	percentiles = ['{0:f}'.format(decimal.Decimal(decimal.Decimal(value) * 100).normalize()) + '%' for value in list(average.keys())]
	latencies = list(average.values())
	ax.errorbar(percentiles, latencies, yerr=list(standardDeviationsPerPercentile.values()), label=system + ' bytes')

for label in ax.xaxis.get_ticklabels():
	label.set_visible(False)
	label.set_fontsize(16)

for label in ax.xaxis.get_ticklabels()[::8]:
    label.set_visible(True)

for label in ax.yaxis.get_ticklabels():
	label.set_fontsize(16)

for line in ax.xaxis.get_ticklines()[::16]:
	line.set_markersize(8)
	line.set_markeredgewidth(2)

for line in ax.xaxis.get_gridlines():
	line.set_linestyle(':')

for line in ax.xaxis.get_gridlines()[::8]:
	line.set_linestyle('-')

plt.xticks(rotation=15)
ax.xaxis.get_ticklines()[-2].set_markersize(8)
ax.xaxis.get_ticklines()[-2].set_markeredgewidth(2)
ax.xaxis.get_gridlines()[-1].set_linestyle('-')

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.xlabel('Perzentil', fontsize=22)
plt.ylabel('Latenz in ms', fontsize=22)
ax.set_ylim(0)
ax.set_xlim(xmin=0,xmax=len(ax.xaxis.get_gridlines()))
ax.set_title('Durchschnittliche Ping RTT pro Perzentil mit Standardabweichung', fontsize=20)
plt.grid(b=True, which='major')
plt.grid(b=True, which='minor')
plt.legend(loc='upper left', fontsize=16)
plt.margins(x=0,y=0)
plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.13)

fig = plt.gcf()
fig.set_size_inches(18.5, 10.5)
fig.savefig(testcase, dpi=200)