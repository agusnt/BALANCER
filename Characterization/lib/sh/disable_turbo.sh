#!/bin/bash

#
# Disable Turbo Boos on AMD processor (Tested: AMD Epyc 7702P)
#
#@AUTHOR: Navarro Torres, Agustin (agusnt@unizar.es)
#@DATE: 21/04/2021
#

if [ "$EUID" -ne 0 ]; then
	echo "Please run as root"
	exit 1
fi

echo 0 > /sys/devices/system/cpu/cpufreq/boost
