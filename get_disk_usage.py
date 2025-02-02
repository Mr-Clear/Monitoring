#!/usr/bin/env python3

from subprocess import check_output
from typing import List, Dict, Iterable
from dataclasses import dataclass
from .db import DbData

@dataclass
class Disk:
    host: str
    mount: str
    size: str
    used: str
    avail: str
    use: str
    extra: str

def get_disk_usage(host: str|None) -> List[Disk]|str:
    command = ['df']
    if host:
        command = ['ssh', host] + command
    try:
        df = check_output(command).decode('utf-8').split('\n')
        disks = []
        for line in df:
            if line.startswith('Filesystem'):
                continue
            if not line:
                continue
            parts = line.split()
            disks.append(Disk(host, parts[5], parts[1], parts[2], parts[3], parts[4], line))
        return disks
    except Exception as e:
        return str(e)

def query_disk_usage(d: Dict[str, Iterable[str]]) -> List[DbData]:
    ret = []
    for host, mounts in d.items():
        disks = get_disk_usage(host)
        if isinstance(disks, str):
            for disk in disks:
                ret.append(DbData(host, f'Disk:{disk.mount}', None, disks))
        else:
            for disk in disks:
                if disk.mount in mounts:
                    ret.append(DbData(host, f'Disk:{disk.mount}', f'{disk.used}/{disk.size}', disk.extra))
    return ret

if __name__ == '__main__':
    print(get_disk_usage('mail.klierlinge.de'))
