#!/bin/bash
snmpwalk -Op 10.8 -v 2c -m +WIENER-CRATE-MIB -c guru 192.168.48.46 $1 $2 $3
