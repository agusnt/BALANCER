#!/usr/bin/python3
import msr
import time
from sys import exit

def bw(on, rmid, cpu):
    """
    Set/Unset the BW occupancy monitor.

    Parameters :
        on -> if true set the monitor, if off unset it
        rmid -> rmid to associate
        cpu -> cpu
    """

    # MSR Registers
    PQR_ASSOC = 0xC8F
    QM_EVTSEL = 0xC8D

    if on:
        # Enable monitor
        # Associate RMID with the processor
        event = (rmid << 32) + 3
        rmid |= msr.readMSR(cpu, PQR_ASSOC)

        msr.writeMSR(cpu, PQR_ASSOC, rmid)
        # Associate the event to measure
        msr.writeMSR(cpu, QM_EVTSEL, event)
    else:
        # Disable monitor
        msr.writeMSR(cpu, PQR_ASSOC, 0)

def l3Occupancy(on, rmid, cpu):
    """
    Set/Unset the L3 occupancy monitor.

    Parameters :
        on -> if true set the monitor, if off unset it
        rmid -> rmid to associate
        cpu -> cpu
    """

    # MSR Registers
    PQR_ASSOC = 0xC8F
    QM_EVTSEL = 0xC8D

    if on:
        # Enable monitor

        # Set event
        event = (rmid << 32) + 1
        rmid |= msr.readMSR(cpu, PQR_ASSOC)

        # Associate RMID with the processor
        msr.writeMSR(cpu, PQR_ASSOC, rmid)
        # Associate the event to measure
        msr.writeMSR(cpu, QM_EVTSEL, event)
    else:
        # Disable monitor

        # Associate RMID with the processor
        msr.writeMSR(cpu, PQR_ASSOC, 0)
        # Associate the event to measure
        msr.writeMSR(cpu, QM_EVTSEL, 0)

def l3OccupancyRead(cpu):
    """
    Read the L3 occupancy

    Parameters :
        cpu -> cpu

    Return :
        Occupancy in bytes
    """

    # L3 Conversion factor
    factor = 64

    # MSR Registers
    QM_CTR = 0xC8E

    return msr.readMSR(cpu, 0xC8E) * factor

def bwRead(cpu):
    """
    Read the BW occupancy

    Parameters :
        cpu -> cpu

    Return :
        Occupancy in bytes
    """

    # L3 Conversion factor
    factor = 64

    # MSR Registers
    QM_CTR = 0xC8E

    return msr.readMSR(cpu, 0xC8E) * factor

def l3Allocation(on, cos, rmid, mask, cpu):
    """
    L3 Allocation enforcement

    Parameters :
        on -> if true set the monitor, if off unset it
        cos -> mask to associate
        rmid -> rmid to associate
        mask -> ways/amount of cache to the givin core
        cpu -> cpu
    """

    # MSR Registers
    PQR_ASSOC = 0xC8F
    PQR_MASK = 0xC90 + cos
    PQR_QOS_CFGI = 0xC81

    # Disable CPD
    msr.writeMSR(cpu, PQR_QOS_CFGI, 0)

    if on:
        # Cos and Mask to associate with the processor
        value = (cos << 32) + rmid
        msr.writeMSR(cpu, PQR_ASSOC, value)
        # Associate Mask
        msr.writeMSR(cpu, PQR_MASK, mask)
    else:
        # Reset MSR Registers
        msr.writeMSR(cpu, PQR_ASSOC, 0)
        msr.writeMSR(cpu, PQR_MASK, 0)

def l3CPDAllocation(on, cos, rmid, maskI, maskD, cpu):
    """
    L3 CPD Allocation enforcement

    Parameters :
        on -> if true set the monitor, if off unset it
        cos -> mask to associate
        rmid -> rmid to associate
        maskI -> ways/amount of cache to the giving core (instructions)
        maskD -> ways/amount of cache to the giving core (data)
        cpu -> cpu
    """

    # MSR Registers
    PQR_ASSOC = 0xC8F
    PQR_QOS_CFGI = 0xC81
    PQR_MASKD = 0xC90 + (2 * cos)
    PQR_MASKI = 0xC91 + (2 * cos)

    # Set bit 0 PQR_QOS_CFGI
    msr.writeMSR(cpu, PQR_QOS_CFGI, 1)

    if on:
        # Cos and Mask to associate with the processor
        value = (cos << 32) + rmid
        msr.writeMSR(cpu, PQR_ASSOC, value)
        # Associate Mask
        msr.writeMSR(cpu, PQR_MASKI, maskI)
        msr.writeMSR(cpu, PQR_MASKD, maskD)
    else:
        # Reset MSR Registers
        msr.writeMSR(cpu, PQR_ASSOC, 0)
        msr.writeMSR(cpu, PQR_MASKI, 0)
        msr.writeMSR(cpu, PQR_MASKD, 0)
        msr.writeMSR(cpu, PQR_QOS_CFGI, 0)

if __name__ == "__main__":
    # Measure occupancy core 0
    l3Occupancy(True, 1, 0)

    # Loop until one key is pressed
    print("16MiB of Cache -- CPU 0")
    try:
        while True:
            value = l3OccupancyRead(0) / 1024 / 1024
            print("L3 Occupancy: {:05.2f} MiB".format(value), end = "\r")
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    # Loop until one key is pressed
    l3Allocation(True, 1, 1, 0xFF00, 0)
    print("8MiB of Cache -- CPU 0")
    try:
        while True:
            value = l3OccupancyRead(0) / 1024 / 1024
            print("L3 Occupancy: {:05.2f} MiB".format(value), end = "\r")
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    # Loop until one key is pressed
    l3Allocation(True, 1, 1, 0x0001, 0)
    print("1MiB of Cache -- CPU 0")
    try:
        while True:
            value = l3OccupancyRead(0) / 1024 / 1024
            print("L3 Occupancy: {:05.2f} MiB".format(value), end = "\r")
            time.sleep(1)
    except KeyboardInterrupt:
        pass


    # Loop until one key is pressed
    l3Allocation(True, 1, 1, 0x0000, 0)
    print("0MiB of Cache -- CPU 0")
    try:
        while True:
            value = l3OccupancyRead(0) / 1024 / 1024
            print("L3 Occupancy: {:05.2f} MiB".format(value), end = "\r")
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    # Disable monitor and enformcement
    l3Occupancy(False, 0, 0)
    l3Allocation(False, 1, 0, 0, 0)

    # Measure BW
    bw(True, 1, 0)
    try:
        old = 0
        while True:
            value = l3OccupancyRead(0) / 1024 / 1024
            if (value > old):
                print("L3 BW: {:07.2f} MiB".format(value - old), end = "\r")
                old = value
            else:
                old = 0
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    print("Finish")

    bw(False, 0, 0)
