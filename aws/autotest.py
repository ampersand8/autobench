#!/usr/bin/env python3

import os
import subprocess
import time
import json

configuration = {}

def executeTest(cluster, url, payload, rate, connections, duration, id, max_retries):
        failures = 0
        for tries in range(int(max_retries)):
                process = subprocess.run(['./autobench', '-cluster', cluster, '-url', url, '-payload', payload, '-rate', rate, '-connections', connections, '-duration', duration, '-out', '{}_{}_{}_{}_{}_{}.txt'.format(id, cluster, payload, rate, connections, duration)])
                if process.returncode != 0:
                        tries += 1
                        print("{}: {} failed {} / {}".format(id, cluster, str(tries), str(max_retries)))
                        failures += 1
                        time.sleep(int(configuration['waitBetweenTests']))
                else:
                        break

        with open("test_failures.txt", "a") as myfile:
                myfile.write("{}_{}_{}_{}_{}: {}\n".format(id, cluster, payload, rate, connections, str(failures)))

def runTest(rate, connections, payload, duration, id, clusters, max_retries = "3"):
        for cluster in clusters:
                print("Testing {} with {} bytes payload, {} rate and {} connections for {} on {}"
                .format(id, payload, rate, connections, duration, cluster))
                executeTest(cluster, next((c['url'] for c in configuration['clusters'] if c['name'] == cluster), None), payload, rate, connections, duration, id, max_retries)
                time.sleep(30)

def main():
        os.chdir(os.path.expanduser("~") + "/test")
        global configuration
        with open('config.json') as json_data:
                config = json.load(json_data)
                configuration = config['configuration']
                print("Following Tests will be executed:")
                for t in config['tests']:
                        print("ID: {}, Clusters: [{}], Rate: {} msg/s, Payload: {} bytes, Connections: {}, Duration: {}, Max Retries: {}"
                        .format(t['id'], ', '.join(t['clusters']), t['rate'], t['payload'], t['connections'], t['duration'], t['max_retries']))
                print('\n')
                for t in config['tests']:
                        runTest(t['rate'], t['connections'], t['payload'], t['duration'], t['id'], t['clusters'])

if __name__== "__main__":
        main()
