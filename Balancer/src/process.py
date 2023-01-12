#!/usr/bin/python3
"""
Function to control process flow in an easy way

Requirements:
    - psutil library

@AUTHOR: Navarro Torres, Agustín
@EMAIL: agusnt (at) unizar (dot) es
@DATE: 23/06/2020
@UPDATES:
"""
import HWCounters
import subprocess
import psutil
import PQOS
import sys
import os
from time import time, sleep
from threading import Lock
from pprint import pprint
from math import gcd

class Process:
    """
    This class manages every aspect related with process that are launched. 
    Also it works as a watchdog to monitor if any core has no job or is shared 
    among multiple jobs.

    One lock is used to ensure mutual exclusion and that no interferences arise
    between the watchdogs and the other process.

    """
    ###########################################################################
    # Class attribute
    ###########################################################################
    _th = None
    _cmd = None
    _hwc = None
    _end = False
    _pqos = None
    _watchdog = None
    _gMPKI3 = None
    _mMPKI3 = None
    _dicPid = None
    _l3Iter = None
    _l3Occupancy = None
    _endCores = None
    _mutex = None
    _limits = None

    ###########################################################################
    # Not override functions
    ###########################################################################
    def __init__(self, cmd, config):
        self._cmd = cmd
        self._th = config['threads']
        self._hwc = HWCounters.HWCounters(config['hwCounters'])
        self._pqos = PQOS.PQOS()
        self._gMPKI3 = {}
        self._mMPKI3 = {}
        self._dicPid = {}
        self._l3Iter = {}
        self._l3Occupancy = {}
        self._endCores = []
        self._mutex = Lock()
        self._lastL3 = {}
        self._lastL3Iter = {}
        self._limits = {}

        # Initialize structures to measure global MPKI3
        for i in self._th:
            self._hwc.start(i)
            self._endCores.append(False)
            self._gMPKI3[i] = {}
            self._mMPKI3[i] = {}
            self._l3Occupancy[i] = 0
            self._l3Iter[i] = 1
            self._lastL3[i] = 0
            self._lastL3Iter[i] = 1
            self._pqos.reset(i)
            self._limits[i] = {'None': 0, 'LLC': 0, 'BW': 0, 'LLCBW': 0, 
                    'Total': 0}
            for j in self._th:
                self._gMPKI3[i][j] = 0
                self._mMPKI3[i][j] = 0

    ###########################################################################
    # Private functions
    ###########################################################################
    def _watchdogProcess(self, minFreq=1900):
        """
        Monitors the process and CPU frequency to detect failures in the 
        execution
        
        Parameters : 
            - minFreq : minimal cpu frequenc, below this value a failure is 
                    detected.
        """
        freq = psutil.cpu_freq(percpu=True)
        with (self._mutex):
            # Test that they are not two or more process running in the same 
            # logical thread
            for i in self._dicPid:
                try:
                    # Get the PID of the process
                    p = psutil.Process(i).children(recursive = True)[-1]
                    # Get the CPU utilization of the process
                    cpu = p.cpu_percent(interval=.001) 
                    # Get the affinity of the core
                    affinity = p.cpu_affinity() 

                    if cpu > 10 and cpu < 70:
                        # We set that a thread is sharing its logical thread if is
                        # using less than 70% of CPU. This script is developed to
                        # launch CPU-intensive workloads.
                        sys.stderr.write("({:.2f}) [Watchdog Process] {} -- {}\n"\
                                .format(time(), affinity, cpu))
                        sys.stderr.flush()
                        pass

                except:
                    # A process can be in the dictionary but die before get its
                    # information. If that happen an exception will be raise.
                    pass

            # We get the frequency of all cores and compare it with the base
            # frequency of the process. If an signification amount of logical
            # threads have a low freq (three o more time consecutively) we can
            # assume that something happens and the script is not launched 
            # process to that core.
            #
            # Q: One warning means that there is a problem?
            # A: No, because we can measure the frequency in a bad moment like 
            # when a process die and we does not launch a new one.
            for i in self._th:
                if freq[i][0] < minFreq:
                    sys.stderr.write("({:.2f}) [Watchdog Freq] {} -- {} MHz\n"\
                            .format(time(), i, freq[i][0]))
                sys.stderr.flush()

    def _watchdogCPU(self):
        """
        This code test that all CPU are running only a process. This function can 
        give false-true and not critical notification. Only if a CPU gives
        multiple error in a short-term time (example 3 notifications in 5
        seconds) you should assume that the schedule is not working well.
        """
        with (self._mutex):
            utility = psutil.cpu_percent(interval=.05, percpu=True)
            for i in self._th:
                # Iterate over all the logical cores and test if each one of them is
                # loaded. In the wort case it's take less than 1 second to detect
                # a dead logical core. Because of cpu_percent function we don't have
                # to do an sleep, this function already block and sleep

                if (utility[i] < 50):
                    # One logical thread is no used
                    #sys.stderr.write("({:.2f}) [Watchdog CPU] {}\n"\
                    #        .format(time(), i))
                    #sys.stderr.flush()

                    for pid in self._dicPid:
                        cpu, _, _ = self._dicPid[pid]
                        if cpu == i:
                            return True, pid
                    else:
                        return False, i
            return None

    def _updateL3Monitor(self, tsleep=0.0005, tsleep_middle=.2):
        """
        Read L3 Occupancy of all cores.

        Because the AMD Rome only allows to measure the LLC occupancy of one 
        CCX core at time, we must to multiplex the hw counter.

        Parameters : 
            - tsleep: seconds to wait before change the hardware counter from one 
                    CCX Core to another.
            - tsleep_middle: seconds to sleep between llc updates. The hardware
                    counters return the actual occupancy value. S
        """

        sys.stderr.write("Init updater L3\n")
        sys.stderr.flush()
        while not self._end:
            sleep(tsleep_middle)
            with (self._mutex):
                for idx in range(0, 4):
                    for jdx in range(0, len(self._th), 4):
                        # Get the thread to monitor each CCX
                        thread = self._th[idx + jdx]
                        # Enable L3 Counter on the CCX
                        self._pqos.l3Occupancy(True, thread)

                    # Sleep before readint the value
                    sleep(tsleep)

                    for jdx in range(0, len(self._th), 4):
                        thread = self._th[idx + jdx]

                        # Read the actual L3 occupancy
                        value = 0
                        retry = 0
                        while value == 0 and retry < 10:
                            value = (self._pqos.l3OccupancyRead(thread))
                            retry += 1

                        # Calculate the mean using Welford's Method in order to 
                        # avoid using big data structures in memory

                        # L3 Occupancy of the instances' live
                        self._l3Occupancy[thread] = self._l3Occupancy[thread] \
                                + ((value - self._l3Occupancy[thread]) \
                                / self._l3Iter[thread])

                        # L3 occupancy that can be reset by the user
                        self._lastL3[thread] = self._lastL3[thread] \
                                + ((value - self._lastL3[thread]) \
                                / self._lastL3Iter[thread])

                        # Increase number of iteration used
                        self._lastL3Iter[thread] += 1
                        self._l3Iter[thread] += 1

        sys.stderr.write("Finish Update L3\n")
        sys.stderr.flush()

    def _readHWC(self, core, l3g=False):
        """
        Read all hw counters and return their value in a dictionary. This
        function doesn't acquire/release mutex, so you must be careful when use
        it.

        Parameters :
            - core : core where the application is executed
            - l3g : calculate global L3 Misses
        """
        dicHWCRes = self._hwc.readValues(core)
        # L3 global miss
        accMPKI3 = 0

        if l3g:
            for i in self._th:
                dicHWC = self._hwc.readValues(i)
                value = dicHWC['L3Miss']

                if i != core:
                    # MPKI3 from another core
                    accMPKI3 += value - self._mMPKI3[core][i]
                    accMPKI3 += self._gMPKI3[core][i]
                    # Save read value from the other core
                    self._mMPKI3[core][i] = value
                    self._gMPKI3[core][i] = 0
                else:
                    for j in self._th:
                        if j != core:
                            self._gMPKI3[j][core] += value - self._mMPKI3[j][core]
                            self._mMPKI3[j][core] = 0
                    accMPKI3 += value

            dicHWCRes['L3Miss Global'] = accMPKI3
        dicHWCRes['L3Occupancy (KB)'] = self._l3Occupancy[core] / 1024 

        return dicHWCRes

    ###########################################################################
    # API functions
    ###########################################################################
    def isEnd(self):
        """
        Return end attribute
        """
        return self._end

    def startWatchdog(self, timeCPU=20, timeProcess=5000):
        """
        Function to manage watchdog in one function with sleeps

        Parameters : 
            - timeCPU : time to wait between enter the watchdog CPU
            - timeProcess : time to wait between watchdog Process
        """
        # Calculate sleeping time
        div = gcd(timeCPU, timeProcess)

        sys.stderr.write("Start Watchdog\n")
        sys.stderr.flush()

        t = (0, 0)
        while not self._end:
            # Sleep for X seconds
            sleep(div / 1000)
            if ((t[0] * div) == timeCPU):
                # Launch CPU watchdog
                value = self._watchdogCPU()
                if value:
                    # A CPU is not running a process
                    val, pid = value
                    if val:
                        # Print end information of the death instance
                        core = self.printInfo(pid)
                        if core >= 0:
                            # Launch a new process in the given core
                            self.launch(core)
                    else:
                        self.launch(pid) # pid == core (special case)
                t = (0, t[1])
            if ((t[1] * div)) == timeProcess:
                # Launch Process Watchdog
                pid = self._watchdogProcess()
                t = (t[0], 0)
            t = (t[0] + 1, t[1] + 1)
        sys.stderr.write("Finish Watchdog\n")
        sys.stderr.flush()

    def launch(self, cpu, init=False):
        """
        Launch the giving command to the CPU.
    
        Parameters:
            - cpu : core where the command will be executed
            - init : bool, True if is the first time that a core is going to
                    receive a job.
    
        Return : pid of the new process
    
        Exception : raise an exception if the core is unavailable to run a process.
        """
        with (self._mutex):
            # Get the mutex
            t = .01

            if not init:
                # This launch is because an instance already finish
                t = .2
                # Indicate that this core already complete at least one job
                self._endCores[cpu] = True

                if all(self._endCores):
                    # All CPU complete at least one job, so we can finish the
                    # program because the experiment is already done.
                    self._end = True
                    return -1

            if (psutil.cpu_percent(interval=t, percpu=True)[cpu] > 50):
                # The core is already running a instance (the load during more
                # than 0.2 seconds is above 50%). So we don not have to launch
                # another job in the cpu.
                return -2
            else:
                # Get the complete command line to launch the program
                # TODO: remove the taskset command for a psutil function that
                # change the core affinity of the process
                arg = " ".join(["taskset", "-c", str(cpu), "bash", "-c", "\""] +\
                        self._cmd[cpu].split(' ') + ["\""])
 
                # Launch process
                proc = subprocess.Popen(arg, stdout = subprocess.DEVNULL, \
                    stderr = subprocess.DEVNULL, preexec_fn = os.setsid, \
                    shell=True)

                # Reset hardware counters
                self._hwc.reset(cpu)
                self._l3Occupancy[cpu] = 0
                self._l3Iter[cpu] = 1
                self._lastL3[cpu] = 0
                self._lastL3Iter[cpu] = 1
                self._limits[cpu] = {'None': 0, 'LLC': 0, 'BW': 0, 'LLCBW': 0, 
                    'Total': 0}

                # Save the information about the processes
                self._dicPid[proc.pid] = (cpu, self._cmd[cpu], time())

            return 0

    def readHWC(self, core, l3g=False):
        """
        Read all hw counters and return their value in a dictionary

        Parameters :
            - core : core where the application is executed
            - l3g : return also the global L3 misses
        """
        with(self._mutex):
            return self._readHWC(core, l3g=l3g)

    def readAllHWC(self, cores, l3g=False):
        """
        Read all hw counters and return their value in a dictionary

        Parameters :
            - core : core where the application is executed
            - l3g : return also the global L3 misses
        """
        aux = {}
        with(self._mutex):
            for core in cores:
                aux[core] = self._readHWC(core, l3g=l3g)
        return aux

    def getL3Monitor(self, cores):
        """
        Get L3 Monitor since last read

        Parameters :
            - core : core where the application is executed
        """
        values = {}
        with(self._mutex):
            for i in cores:
                # Return the value on KiB to easy human read
                values[i] = self._lastL3[i] / 1024
                self._lastL3[i] = 0
                self._lastL3Iter[i] = 1
        return values

    def pqos(self):
        """
        Return the PQOS object
        """
        return self._pqos

    def printInfo(self, pid):
        """
        Print information about an execution

        Parameters :
            - pid : pid of the process to measure
        """
        with(self._mutex):
            core = -1

            # Get info about the execution
            if (pid in self._dicPid): 
                core, cmd, tini = (self._dicPid[pid])

                # Print the info about the finish thread
                print("TH: {}".format(core))
                print(cmd)
                print("Time Init: {}".format(tini))
                print("Time End: {}".format(time()))
                print("Time (s): {}".format(time() - tini))

                # Read hardware counters and print its information
                dicHWC = self._readHWC(core, l3g=True)
                for i in dicHWC:
                    print("{}: {}".format(i, dicHWC[i]))
                
                print("LLC: {} BW: {} LLCBW: {} Total: {}".format(
                    self._limits[core]['LLC'], self._limits[core]['BW'], 
                    self._limits[core]['LLCBW'], self._limits[core]['Total']))

                # Remove this pid from the dictionary
                del self._dicPid[pid]
            return core

    def update_restrictions(self, dic):
        """
        Update the number of epochs with restriction
        """
        for i in dic:
            lllc, lbw = dic[i]
            if lllc and not lbw:
                self._limits[i]['LLC'] += 1
            elif not lllc and lbw:
                self._limits[i]['BW'] += 1
            elif lllc and lbw:
                self._limits[i]['LLCBW'] += 1
            self._limits[i]['Total'] += 1
