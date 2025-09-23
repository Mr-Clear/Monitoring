#!/home/user/Monitoring/venv/bin/python

import os
import sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/lib")

import db
from email_report import send_email

import re
import traceback
from datetime import datetime, timedelta

def set_and_check_status(check: db.CheckStatus, operator: str, actual_value, check_value):
    is_good = compare(actual_value, check_value, operator)
    if is_good is not None:
        set_status(check, is_good, actual_value)

def set_status(check: db.CheckStatus, is_good: bool, actual):
    now = datetime.now()
    last_mail = check.last_mail
    status_since = check.check_status_since
    send_mail = False
    if status_since is None:
        status_since = now
    if not is_good \
       and now > status_since + check.patience \
       and (not check.last_mail \
            or now > check.last_mail + check.repeat):
        send_mail = True
    elif is_good:
        last_mail = None

    if check.is_good != is_good:
        status_since = now

    message = check.fail_message.format(actual=actual,
                                        id=check.id,
                                        host=check.host,
                                        key=check.key,
                                        value=check.value,
                                        extra=check.extra,
                                        value_timestamp=check.value_timestamp,
                                        value_age=check.value_age,
                                        check=check.check,
                                        arguments=check.arguments,
                                        patience=check.patience,
                                        fail_message=check.fail_message,
                                        repeat=check.repeat,
                                        is_good=check.is_good,
                                        check_status_since=check.check_status_since,
                                        check_status_since_duration=now-check.check_status_since if check.check_status_since else None,
                                        check_message=check.check_message,
                                        last_check=check.last_check,
                                        last_mail=check.last_mail
                                        ) \
        if not is_good and check.fail_message else None

    if send_mail:
        last_mail = now
        send_email(f'"{check.host} {check.key} {check.check} {check.arguments}"', message, str(check))

    db.set_check_status(check.id, now, is_good, status_since, message, last_mail)

def compare(a, b, operator: str) -> bool | None:
    match (operator):
        case '=':
            return a == b
        case '!=':
            return a != b
        case '>':
            return a > b
        case '>=':
            return a >= b
        case '<':
            return a < b
        case '<=':
            return a <= b
        case _:
            print(f"Unknown operator: '{operator}'", file=sys.stderr)
            send_email('Monitoring Engine', f'Unknown operator: "{operator}"', str(check))
            return None

def disk_space(check: db.CheckStatus):
    # Parse arguments
    regex = re.compile(r'^(\w+) ?(!?[<>]?=?) ?(\d+) ?((([kKMGT]?)(i?)B)|(%)|([smhd]))$')
    match = regex.match(check.arguments)
    if not match:
        print(f"Invalid argument for disk_space check: '{check.arguments}'", file=sys.stderr)
        send_email('Monitoring Engine', f'Invalid value for disk_space check: "{check.check}"', str(check))
        return
    value_name = match[1]
    operator = match[2]
    number = int(match[3])
    prefix = match[6]
    binary = match[7]
    percent = match[8]
    time = match[9]

    if value_name == 'value_age':
        if not time:
            print(f"Value age must have a time value: '{check.value}'", file=sys.stderr)
            send_email('Monitoring Engine', f'Value age must have a time value: "{check.check}"', str(check))
            return
        match (time):
            case 's':
                number = timedelta(seconds=int(numbers[2]))
            case 'm':
                number = timedelta(minutes=int(numbers[2]))
            case 'h':
                number = timedelta(hours=int(numbers[2]))
            case 'd':
                number = timedelta(days=int(numbers[2]))
            case _:
                print(f"Unknown time unit: '{time}'", file=sys.stderr)
                send_email('Monitoring Engine', f'Unknown time unit: "{time}"', str(check))
                return
        actual = check.value_age
    else:
        # Parse value
        numbers = check.value.split('/')
        if len(numbers) != 2:
            print(f"Cannot parse value for disk_space check: '{check.value}'", file=sys.stderr)
            send_email('Monitoring Engine', f'Cannot parse value for disk_space check: "{check.check}"', str(numbers))
            return
        try:
            used = int(numbers[0])
            total = int(numbers[1])
        except ValueError as e:
            print(f"Cannot parse value for disk_space check: '{check.value}'", file=sys.stderr)
            send_email('Monitoring Engine', f'Cannot parse value for disk_space check: "{check.check}"', str(e))
            return

        if value_name == 'usage':
            if not percent:
                print(f"Usage must have a percentage value: '{check.value}'", file=sys.stderr)
                send_email('Monitoring Engine', f'Usage must have a percentage value: "{check.check}"', str(check))
                return
            actual = round(int(numbers[0]) / int(numbers[1]) * 100)
        else:
            if match[5] is None:
                print(f"Value has no byte size: '{check.value}'", file=sys.stderr)
                send_email('Monitoring Engine', f'Value has no byte size: "{check.check}"', str(check))
                return

            if binary:
                number = number * 1024 ** 'BKMGT'.index(prefix)
            else:
                number = number * 1000 ** 'BKMGT'.index(prefix)


            match (value_name):
                case 'free':
                    actual = int(numbers[1]) - int(numbers[0])
                case 'used':
                    actual = int(numbers[0])
                case 'size':
                    actual = int(numbers[1])
                case _:
                    print(f"Unknown value name: '{value_name}'", file=sys.stderr)
                    send_email('Monitoring Engine', f'Unknown value name: "{value_name}"', str(check))
                    return

    set_and_check_status(check, operator, actual, number)

def loadavg(check: db.CheckStatus):
    arg_regex = re.compile(r'^((1min)|(5min)|(15min)|(running)|(total)|(pid)) (!?[<>]?=?) ([\d.]+)$')
    arg_match = arg_regex.match(check.arguments)
    if not arg_match:
        print(f"Invalid argument for loadavg check: '{check.arguments}'", file=sys.stderr)
        send_email('Monitoring Engine', f'Invalid value for loadavg check: "{check.check}"', str(check))
        return
    arg_type = arg_match[1]
    arg_operator = arg_match[8]
    arg_value = float(arg_match[9])

    val_regex = re.compile(r'^([\d.]+) ([\d.]+) ([\d.]+) (\d+)/(\d+) (\d+)$')
    val_match = val_regex.match(check.value)
    if not val_match:
        print(f"Invalid value for loadavg check: '{check.value}'", file=sys.stderr)
        send_email('Monitoring Engine', f'Invalid value for loadavg check: "{check.check}"', str(check))
        return

    match (arg_type):
        case '1min':
            actual = float(val_match[1])
        case '5min':
            actual = float(val_match[2])
        case '15min':
            actual = float(val_match[3])
        case 'running':
            actual = int(val_match[4])
        case 'total':
            actual = int(val_match[5])
        case 'pid':
            actual = int(val_match[6])
        case _:
            print(f"Unknown argument for loadavg check: '{arg_type}'", file=sys.stderr)
            send_email('Monitoring Engine', f'Unknown argument for loadavg check: "{check.check}"', str(check))
            return

    set_and_check_status(check, arg_operator, actual, arg_value)

def number(check: db.CheckStatus):
    regex = re.compile(r'^(!?[<>]?=?) ([\d.]+)$')
    match = regex.match(check.arguments)
    if not match:
        print(f"Invalid argument for number check: '{check.arguments}'", file=sys.stderr)
        send_email('Monitoring Engine', f'Invalid value for number check: "{check.check}"', str(check))
        return

    set_and_check_status(check, match[1], check.value, float(match[2]))

def value_age(check: db.CheckStatus):
    regex = re.compile(r'^(!?[<>]?=?) ((\d+)y)?((\d+)M)?((\d+)w)?((\d+)d)?((\d+)h)?((\d+)m)?((\d+)s)?$')
    match = regex.match(check.arguments)
    if not match:
        print(f"Invalid argument for time delta check: '{check.arguments}'", file=sys.stderr)
        send_email('Monitoring Engine', f'Invalid argument for time delta check: "{check.check}"', str(check))
        return
    years = int(match[3]) if match[3] else 0
    months = int(match[5]) if match[5] else 0
    weeks = int(match[7]) if match[7] else 0
    days = int(match[9]) if match[9] else 0
    hours = int(match[11]) if match[11] else 0
    minutes = int(match[13]) if match[13] else 0
    seconds = int(match[15]) if match[15] else 0
    td = timedelta(days=years*365 + months*30 + weeks*7 + days, hours=hours, minutes=minutes, seconds=seconds)

    set_and_check_status(check, match[1], check.value_age, td)

if __name__ == "__main__":
    for check in db.get_checks():
        id = check.id
        try:
            match (check.check):
                case '':
                    db.set_check_status(0, datetime.now(), True, check.check_status_since if check.check_status_since else datetime.now(), None, None)
                case 'number':
                    number(check)
                case 'disk_space':
                    disk_space(check)
                case 'loadavg':
                    loadavg(check)
                case 'value_age':
                    value_age(check)
                case _:
                    print(f"Unknown check: '{check.check}'", file=sys.stderr)
                    send_email('Monitoring Engine', f'Unknown check: "{check.check}"', str(check))
        except Exception as e:
            print(f"Error in check {id} {check.check} {check.arguments}: {e}", file=sys.stderr)
            send_email('Monitoring Engine', f'Error in check {id} {check.check} {check.arguments}',
                       f'{check}\n\n{e}\n{traceback.format_exc()}')
