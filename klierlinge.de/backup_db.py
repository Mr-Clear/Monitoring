#!/usr/bin/env python3

import os
import sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/lib")

import get_disk_usage
from db import get_backup

import json
from datetime import datetime, timedelta

script_path = os.path.dirname(os.path.realpath(__file__))

def _json_default(o):
    if isinstance(o, datetime):
        # ISO 8601, von Postgres als (timestamptz) erkannt
        return o.isoformat(sep=' ', timespec='seconds')
    if isinstance(o, timedelta):
        total_seconds = int(o.total_seconds())
        sign = '-' if total_seconds < 0 else ''
        total_seconds = abs(total_seconds)
        days, rem = divmod(total_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        if days:
            return f"{sign}{days} days {hours:02}:{minutes:02}:{seconds:02}"
        return f"{sign}{hours:02}:{minutes:02}:{seconds:02}"
    return str(o)

if __name__ == "__main__":
    data = get_backup()
    data['timestamp'] = datetime.now()
    with open(script_path + "/../checks_backup.json", "w") as f:
        json.dump(data, f, default=_json_default, indent=4)
