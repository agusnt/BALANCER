# BALANCER

Balancer is a set of mechanisms that controls last level cache (LLC) space and 
memory traffic allocations (DRAM bandwidth) to improve system performance and 
fairness when running multiprogrammed workloads.

More details on how Balancer works is available in the following paper. 

## Platform

Balancer was developed and tested on an 64-core/128-thread AMD EPYC 7702P which
supports LLC and DRAM-BW partitioning. The system was running CentOS Linux 8,
Linux kernel version 4.18.0 and Python 3.6.8

## Requirements

* An AMD processor with [PQoSE](https://www.amd.com/system/files/TechDocs/56375_1.03_PUB.pdf).
* A GNU/Linux system with capabilities to read/write MSR registers (
`msr-tools`, `taskset`, root access...).
* `Python3` with `numpy`, `psutil` and `json` packages.

## Directories

* **Characterization**: scripts and data to reproduce section 3.
* **Balancer**: Balancer source code.

## Cite this
