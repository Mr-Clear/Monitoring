#!/home/user/Monitoring/venv/bin/python

import os
import sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/lib")

import db
from email_report import send_email

import re

from datetime import datetime, timedelta

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
                                        check_status_since_duration=now-check.check_status_since,
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
    
    is_good = compare(actual, number, operator)
    if is_good is not None:
        set_status(check, is_good, actual)

def number(check: db.CheckStatus):
    regex = re.compile(r'^(!?[<>]?=?) ([\d.]+)$')
    match = regex.match(check.arguments)
    if not match:
        print(f"Invalid argument for number check: '{check.arguments}'", file=sys.stderr)
        send_email('Monitoring Engine', f'Invalid value for number check: "{check.check}"', str(check))
        return

    number = float(match[2])
    is_good = compare(check.value, number, match[1])
    if is_good is not None:
        set_status(check, is_good, number)

if __name__ == "__main__":
    for check in db.get_checks():
        id = check.id
        match (check.check):
            case '':
                db.set_check_status(0, datetime.now(), True, check.check_status_since if check.check_status_since else datetime.now(), None, None)
            case 'number':
                number(check)
            case 'disk_space':
                disk_space(check)
            case 'value_age':
                pass
            case _:
                print(f"Unknown check: '{check.check}'", file=sys.stderr)
                send_email('Monitoring Engine', f'Unknown check: "{check.check}"', str(check))
