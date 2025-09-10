#!/home/user/Monitoring/venv/bin/python

import json
import os
import sys
import urllib.request
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/lib")

from pprint import pprint

from db import DbData, set_values

with urllib.request.urlopen("http://python/rrd/values") as url:
    data = json.loads(url.read().decode())

values = []
for database, item in data.items():
    timestamp = item['date']
    for key, value in item['ds'].items():
        values.append(DbData(host='klierlinge.de',
                             key=f'rrd/{database}/{key}',
                             value=value,
                             timestamp=timestamp))

db = set_values(values)

