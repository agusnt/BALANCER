#!/usr/bin/python3

"""
Function to read and measure characteristics using hardware counters

Arguments:
    $1 : cpu where run the application
    $2 : file with the configuration, see example.json and respect hex values

@Author: Navarro Torres, Agustin (agusnt@unizar.es)
@Date: 21/04/2020
"""

import sys
import os
import json
import msr
import threading
import PQOS
from time import time, sleep
from pprint import pprint
from sys import exit
from numpy import mean

bwMeasurements = []
end = False

def bw(cpu):
    global idx
    global end

    PQOS.bw(True, 1, cpu)

    old = PQOS.bwRead(cpu) / 1024 / 1024
    while not end:
        t2 = time()
        sleep(5)
        value = PQOS.bwRead(cpu) / 1024 / 1024
        t1 = time()
        if (value >= old):
            val = (value - old) / (t1 - t2)
            bwMeasurements.append(val)
            old = value
        else:
            old = 0

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Arguments: [cpu] [mask] [json file]")

    # Load configuration options
    cpu = int(sys.argv[1])
    config = json.load(open(sys.argv[3]))
    mask = int(sys.argv[2], 16)

    # Apply mask
    PQOS.l3Allocation(True, 1, 1, mask, cpu)

    # Prepare the command to run
    cmd = "taskset -c {} {}".format(cpu, config['cmd'])

    bw = threading.Thread(target = bw, args=(cpu,))
    bw.start()

    # Read and configure HW counters
    for i in config['hwCounters']:
        addr = int(config['hwCounters'][i]['addr'], 16)
        value = int(config['hwCounters'][i]['value'], 16)
        # Write 0 the return msr
        msr.writeMSR(0, addr + 1, 0)
        # Configure and enable de register
        msr.writeMSR(0, addr, value)
    
    # Execute the command
    t1 = time()
    os.system(cmd)
    t2 = time()
    end = True

    PQOS.l3Allocation(False, 1, 1, 0xFFFF, cpu)

    # Read the HW Counters
    for i in config['hwCounters']:
        addr = int(config['hwCounters'][i]['addr'], 16)
        print("{}: {}".format(i, msr.readMSR(0, addr + 1)))
        # Disable HW Counter
        msr.writeMSR(0, addr, 0)
    print("Time (s): {}".format(t2 - t1))
    print("BW (MB/s): {}".format(mean(bwMeasurements)))
