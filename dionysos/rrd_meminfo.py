#!/usr/bin/env python

import rrd

info = []
with open('/proc/meminfo') as f:
    for line in f:
        key, value = line.split(':')
        info.append(int(value.strip().split()[0]) * 1024)

rrd.update('dionysos_meminfo', *info)
