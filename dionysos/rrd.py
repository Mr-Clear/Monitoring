import json
import logging
import os
import requests
import urllib3

from dataclasses import dataclass
from datetime import time, datetime, date, timedelta
from enum import Enum
from filelock import FileLock
from time import mktime
from timeit import default_timer
from typing import List, Optional, Union

log = logging.getLogger(__name__)

# noinspection PyUnresolvedReferences
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_url = 'https://www.klierlinge.de/rrd'
buffer_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'buffer.txt')


class RrdException(Exception):
    def __init__(self, message):
        super().__init__(message)


class DataSourceType(Enum):
    GAUGE = 1
    COUNTER = 2
    DCOUNTER = 3
    DERIVE = 4
    DDERIVE = 5
    ABSOLUTE = 6
    COMPUTE = 7


@dataclass()
class DataSource:
    name: str
    ds_type: DataSourceType = DataSourceType.GAUGE
    heartbeat: int = 90
    min: Optional[float] = None
    max: Optional[float] = None


class RoundRobinArchiveType(Enum):
    AVERAGE = 1
    MIN = 2
    MAX = 3
    LAST = 4


@dataclass()
class RoundRobinArchive:
    consolidation_function: RoundRobinArchiveType
    xfiles_factor: float
    singe_time: timedelta
    overall_time: timedelta


def default_rra_list() -> List[RoundRobinArchive]:
    r = RoundRobinArchive
    t = RoundRobinArchiveType
    return [r(t.AVERAGE, 0.9, timedelta(minutes=1),  timedelta(days=31)),
            r(t.AVERAGE, 0.5, timedelta(minutes=10), timedelta(days=731)),
            r(t.MIN,     0.5, timedelta(minutes=10), timedelta(days=731)),
            r(t.MAX,     0.5, timedelta(minutes=10), timedelta(days=731)),
            r(t.AVERAGE, 0.5, timedelta(hours=1),    timedelta(days=36525)),
            r(t.MIN,     0.5, timedelta(hours=1),    timedelta(days=36525)),
            r(t.MAX,     0.5, timedelta(hours=1),    timedelta(days=36525)),
            r(t.AVERAGE, 0.5, timedelta(days=1),     timedelta(days=36525)),
            r(t.MIN,     0.5, timedelta(days=1),     timedelta(days=36525)),
            r(t.MAX,     0.5, timedelta(days=1),     timedelta(days=36525))]


def unix_timestamp(time: Union[datetime, date, time]) -> int:
    return int(mktime(time.timetuple()))


def buffer_api_call(function: str, args: List[str]):
    with open(buffer_file, 'a', encoding='UTF-8') as file:
        file.write(json.dumps({'function': function, 'args': args}) + '\n')


def flush_buffer():
    lock_file = f'{buffer_file}.lock'
    with FileLock(lock_file):
        if os.path.isfile(buffer_file):
            log.info('Starting to upload buffered data...')
            start_time = default_timer()
            count = 0
            with open(buffer_file, 'r', encoding='UTF-8') as file:
                for line in file:
                    buffered = json.loads(line)
                    api_call(buffered['function'], buffered['args'], buffer_on_fail=False)
            os.remove(buffer_file)
            log.info(f'Uploaded {count} datasets in {timedelta(seconds=default_timer()-start_time)} seconds:')


def api_call(function: str, args: List[str], buffer_on_fail: bool = False):
    url = f'{base_url}/{function}'

    if buffer_on_fail:
        try:
            flush_buffer()
        except requests.exceptions.ConnectionError as e:
            buffer_api_call(function, args)
            return

    print("create " + " ".join(args))

    try:
        result = requests.post(url, json={'args': args}, verify=False)
    except requests.exceptions.ConnectionError as e:
        if buffer_on_fail:
            log.warning(f'Failed to contact "{base_url}". Writing data to "{buffer_file}".')
            buffer_api_call(function, args)
            return
        else:
            raise e

    content = result.content.decode("utf-8")
    if content:
        data = json.loads(content)
    else:
        data = None

    if result:
        return data
    else:
        if result.status_code == 400:
            raise RrdException(f'Error when calling "{function}": {data["error_type"]} - {data["error_message"]}')
        if result.status_code == 404:
            raise RrdException(f'URL not found: {url}')


def create(name: str, data_sources: List[DataSource], archives: List[RoundRobinArchive],
           step: timedelta = timedelta(seconds=60), overwrite: bool = False):
    args = [f'{name}.rrd']
    args.extend(['--step', str(int(step.total_seconds()))])
    args.extend(['--start', f'{unix_timestamp(date(date.today().year, 1, 1))}'])
    if not overwrite:
        args.append('--no-overwrite')
    for ds in data_sources:
        args.append(f'DS:{ds.name}:{ds.ds_type.name}:{ds.heartbeat}:'
                    f'{ds.min if ds.min else "U"}:{ds.max if ds.max else "U"}')
    for rra in archives:
        args.append(f'RRA:{rra.consolidation_function.name}:{rra.xfiles_factor}:'
                    f'{int(rra.singe_time.total_seconds() / step.total_seconds())}:'
                    f'{int(rra.overall_time.total_seconds() / rra.singe_time.total_seconds())}')
    api_call('create', args)


def update(name: str, *params, timestamp: Optional[datetime] = None, buffer_on_fail: bool = False):
    if not timestamp:
        timestamp = datetime.now()
    s = ':'.join([*map(str, [unix_timestamp(timestamp), *params])])
    api_call('update', [f'{name}.rrd', s], buffer_on_fail=buffer_on_fail)
