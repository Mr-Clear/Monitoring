#!/usr/bin/env python3

import configparser
import os
import psycopg2

from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class DbData:
    host: str
    key: str
    value: str | None
    extra: str | None = None
    timestamp: datetime | None = None

_path = os.path.dirname(os.path.realpath(__file__))

def _connect():
    config = configparser.ConfigParser()
    config.read(f'{_path}/dbconfig.ini')
    config_default = config['DEFAULT']

    conn = psycopg2.connect(
        user=config_default['username'],
        password=config_default['password'],
        host=config_default['server'],
        port=int(config_default['port']),
        database=config_default['database']
    )
    return conn

def set_values(data: List[DbData]):
    conn = _connect()
    cur = conn.cursor()

    for d in data:
        cur.execute(
            f"CALL monitoring.monitoring.set_value(%s, %s, %s, %s, %s)",
            (d.host, d.key, d.timestamp, d.value, d.extra)
        )

    conn.commit()
    cur.close()
    conn.close()
