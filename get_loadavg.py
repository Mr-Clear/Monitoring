
from .db import DbData

from subprocess import check_output, CalledProcessError, PIPE
from typing import Iterable, List

def get_loadavg(host: str|None) -> str | Exception:
    command = ['cat', '/proc/loadavg']
    if host:
        command = ['ssh', host] + command
    try:
        return check_output(command, stderr=PIPE).decode('utf-8').strip()
    except Exception as e:
        return e

def query_loadavg(hosts: Iterable[str]) -> List[DbData]:
    l = []
    for host in hosts:
        loadavg = get_loadavg(host)
        if isinstance(loadavg, str):
            l.append(DbData(host, 'loadavg', loadavg))
        elif isinstance(loadavg, CalledProcessError):
            l.append(DbData(host, 'loadavg', None, loadavg.stderr.decode('utf-8').strip()))
        else:
            l.append(DbData(host, 'loadavg', None, str(loadavg)))
    return l

if __name__ == '__main__':
    print(query_loadavg(['www.klierlinge.de', 'mail.klierlinge.de', 'Test']))
