# BALANCER: LLC Characterization

This directory contains one directory with the scripts that take metrics of
all CPU2006 and CPU2017 benchmarks (application + reference inputs).

You should probably have to change some variables. 
They are initialized at the beginning of each file and come with a brief description.

## Scripts

* **sh/run.sh**: measure the performance and cache information when the
  CPU2006 and CPU2017 benchmarks are running with different LLC capacity 
  restrictions.
* **sh/2k6.sh**: measure the performance and cache information when the
  CPU2006 benchmarks is running with different LLC capacity restrictions.
* **sh/2k17.sh**: measure the performance and cache information when the
  CPU2017 benchmarks is running with different LLC capacity restrictions.

  To run any scripts just:

## Running

* Change the initial vars with your proper values (e.g. folder where the SPEC CPU2006 were compiled)
* Type:

    ```Bash
    ./script_name.sh
    ```
