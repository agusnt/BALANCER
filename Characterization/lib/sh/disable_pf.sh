#!/bin/bash

#
# Disable HW Prefetch on AMD processor (Tested: AMD Epyc 7702P)
#
#@AUTHOR: Navarro Torres, Agustin (agusnt@unizar.es)
#@DATE: 21/04/2021
#

if [ "$EUID" -ne 0 ]; then
	echo "Please run as root"
	exit 1
fi

wrmsr -a 0xc0011022 0xc000000002502000
