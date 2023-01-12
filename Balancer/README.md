# BALANCER: Bandwidth ALlocation ANd CachE paRtitioning

Source code for balancer. 

## Requirements

* An AMD processor with [PQoSE](https://www.amd.com/system/files/TechDocs/56375_1.03_PUB.pdf).
* A GNU/Linux system with capabilities to read/write MSR registers (
`msr-tools`, `taskset`, root access...).
* `python3` with `numpy`, `psutil` and `json` packages

## Running Balancer

`taskset -c <schedule core> src/main.py <json config file> <schedule core>`

Parameters:
* **json config file**: configuration json file
* **schedule core**: physical thread where balancer will run

**NOTE**: Use `taskset` or equivalent to pin Balancer to a physical thread

### Config file

Example of the configuration file to run balancer. These are default values for
AMD Rome 7702P and increase performance. Modify them according to your processor
and the purpose of balancer (performance or fairness).
```json
{
    "cmd": "mix.in", # File with the applications to run
    "alg": "llcbw", # Constrain algorithm to use (llc, bw, llcbw, static, ucp)
    "hpmo_limit": 0.06, # HpMO value to trigger the LLC constrain
    "hpmo_max": 0.065, # HpMO value to unconstrain LLC
    "lat_limit": 450, # Latency limit to trigger BW constrain
    "threads": [0, 1, 2, 3], # Number of threads to monitor
    "hwCounters": { # List of hardware counter to use
        "Instr Retired": { # Hardware counter name
            "addr": "0xC0010200", # MSR address
            "value": "0x5100c0" # Value
        },
        "Cycles": {
            "addr": "0xC0010202",
            "value": "0x510076"
        },
        "L3HitDC": {
            "addr": "0xC0010204",
            "value": "0x511243"
        },
        "L3MissDC": {
            "addr": "0xC0010206",
            "value": "0x514843"
        },
        "L3HitPF": {
            "addr": "0xC0010208",
            "value": "0x51125A"
        },
        "L3HitPFL2": {
            "addr": "0xC001020A",
            "value": "0x513F71"
        },
        "L3Miss": {
            "addr": "0xC0010230",
            "value": "0x0F000000400106"
        },
        "L3Latency1": {
            "addr": "0xC0010238",
            "value": "0xFF0F000000400090"
        },
        "L3Latency2": {
            "addr": "0xC001023A",
            "value": "0xFF0F000000401B9A"
        }
    },
    "tepoch": 1, # Epoch time
    "limit": 1.2, # LLC accesses to detect phase changes (1.2 is 20%)
    "rolling": 10, # Last n-values to use in the average
    "bw_limit": 2.5, # Maximum bandwidth that can be given to a constrained thread (Gb/s)
    "file_log": "log" # Log file
}
```

### input.in

This file has the applications to be run during a balancer experiment.

The file structure is: `<physical thread> <bash command>`

Example:
```
0 /usr/bin/ls
1 /usr/bin/ls -l
2 /usr/bin/ls -lh
3 /usr/bin/ls -la
```
