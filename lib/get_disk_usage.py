
from db import DbData

from subprocess import check_output, CalledProcessError, PIPE
from typing import List, Dict, Iterable
from dataclasses import dataclass

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
    command = ['df', '-B1']
    if host:
        command = ['ssh', host] + command
    try:
        df = check_output(command, stderr=PIPE).decode('utf-8').split('\n')
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
        return e

def query_disk_usage(d: Dict[str, Iterable[str]]) -> List[DbData]:
    ret = []
    for host, mounts in d.items():
        disks = get_disk_usage(host)
        if isinstance(disks, list):
            for disk in disks:
                if disk.mount in mounts:
                    ret.append(DbData(host, f'Disk:{disk.mount}', f'{disk.used}/{disk.size}', disk.extra))
        elif isinstance(disks, CalledProcessError):
            for mount in mounts:
                ret.append(DbData(host, f'Disk:{mount}', None, disks.stderr.decode('utf-8').strip()))
        else:
            for disk in disks:
                if disk.mount in mounts:
                    ret.append(DbData(host, f'Disk:{disk.mount}', None, str(disk)))

    return ret
