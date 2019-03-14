#!/usr/bin/env python3
# Transforms a list of values to a HdrHistogram
import argparse
import re
import glob
import pprint
from hdrh.histogram import HdrHistogram
import decimal
import matplotlib
import matplotlib.pyplot as plt

parser = argparse.ArgumentParser(description='Process environment test files')
parser.add_argument('--testruns', nargs='+', help='Input test run', dest='testruns', required=True)
args = parser.parse_args()
testruns = [str(testrun) for testrun in args.testruns]

def getFilenames(directory, payload):
	return glob.glob(directory + '/env_ping_*' + payload + '.txt')

def getLatencyFromPing(ping):
	latency = re.split('=| ', ping)
	return float(latency[9])

def getLatenciesFromFile(filename):
	latencies = []
	with open(filename, 'r') as f:
		pings = f.read().splitlines()
		for ping in pings[1:-4]:
			latencies.append(getLatencyFromPing(ping))
	return latencies

def writeHistogram(outfilename, latencies):
	histogram = HdrHistogram(1, 60 * 60 * 1000, 2)
	for latency in latencies:
		histogram.record_value(float(latency) * 1000)
	with open(outfilename, 'wb') as f:
		histogram.output_percentile_distribution(f, 1000)
	with open(outfilename, 'r+') as f:
		d = f.readlines()
		f.seek(0)
		for i in d:
			if not i.startswith('#'):
				f.write(i)
		f.truncate()
	
def writeListToFile(outfilename, inlist):
	inlist = [str(value) for value in inlist]
	with open(outfilename, 'w') as f:
		f.write('\n'.join(inlist))

def getFilesystemSpeedFromFile(filename):
	values = []
	with open(filename, 'r') as f:
		value, unit = f.readlines()[2].split(', ')[3].rstrip().split(' ')
		if unit == 'GB/s':
			value = decimal.Decimal(value) * 1000
		values.append(decimal.Decimal(value))
	return values

def getIperfSpeedFromFile(filename):
	with open(filename, 'r') as f:
		return f.readlines()[6].split()[6]

def makePingHistograms():
	payloads = ['256', '1024', '5120']
	systems = ['kafka', 'nats']
	latenciesPerPayload = {payloads[0]: [], payloads[1]: [], payloads[2]: []}
	for testrun in testruns:
		latenciesPerTestrun = {payloads[0]: [], payloads[1]: [], payloads[2]: []}
		for system in systems:
			indirectory = system + '_tests/aws' + testrun + '/env'
			for payload in payloads:
				filename = getFilenames(indirectory, payload)[0]
				latenciesPerTestrun[payload].extend(getLatenciesFromFile(filename))
		for payload in payloads:
			latenciesPerPayload[payload].extend(latenciesPerTestrun[payload])
			writeHistogram('pings/ping_' + payload + '/'+testrun+'.hgrm', latenciesPerTestrun[payload])

	for payload in payloads:
		writeHistogram('pings/ping_'+payload+'.hgrm', latenciesPerPayload[payload])

def mergeFSSpeeds():
	testcases = ['T01', 'T02', 'T03', 'T04']
	for operation in ['read', 'write']:
		readSpeedPerTestcase = {testcases[0]: [], testcases[1]: [], testcases[2]: [], testcases[3]: []}
		for testrun in testruns:
			indirectory = 'kafka_tests/aws'+testrun+'/env'
			for testcase in testcases:
				filename = indirectory + '/env_'+testcase+'_'+operation+'.txt'
				readSpeedPerTestcase[testcase].extend(getFilesystemSpeedFromFile(filename))

		fig, ax = plt.subplots()

		for testcase in testcases:
			ax.plot(testruns, readSpeedPerTestcase[testcase], label=testcase)

		ax.set(xlabel='Testlauf', ylabel='Geschwindigkeit MB/s',
			title='Filesystem ' + operation + ' speed')
		ax.grid()
		ax.set_ylim(bottom=0.0)
		plt.legend(loc='upper left')
		fig.set_size_inches(11, 6)
		fig.savefig('fs_'+operation+'_speeds.png', dpi=200)

def mergeIperfResults():
    filenames = []
    for testrun in testruns:
        filenames.extend(glob.glob('kafka_tests/aws'+testrun+'/env/env_iperf_*.txt'))
    
    results = []
    for filename in filenames:
        results.append(int(getIperfSpeedFromFile(filename)))
	
    fig, ax = plt.subplots()
    print(results)
    ax.plot(testruns, results)

    ax.set(xlabel='Testlauf', ylabel='Geschwindigkeit MB/s',
		title='Netzwerkdurchsatz')
    ax.grid()
    ax.set_ylim(bottom=0, top=800)
    fig.set_size_inches(11, 6)
    fig.savefig('netzwerkdurchsatz.png', dpi=200)

makePingHistograms()
mergeFSSpeeds()
mergeIperfResults()