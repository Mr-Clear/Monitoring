#!/usr/bin/env python3

import configparser
import os
import psycopg2
import time

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

_checks_buffer = {}

@dataclass
class DbData:
    host: str
    key: str
    value: str | None
    extra: str | None = None
    timestamp: datetime | None = None

@dataclass
class CheckStatus:
    id: int
    value_id: int
    host: str
    key: str
    value: str
    extra: str | None
    value_timestamp: datetime | None
    value_age: timedelta | None
    check: str
    arguments: str | None
    patience: timedelta
    fail_message: str | None
    repeat: timedelta
    is_good: bool | None
    check_status_since: datetime | None
    check_message: str | None
    last_check: datetime | None
    last_mail: datetime | None

    def __str__(self):
        r = ''""''
        if self.extra:
            r += f'{self.extra}\n\n'
        r += 'Status:'
        for k, v in self.__dict__.items():
            val = str(v).replace('\n', f'\n\t  {" " * len(k)}').strip()
            r += f'\n\t{k}: {val}'
        return r

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
    cur = conn.cursor()
    cur.execute(f"SET TIMEZONE TO '{time.tzname[0]}'")
    return conn

def set_values(data: List[DbData]):
    conn = _connect()
    cur = conn.cursor()

    for d in data:
        cur.execute(
            f"CALL monitoring.monitoring.set_value(%s::varchar, %s::varchar, %s::timestamp, %s::text, %s::text)",
            (d.host, d.key, d.timestamp, d.value, d.extra)
        )

    conn.commit()
    cur.close()
    conn.close()

def get_checks():
    conn = _connect()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM monitoring.monitoring.checks_overview"
    )

    checks = []
    for row in cur.fetchall():
        check = CheckStatus(
            id=row[0],
            value_id=row[1],
            host=row[2],
            key=row[3],
            value=row[4],
            extra=row[5],
            value_timestamp=row[6],
            value_age=row[7],
            check=row[8],
            arguments=row[9],
            patience=row[10],
            fail_message=row[11],
            repeat=row[12],
            is_good=row[13],
            check_status_since=row[14],
            check_message=row[15],
            last_check=row[16],
            last_mail=row[17]
        )
        checks.append(check)

    cur.close()
    conn.close()

    global _checks_buffer
    _checks_buffer = {check.id: check for check in checks}

    return checks

def set_check_status(check_id: int, last_check: datetime, is_good: bool, status_since: datetime, message: str | None = None, last_mail: datetime | None = None):
    conn = _connect()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO monitoring.monitoring.checks_status "
        "    (check_id, last_check, is_good, status_since, message, last_mail)"
        "VALUES (%s, %s, %s, %s, %s, %s)"
        "ON CONFLICT (check_id) DO UPDATE SET "
        "    last_check = excluded.last_check, "
        "    is_good = excluded.is_good, "
        "    status_since = excluded.status_since, "
        "    message = excluded.message, "
        "    last_mail = excluded.last_mail",
        (check_id, last_check, is_good, status_since, message, last_mail)
    )

    conn.commit()
    cur.close()
    conn.close()
