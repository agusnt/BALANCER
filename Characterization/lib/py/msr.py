#!/usr/bin/python3

"""
Functions to read and write MSR registers

@Author: Navarro Torres, Agustin (agusnt@unizar.es)
@Date: 21/04/2020
"""
import os
import struct

def readMSR (cpu, reg):
    """
    Read the given MSR in the given CPU.

    Parameters : 
        cpu : cpu number
        reg : msr register

    Return :
        Reading value
    """
    dmsr = "/dev/cpu/{}/msr".format(cpu)
    # Open the MSR interface
    f = os.open(dmsr, os.O_RDONLY)
    # Seek the MSR register
    os.lseek(f, reg, os.SEEK_SET)
    # Read the register
    value = struct.unpack('Q', os.read(f, 8))[0]
    os.close(f)

    return value

def writeMSR (cpu, reg, value):
    """
    Write the given MSR in the given CPU.

    Parameters : 
        cpu : cpu number
        reg : msr register
        value : value to write into the msr
    """
    dmsr = "/dev/cpu/{}/msr".format(cpu)
    # Open the MSR interface
    f = os.open(dmsr, os.O_WRONLY)
    # Seek the MSR register
    os.lseek(f, reg, os.SEEK_SET)
    # Read the register
    os.write(f, struct.pack('Q', value))
    os.close(f)
    return value

if __name__ == '__main__':
    # Read register associated to hardware counter select (Core 0)
    print("1st Read 0x{:02x}".format(readMSR(0, 0xC0010202)))
    print("Write 0x5300c0")
    writeMSR(0, 0xC0010202, 0x5300c0)
    print("2st Read 0x{:02x}".format(readMSR(0, 0xC0010202)))
