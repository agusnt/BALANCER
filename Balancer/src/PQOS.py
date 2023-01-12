#!/usr/bin/python3
"""
Class to manage PQOS with mutual exclusion

NOTE: in this file cpu refers to physical threads.

@AUTHOR: Navarro Torres, Agustín
@EMAIL: agusnt (at) unizar (dot) es
@DATE: 23/06/2020
@UPDATES:
"""
import msr
import time
import sys
from threading import Lock

class PQOS:
    """
    Class to manage PQOS with mutual exclusion.

    NOTE: multiple instance of this class gives a result undefined behavior. 
    Please be sure that you only instance this class one time in their life time.
    """
    ###########################################################################
    # Class attribute
    ###########################################################################
    _mutex = Lock()
    _rmid_core = {}
    _rmid = 1

    ###########################################################################
    # Private functions 
    ###########################################################################
    def _getRmid(self, cpu):
        """
        Return the RMID associate to that core (a new one or a existed one)

        Parameters:
            - cpu : the cpu that we want to know its RMID
        """
        if cpu in self._rmid_core:
            # We know this core, we return its associated RMID
            return self._rmid_core[cpu]

        self._rmid_core[cpu] = self._rmid
        self._rmid += 1

        return self._rmid_core[cpu]

    ###########################################################################
    # API functions
    ###########################################################################
    def l3Occupancy(self, on, cpu):
        """
        Set/Unset the L3 occupancy monitor.
    
        Parameters :
            on -> if true set the monitor, if off unset it
            cpu -> cpu
        """
    
        with(self._mutex):
            rmid = self._getRmid(cpu)
            # MSR Registers
            PQR_ASSOC = 0xC8F
            QM_EVTSEL = 0xC8D
    
            if on:
                # Set event and mask
                event = (rmid << 32) + 1
                aux = msr.readMSR(cpu, PQR_ASSOC)
                aux &= (~((1 << 9) - 1))
                rmid |= aux
    
                # Associate RMID with the processor
                msr.writeMSR(cpu, PQR_ASSOC, rmid)
                # Associate the event to measure
                msr.writeMSR(cpu, QM_EVTSEL, event)
            else:
                # Disable monitor
    
                # Associate the event to measure
                msr.writeMSR(cpu, QM_EVTSEL, 0)
    
    def l3OccupancyRead(self, cpu):
        """
        Read the L3 occupancy
    
        Parameters :
            - cpu : cpu
    
        Return :
            - Occupancy in bytes
        """
        with(self._mutex):
            # L3 Conversion factor
            factor = 64
    
            # MSR Registers
            QM_CTR = 0xC8E
            value = msr.readMSR(cpu, 0xC8E) * factor 
        return value

    def l3Allocation(self, on, cos, mask, cpu):
        """
        L3 Allocation enforcement
    
        Parameters :
            - on : if true set the monitor, if off unset it
            - cos : mask to associate
            - mask : ways/amount of cache to the givin core
            - cpu : cpu
        """

        with(self._mutex):
            rmid = self._getRmid(cpu)
            # MSR Registers
            PQR_ASSOC = 0xC8F
            PQR_MASK = 0xC90 + cos
            PQS_CFG = 0xC81
            msr.writeMSR(cpu, PQR_ASSOC, 0x0)
    
            if on:
                # Cos and Mask to associate with the processor
                value = (cos << 32) + rmid
                msr.writeMSR(cpu, PQR_ASSOC, value)
                # Associate Mask
                msr.writeMSR(cpu, PQR_MASK, mask)
            else:
                # Reset MSR Registers
                msr.writeMSR(cpu, PQR_ASSOC, rmid)
                msr.writeMSR(cpu, PQR_MASK, 0xFFFF)

    def bwAllocation(self, on, cos, mask, cpu):
        """
        Bandwidth Allocation enforcement

        Parameters :
            - on : if true set the monitor, if off unset it
            - cos : mask to associate
            - mask : max amount of bw to the given core
            - cpu : cpu to enforce the allocation
        """
        with(self._mutex):
            rmid = self._getRmid(cpu)
            # MSR Registers
            PQR_ASSOC = 0xC8F
            PQR_MASK = 0xC0000200 + cos

            if on:
                # Cos and Mask to associate with the processor
                value = (cos << 32) + rmid

                # Associate RMID with the processor
                msr.writeMSR(cpu, PQR_ASSOC, value)
                msr.writeMSR(cpu, PQR_MASK, mask)
            else:
                # Reset MSR Registers
                msr.writeMSR(cpu, PQR_ASSOC, rmid)
                msr.writeMSR(cpu, PQR_MASK, 2048)

    def reset(self, cpu):
        """
        Reset all configuration

        Parameters :
            - cpu : cpu
        """
        with(self._mutex):
            PQR_ASSOC = 0xC8F
            QM_EVTSEL = 0xC8D
            msr.writeMSR(cpu, PQR_ASSOC, 0)
            msr.writeMSR(cpu, QM_EVTSEL, 0)

        # Set new enforcement
        self.bwAllocation(False, 0, 2048, cpu)
        self.l3Allocation(False, 0, 0xFFFF, cpu)
