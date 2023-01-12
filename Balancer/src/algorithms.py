#!/usr/bin/python3
"""
Class for the algorithm execution

@AUTHOR: Navarro Torres, Agustín
@EMAIL: agusnt (at) unizar (dot) es
@DATE: 13/12/2020
@UPDATES:
"""

# Local imports
import HWCounters
import rollingAVG
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

class Algorithm:
    """
    Class to manage the functions and elements of the algorithm
    """
    _prc = None
    _alg = None
    _interCall = None
    _parameterCall = None
    _cores_with_limit= []
    _limit_core = {} # None = 0, LLC = 1, BW = 2
    _mask = {}
    _limit_bw = {}
    CCX_SIZE = 4

    def __init__(self, alg, parameters):
        self._alg = alg
        self._parameterCall = {}
        self._parameterCall['core'] = parameters['core']
        self._prc = parameters['prc']

        for i in range(0, max(parameters['core']), 4):
            # Initialize data structure
            self._cores_with_limit.append(0)

        if (alg == "llc") or (alg == "llcbw") or (alg == "bw"):
            self._parameterCall['limit'] = parameters['limit']
            self._parameterCall['rolling'] = parameters['rolling']
            self._parameterCall['hpmo_max'] = parameters['hpmo_max']
            self._parameterCall['bw_limit'] = parameters['bw_limit']
            self._parameterCall['lat_limit'] = parameters['lat_limit']
            self._parameterCall['hpmo_limit'] = parameters['hpmo_limit']
            # Data that must be keep between functions call
            self._interCall = {}
            self._interCall['hwc'] = {}
            self._interCall['cmask'] = {}
            for core in self._parameterCall['core']:
                # Rolling average functions
                self._interCall['hwc'][core] = {
                        'hpmo': rollingAVG.RollingAVG(\
                            self._parameterCall['rolling']),
                        'acy': rollingAVG.RollingAVG(\
                                self._parameterCall['rolling']),
                        'lat': rollingAVG.RollingAVG(\
                                self._parameterCall['rolling']),
                        'bw': rollingAVG.RollingAVG(\
                                self._parameterCall['rolling'])
                    }
                self._interCall['cmask'][core] = (0xFFFF, 2048, (core % self.CCX_SIZE) +1)
                self._limit_core[core] = (False, False)
        elif alg == "static":
            mask = [(0xF000, 13, 1), (0x0F00, 13, 2), (0x00F0, 13, 3), (0x000F,
                13, 4)]
            for core in range(0, len(self._parameterCall['core'])):
                mask_llc, mask_bw, cos = mask[core % self.CCX_SIZE]
                self._prc.pqos().l3Allocation(True, cos, mask_llc, core)
                self._prc.pqos().bwAllocation(True, cos, mask_bw, core)
        elif alg == "ucp":
            with open(parameters['allocation']) as f:
                raw = f.read().split('\n')
                mov = 0
                for i in raw[:-1]:
                    core = int(i.split(' ')[0])
                    ways = int(i.split(' ')[1])

                    if core % self.CCX_SIZE == 0:
                        mov = 0

                    cos = (core % self.CCX_SIZE) + 1
                    # Add 1 to the mask
                    mask = 0
                    for i in range(0, ways):
                        mask += (1 << i)
                    # Add 0 to the mask
                    for i in range(0, mov):
                        mask = mask << 1
                    mov += ways

                    # Apply mask
                    self._prc.pqos().l3Allocation(True, cos, mask, core)

        if (alg == "llcbw"):
            self._parameterCall['lat_limit'] = parameters['lat_limit']
            self._parameterCall['bw_limit'] = parameters['bw_limit']

    def _rollingAVG_update(self, hwcg):
        '''
        Update and calculate rolling average
    
        Parameters : 
            - hwcg: hardware counters data    
    
        Return: rolling average data and access data
        '''
        cores = self._parameterCall['core']
        hwc = self._interCall['hwc']
        access = {}
        ravg = {}

        # Get hardware counters measures
        for core in hwcg:

            # Get average acess
            if hwc[core]['acy'].nElements() == hwc[core]['acy'].max():
                access[core] = hwc[core]['acy'].avg()
            else:
                access[core] = None 

            for key in hwc[core]:
                # If the value is none, we reset it
                value = 0 if hwcg[core][key] == None else hwcg[core][key]
    
                if value != 0:
                    # Add element the rolling average
                    hwc[core][key].add(value)
                else:
                    # Reset rolling average
                    hwc[core][key] = rollingAVG.RollingAVG(\
                            self._parameterCall['rolling'])
    
                # Set rolling average structure
                if key not in ravg:
                    ravg[key] = {}
                # Remove older data
                if hwc[core][key].nElements() == hwc[core][key].max():
                    # Calculate rolling average
                    ravg[key][core] = hwc[core][key].avg()
                else:
                    ravg[key][core] = None
    
        return ravg, access

    def _getCCX(self, ccx=4):
        """
        Return one ccx ever time is called
    
        Parameters :
            - cores : list of the cores
            - ccx : ccx size 
        """
        for i in range(0, len(self._parameterCall['core']), ccx):
            yield i, [i + j for j in range(0, ccx)]

    def _getCCD(self, ccd=8):
        """
        Return one ccd ever time is called
    
        Parameters :
            - cores : list of the cores
            - ccd : ccd size 
        """
        for i in range(0, len(self._parameterCall['core']), ccd):
            yield i, [i + j for j in range(0, ccd)]

    def _phase_change(self, new, old, core, bw=False):
        """
        Detect phase changes

        Parameters:
            - new : latest hardware counter data
            - old : older hardware counter data
            - core : monitored cores
            - bw : algorithm is using bw?

        Return: true if a phase change is identified, otherwise false
        """
        # Detect phase changes
        if (old is None or new is None) or \
                ((new / self._parameterCall['limit']) > old) \
                or \
                ((new * self._parameterCall['limit']) < old):

            cos = (core % 4) + 1
            llc_mask = 0xFFFF
            bw_mask = 2048
    
            # Rollback last modification
            self._prc.pqos().l3Allocation(True, cos, llc_mask, core)
            self._prc.pqos().bwAllocation(True, cos, bw_mask, core)
            self._interCall['cmask'][core] = (llc_mask, bw_mask, cos)

            self._limit_core[core] = (False, False)
            if self._cores_with_limit[int(core / self.CCX_SIZE)] > 0:
                self._cores_with_limit[int(core / self.CCX_SIZE)] -= 1

            # Remove limit bw
            self._limit_bw[core] = 2.5
            return True
        return False

    def _restrict_llc(self, core, hpmo, bw=False):
        """
        Limit LLC

        Parameters:
            - core: core to restrict
            - hpmo: core hmpo value
            - bw : algorithm is using bw?

        Return: true if the llc is limited
        """
        limited = False

        # Get actual mask of the process
        llc_mask, bw_mask, cos = self._interCall['cmask'][core]

        if hpmo < self._parameterCall['hpmo_limit']:
            if self._cores_with_limit[int(core / self.CCX_SIZE)] == 3:
                return

            # Decrease cache
            if llc_mask == 0xFFFF:
                llc_mask = 0x1
                self._prc.pqos().l3Allocation(True, cos, llc_mask, core)
                self._prc.pqos().bwAllocation(True, cos, bw_mask, core)
                self._cores_with_limit[int(core / self.CCX_SIZE)] += 1
                limited = True

                # Measure times that the core is limited
                _, lbw = self._limit_core[core]
                self._limit_core[core] = (True, lbw)
        elif (hpmo >= self._parameterCall['hpmo_max']):
            if llc_mask == 0x1:
                llc_mask = 0xFFFF
                self._prc.pqos().l3Allocation(True, cos, llc_mask, core)
                self._prc.pqos().bwAllocation(True, cos, bw_mask, core)
                self._cores_with_limit[int(core / self.CCX_SIZE)] -= 1

                # Measure times that the core is limited
                _, lbw = self._limit_core[core]
                self._limit_core[core] = (False, lbw)

        self._interCall['cmask'][core] = (llc_mask, bw_mask, cos)
        return limited

    def _restrict_bw(self, core, lat, read_bw):
        """
        Limit BW


        Parameters:
            - core: core to restrict
            - lat: CCX latency value
            - read_bw : read bw used by the core

        Return: true if the bw is limited
        """
        mask_llc, mask_bw, cos = self._interCall['cmask'][core]

        if lat == None or read_bw == None:
            # Not enough data to apply the mechanism
            return

        if lat > self._parameterCall['lat_limit']:
            # Get new limit
            if core not in self._limit_bw:
                self._limit_bw[core] = self._parameterCall['bw_limit']
            elif self._limit_bw[core] >= (1.5 * 1.1):
                self._limit_bw[core] = self._limit_bw[core] * 0.9
            else:
                self._limit_bw[core] = 1.5
            mask_bw = int(self._limit_bw[core] / (1 / 8))
            # Only limit if there is no LLC limitation 
            self._prc.pqos().l3Allocation(True, cos, mask_llc, core)
            self._prc.pqos().bwAllocation(True, cos, mask_bw, core)

            # Measure times that the core is limited
            lllc, _ = self._limit_core[core]
            self._limit_core[core] = (lllc, True)
            self._interCall['cmask'][core] = (mask_llc, mask_bw, cos)
        return True
    
    def _balancer(self, data, bw=False, llc=True):
        """
        Algorithm that manage only llc

        Parameters:
            - data : data get from the hardware counters
            - bw : this algorithm manage bw?
            - llc : this algorithm manage llc?
        """
        phase = {}
        ravg, access = self._rollingAVG_update(data)
        for _, cores in self._getCCD():
            limit = False
            for core in cores:
                phase[core] = False
                # Iterate over all core of this CCX
                if access[core] != None:
                    phase[core] = self._phase_change(data[core]['acy'], \
                            access[core], core, bw=bw)
                
                if llc:
                    if ravg['hpmo'][core] != None and not phase[core]:
                        # Restrict LLC core
                        limit = self._restrict_llc(core, ravg['hpmo'][core], \
                                bw=bw)

            if bw:
                # Restrict BW also
                core = cores[0]
                maxx = 0
                for i in cores:
                    if ravg['bw'][i] != None and ravg['bw'][i] > maxx:
                        maxx = ravg['bw'][i]
                        core = i

                if not limit and not phase[core]:
                    # Restrict LLC core
                    self._restrict_bw(core, ravg['lat'][core], ravg['bw'][core])
        return phase

    def step(self, data):
        """
        Execute the selected algorithm

        Parameters:
            - data: data used for the algorithm
        """
        phase = {}
        if self._alg == "llc":
            phase = self._balancer(data)
        elif self._alg == "llcbw":
            phase = self._balancer(data, bw=True)
        elif self._alg == "bw":
            phase = self._balancer(data, bw=True, llc=False)

        self._prc.update_restrictions(self._limit_core)

        # Get data to analyze behavior
        lphase = "Phase:"
        limit_core = "LimitCore:"
        limit_bw = "LimitBW:"
        for i in range(0, 64):
            if i in phase:
                if phase[i]:
                    lphase = "{} {},True".format(lphase, i)
                else:
                    lphase = "{} {},False".format(lphase, i)

            if i in self._limit_core:
                lllc, lbw = self._limit_core[i]
                if lllc and not lbw:
                    limit_core = "{} {},LLC".format(limit_core, i)
                elif not lllc and lbw:
                    limit_core = "{} {},BW".format(limit_core, i)
                elif lllc and lbw:
                    limit_core = "{} {},LLCBW".format(limit_core, i)
                else:
                    limit_core = "{} {},None".format(limit_core, i)

            if i in self._limit_bw:
                limit_bw = "{} {},{}".format(limit_bw, i, self._limit_bw[i])

        sys.stderr.write("{}\n{}\n{}\n".format(lphase, limit_core, limit_bw))
        sys.stderr.flush()
