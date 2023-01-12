#!/usr/bin/python3
"""
Main function to launch process, measure and perform policies

@AUTHOR: Navarro Torres, Agustín
@EMAIL: agusnt (at) unizar (dot) es
@DATE: 23/06/2020
@UPDATES:
    13/06/2020 -> 
"""

# Local imports
import HWCounters
import rollingAVG
import algorithms
import utilities
import process

# General imports
import threading
import signal
import json
import sys
import os
import numpy as np
from pprint import pprint
from time import time, sleep
from random import choice as choice
from random import randrange as rnd

def readCMD(fname):
    """
    Read a file with the commands to execute (and the core where each command
    should be executed) and transform it to a dictionary.

    Parameters:
        - fname : name of the file with the commands

    Return : dictionary with the information
    """
    cmd = {}
    with open(fname) as f:
        raw = f.read().split('\n')

        for i in raw[:-1]:
            core = int(i.split(' ')[0])
            comm = ' '.join(i.split(' ')[1:])
            cmd[core] = comm

    return cmd


    cpi = hwc['']

def log(f, prc, cores, hwcg, ttime, llc):
    """
    Print log information about the execution

    Parameters : 
        - f : file object to write the log
        - prc : process object of the process class
        - cores : list with the cores
        - ttime : time where the old hardware counters was measured
        - old : hardware counters to calculate the new complex event
        - bw : cores which bw was constrained

    Return: hardware counters data
    """
    bwg = 0

    f.write("{}\n".format(time()))
    for i in cores:
        if hwcg[i]['bwl'] is not None:
            #cpig.append(hwcg[i]['cpi'])
            bwg += hwcg[i]['bwl']
            str_ = "Core: {} CPI: {:.2f}".format(i, hwcg[i]['cpi'])
            str_ += " HpMO: {:.2f}".format(hwcg[i]['hpmo'])
            str_ += " DMPKI3: {:.2f}".format(hwcg[i]['dmpki3'])
            str_ += " BW Local (GB/s): {:.1f}".format(hwcg[i]['bwl'])
            str_ += " Lat L3: {:.0f}\n".format(hwcg[i]['lat'] )
        else:
            str_ = ""
        f.write(str_)
    f.write("BW Global (GB/s): {:.0f}\n".format(bwg))
    f.write("Constrain LLC: {}\n".format(' '.join([str(i) for i in llc])))
    f.write("------\n")

    return hwcg, bwg

def alg(flog, prc, config):
    """
    Run the management algorithm every tepoch

    Parameters :
        - prc: process object
        - config : configuration file
    """
    # Create function to call the algorithm
    parameters = {}
    parameters['core'] = config['threads']
    if 'limit' in config:
        parameters['limit'] = config['limit']
    if 'rolling' in config:
        parameters['rolling'] = config['rolling']
    if 'hpmo_max' in config:
        parameters['hpmo_max'] = config['hpmo_max']
    if 'bw_limit' in config:
        parameters['bw_limit'] = config['bw_limit']
    if 'lat_limit' in config:
        parameters['lat_limit'] = config['lat_limit']
    if 'hpmo_limit' in config:
        parameters['hpmo_limit'] = config['hpmo_limit']
    if 'allocation' in config:
        parameters['allocation'] = config['allocation']
    parameters['prc'] = prc
    # Create algorithm class
    alg = algorithms.Algorithm(config['alg'], parameters)
    hwc = utilities.getHWC(prc, config['threads'])

    while not prc.isEnd():
        # Do epoch
        data = utilities.doEpoch(prc, config['threads'], config['tepoch'])
        alg.step(data)

def loop(config, runCore):
    """
    Main loop of the LLC schedule

    Parameters :
        - config : configuration file
        - runCore : core where the pseudo-scheduler is running
    """
    # Read Configuration file. The configuration file has the following format:
    # {
    #   'threads': [List with the threads where run applications], 
    #   'hwCounters' : {}
    #   'cmd': 'command file with the applications to run',
    #   'alg': 'management algorithm to use,
    #   'tepoch': 'time epoch',
    # }
    cmd = readCMD(config['cmd'])
    tepoch = config['tepoch']
    flog = config['file_log']
    hwcg = {}

    # Start class
    prc = process.Process(cmd, config)

    # Allocate 0 ways to the management core to avoid pollute another running
    # process
    prc.pqos().l3Allocation(True, 5, 0x0, runCore)

    for core in config['threads']:
        # Configure and launch the processes
        prc.pqos().reset(core)
        prc.launch(core, init=True)
        hwcg[core] = prc.readHWC(core)

    # Start watchdogs
    watchdog = threading.Thread(target=prc.startWatchdog)
    watchdog.start()
    # Start watchdog l3 monitor
    watchdog_l3 = threading.Thread(target=prc._updateL3Monitor)
    watchdog_l3.start()
    # Start management algorithm
    algTh = threading.Thread(target=alg, args=(open(flog, 'w+'), prc, config,))
    algTh.start()

    while not prc.isEnd():
        # Wait until the process end and launch the next process
        (pid, _) = os.wait()

        core = prc.printInfo(pid)
        if core != -1:
            prc.launch(core) 

    sys.stderr.write("End main program\n")
    sys.stderr.flush()

    for core in config['threads']:
        # Reset constrain of cores
        prc.pqos().reset(core)

    # Remove constrain of schedule core
    prc.pqos().l3Allocation(False, 1, 0x0, runCore)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        # Arguments to launch the scheduler
        sys.stderr.write("main.py [config file] [schedule core]") 
        exit()

    # Load configuration options
    config = json.load(open(sys.argv[1]))
    runCore = int(sys.argv[2])

    # Run execution
    loop(config, runCore)
    
