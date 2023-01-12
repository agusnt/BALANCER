#!/usr/bin/python3

"""
Functions to manage in an easy way the hardware counters on an AMD Zen2 
processor. This class is ad-hoc develop to works with AMD Rome processor, 
it maybe works on another AMD processors but some changes will probably must 
be done.

NOTE: The word cpu in this file refers to cpu physical thread.

@AUTHOR: Navarro Torres, Agustín
@EMAIL: agusnt (at) unizar (dot) es
@DATE: 23/06/2020
@UPDATES:
"""
import msr

class HWCounters:
    """
    Class to configure HW counters.
    """
    ###########################################################################
    # Class attribute
    ###########################################################################
    _config = None # Configuration file

    ###########################################################################
    # Not override functions
    ###########################################################################
    def __init__(self, config):
        """
        Constructor of the class.
        
        Parameters:
            - config : dictionary with the configuration. The configuration has
              two values:
                * addr -> MSR address where the hardware counter will be 
                        configured
                * value -> value to write in the MSR that configure the 
                        hardware counter
        """
        self._config = config

    ###########################################################################
    # Private functions
    ###########################################################################
    def _getAddrAndValue(self, thread):
        """
        Generator.
        Every time that his generator is called return the MSR addr and value 
        to configure an L3 hardware counters
    
        Parameters:
            - thread : thread to configure hw counters
        """
        # Read and configure HW counters
        for i in self._config:
            if i == "L3Miss":
                # TODO: change the way to recognize L3 HW counters to be more
                # general
                # On AMD Rome the hardware counters associate to the L3 are
                # requires an extra configuration.
                thdx = thread % 4
                addr = int(self._config[i]['addr'], 16) + (thdx * 2)
                value = int(self._config[i]['value'], 16)
                value |= (1 << (56 + thdx * 2))
            else:
                addr = int(self._config[i]['addr'], 16)
                value = int(self._config[i]['value'], 16)
    
            yield addr, value, i

    ###########################################################################
    # API functions
    ###########################################################################
    def reset(self, cpu):
        """
        Reset all register dst hw counter. This Function doesn't disable hardware
        counters.
    
        Parameters:
            - cpu : core to reset the hardware counter value
        """
        for addr, _, _ in self._getAddrAndValue(cpu):
            msr.writeMSR(cpu, addr + 1, 0)
    
    def start(self, cpu):
        """
        Start all hardware counters 
    
        Parameters :
            - cpu : core to init the hardware counters
        """
        for addr, value, _ in self._getAddrAndValue(cpu):
            msr.writeMSR(cpu, addr + 1, 0)
            # Configure and enable de register
            msr.writeMSR(cpu, addr, value)
    
    def readValues(self, cpu):
        """
        Return the hw counter value of the given CPU

        Return : a dictionary with the values read. Dictionary output format:
            {
               'HW Counter Alias' : value
            }
        """
        dic = {}
        for addr, _, i in self._getAddrAndValue(cpu):
            # Read the hwCounter Value 
            value = msr.readMSR(cpu, addr + 1)
            # Save its value
            dic[i] = value
        return dic
    
