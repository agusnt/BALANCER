#!/usr/bin/python3
"""
API function to read / write MSR Register.

This API is tested to work on GNU/Linux using msr. Please, install and load
msr module to use it.

More information can be found at:
* MAN pages
* Ubuntu Manuals (https://manpages.ubuntu.com/manpages/trusty/man4/msr.4.html)
* Intel/msr-tools (https://github.com/intel/msr-tools)

@AUTHOR: Navarro Torres, Agustin
@EMAIL: agusnt (at) unizar (dot) es
@DATE: 21/04/2020
@UPDATES:
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
    # Close file descriptor
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
    # Close file descriptor
    os.close(f)

    return 

if __name__ == '__main__':
    # NOTE: An small test, ad-hoc developed. So there is high probabilities that
    # doesn't work on your machine

    # Read register associated to hardware counter select (Core 0)
    print("1st Read 0x{:02x}".format(readMSR(0, 0xC0010202)))
    print("Write 0x5300c0")
    writeMSR(0, 0xC0010202, 0x5300c0)
    print("2st Read 0x{:02x}".format(readMSR(0, 0xC0010202)))
