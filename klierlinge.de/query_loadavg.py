#!/home/user/monitoring/venv/bin/python

import os
import sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/lib")

import get_loadavg
from db import set_values

ussage = get_loadavg.query_loadavg({'www.klierlinge.de': ['/', '/media/storage'], 'mail.klierlinge.de': ['/', '/mnt/HC_Volume_16021708']})
set_values(ussage)
