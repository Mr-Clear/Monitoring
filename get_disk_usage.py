#!/usr/bin/env python3

from subprocess import check_output
from typing import List
from dataclasses import dataclass

@dataclass
class Disk:
    host: str
    mount: str
    size: str
    used: str
    avail: str
    use: str

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
            disks.append(Disk(host, parts[5], parts[1], parts[2], parts[3], parts[4]))
        return disks
    except Exception as e:
        return str(e)

if __name__ == '__main__':
    print(get_disk_usage('mail.klierlinge.de'))
