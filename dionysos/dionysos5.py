#!/usr/bin/env python

import os
import sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/lib")

import db
import get_disk_usage
import get_loadavg
from subprocess import check_output, CalledProcessError, PIPE

disk_usage = get_disk_usage.query_disk_usage({None: ['/', '/home', '/mnt/disk/Daten', '/mnt/disk/SSD', '/mnt/disk/Windows10', '/mnt/disk/Vera']})
loadavg = get_loadavg.query_loadavg([None])
combined = disk_usage + loadavg

for d in combined:
    d.host = 'dionysos'

db.set_values(combined)
