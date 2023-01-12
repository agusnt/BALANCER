#!/usr/bin/python3
"""
Auxiliary functions used by multiples files.

@AUTHOR: Navarro Torres, Agustín
@EMAIL: agusnt (at) unizar (dot) es
@DATE: 13/12/2020
@UPDATES:
"""

# Local imports
import HWCounters
import rollingAVG
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

def getComplexEvent(prc, cores, ttime, old):
    """
    Calculate the complex events.

    Parameter: 
        - prc : process object of the process class
        - cores : list with the cores
        - ttime : time where the old hardware counters was measured
        - old : hardware counters to calculate the new complex event

    Return : a dictionary with the complex hardware events by core
    """
    dic = {}
    lr = prc.getL3Monitor(cores)
    for core in cores:
        oc = 0
        hwcg = prc.readHWC(core)
        t = time() - ttime
        if hwcg['Instr Retired'] > old[core]['Instr Retired']:
            ins = hwcg['Instr Retired'] - old[core]['Instr Retired']
            cyc = hwcg['Cycles'] - old[core]['Cycles']
            l3m = hwcg['L3Miss'] - old[core]['L3Miss']
            l3d = hwcg['L3MissDC'] - old[core]['L3MissDC']
            lt1 = hwcg['L3Latency1'] - old[core]['L3Latency1']
            lt2 = hwcg['L3Latency2'] - old[core]['L3Latency2']
            lpf = hwcg['L3HitPF'] - old[core]['L3HitPF']
            lp2 = hwcg['L3HitPFL2'] - old[core]['L3HitPFL2']
            l3h = hwcg['L3HitDC'] - old[core]['L3HitDC']
            och = hwcg['L3Occupancy (KB)']

            # Measure oc, in case of 0 return 1
            oc = lr[core]
            oc = 1 if oc == 0 else oc

            # Complex event
            hpm = ((lpf + lp2 + l3h) / (l3m))
            hpmo = hpm / (oc / 1024)
            mpki3 = (l3m / (ins / 1000))

            dic[core] = {
                    'cpi': cyc / ins, 
                    'bwl': ((l3m * 64) / (1024 * 1024 * 1024)) / t,
                    'lat': (lt1 * 16) / lt2,
                    'dmpki3': (l3d) / (ins / 1000),
                    'hpm': hpm,
                    'hr': (lpf + lp2 + l3h) / (l3m + lpf + lp2 + l3h),
                    'mr': l3m / (l3m + lpf + lp2 + l3h),
                    'oc': oc / 1024,
                    'hpmo': hpmo,
                    'mro': (l3m / (l3m + lpf + lp2 + l3h)) / oc,
                    #'acy': (lpf + lp2 + l3h + l3m) / cyc,
                    'acy': (lpf + lp2 + l3h + l3m) / ins,
                    'access': (lpf + lp2 + l3h + l3m),
                    'hit': (lpf + lp2 + l3h),
                    'och': och / 1024,
                    'hpmom': hpmo * mpki3,
                    'bw': ((l3m * 64) / (1024 * 1024 * 1024)) / t
                    }
        else:
            dic[core] = {'cpi': None, 'bwl': None, 'lat': None, 'dmpki3': None,
                    'hr': None, 'acy': None, 'oc': None, 'hpmo': None,
                    'hpm': None, 'och': None, 'bw': None}
    return dic

def getHWC(prc, cores):
    """
    Read the hardware counters from the cores

    Parameters:
        - cores : list with the cores

    Return: hardware counters
    """
    return prc.readAllHWC(cores)

def doEpoch(prc, cores, tepoch):
    """
    Do an epoch and measure the events in that time

    Parameters:
        - prc : process object of the process class
        - cores : list with the cores
        - tepoch : epoch time

    Return: hardware counter data in the epoch
    """
    aux = getHWC(prc, cores)
    t = time()
    sleep(tepoch)
    return getComplexEvent(prc, cores, t, aux)
