#!/mnt/ssd/home/thomas/Develop/Monitoring/venv/bin/python

import os
import sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/lib")

import db
import get_disk_usage
import get_loadavg
from subprocess import check_output, CalledProcessError, PIPE

disk_usage = get_disk_usage.query_disk_usage({None: ['/', '/mnt/ssd', '/mnt/External2TB']})
loadavg = get_loadavg.query_loadavg([None])
combined = disk_usage + loadavg

for d in combined:
    d.host = 'homepi'

db.set_values(combined)
