# BALANCER: DRAM-BW Characterization

This directory contains two directories with the scripts that take metrics of
all CPU2006 and CPU2017 benchmarks (application + reference inputs).

You should probably have to change some variables. 
They are initialized at the beginning of each file (and in line 135) and come 
with a brief description.

## Scripts

* **sh/run.sh**: measure the performance and cache information when the
  CPU2006 and CPU2017 benchmarks are running with different DRAM-bandwidth 
  restrictions.

## Requirements

A C compiler. The experiments were tested with gcc 8.4.1

## Running

To run any scripts just:

* Change the initial vars with your proper values (e.g. folder where the SPEC CPU2006 were compiled)
* Type:

    ```Bash
    ./script_name.sh
    ```
