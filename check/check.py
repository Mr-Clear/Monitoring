#!/home/user/monitoring/venv/bin/python

import os
import sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/lib")

import db
import report

import re

from datetime import datetime, timedelta

def set_status(check: db.CheckStatus, is_good: bool, message: str = None):
    now = datetime.now()
    last_mail = check.last_mail
    status_since = check.check_status_since
    if not is_good \
       and now > check.check_status_since + check.patience \
       and (not check.last_mail \
            or now > check.last_mail + check.repeat):
        last_mail = now
        report.send_email(f'"{check.host} {check.key} {check.check} {check.arguments}"', message, str(check))
    elif is_good:
        last_mail = None

    if check.is_good != is_good:
        status_since = now

    db.set_check_status(check.id, now, is_good, status_since, message, last_mail)

def disk_space(check: db.CheckStatus):
    # Parse arguments
    regex = re.compile(r'^(\w+) ?(!?[<>]?=?) ?(\d+) ?((([kKMGT]?)(i?)B)|(%)|([smhd]))$')
    match = regex.match(check.arguments)
    if not match:
        print(f"Invalid argument for disk_space check: '{check.arguments}'", file=sys.stderr)
        report.send_email('Monitoring Engine', f'Invalid value for disk_space check: "{check.check}"', str(check))
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
            report.send_email('Monitoring Engine', f'Value age must have a time value: "{check.check}"', str(check))
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
                report.send_email('Monitoring Engine', f'Unknown time unit: "{time}"', str(check))
                return
        actual = check.value_age
    else:
        # Parse value
        numbers = check.value.split('/')
        if len(numbers) != 2:
            print(f"Cannot parse value for disk_space check: '{check.value}'", file=sys.stderr)
            report.send_email('Monitoring Engine', f'Cannot parse value for disk_space check: "{check.check}"', str(numbers))
            return
        try:
            used = int(numbers[0])
            total = int(numbers[1])
        except ValueError as e:
            print(f"Cannot parse value for disk_space check: '{check.value}'", file=sys.stderr)
            report.send_email('Monitoring Engine', f'Cannot parse value for disk_space check: "{check.check}"', str(e))
            return

        if value_name == 'usage':
            if not percent:
                print(f"Usage must have a percentage value: '{check.value}'", file=sys.stderr)
                report.send_email('Monitoring Engine', f'Usage must have a percentage value: "{check.check}"', str(check))
                return
            actual = round(int(numbers[0]) / int(numbers[1]) * 100)
        else:
            if match[5] is None:
                print(f"Value has no byte size: '{check.value}'", file=sys.stderr)
                report.send_email('Monitoring Engine', f'Value has no byte size: "{check.check}"', str(check))
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
                    report.send_email('Monitoring Engine', f'Unknown value name: "{value_name}"', str(check))
                    return
    
    match (operator):
        case '=':
            is_good = actual == number
        case '!=':
            is_good = actual != number
        case '>':
            is_good = actual > number
        case '>=':
            is_good = actual >= number
        case '<':
            is_good = actual < number
        case '<=':
            is_good = actual <= number
        case _:
            print(f"Unknown operator: '{operator}'", file=sys.stderr)
            report.send_email('Monitoring Engine', f'Unknown operator: "{operator}"', str(check))
            return

    message = check.fail_message.format(actual=actual, check=number) if not is_good and check.fail_message else None
    
    set_status(check, is_good, message)


if __name__ == "__main__":
    for check in db.get_checks():
        id = check.id
        match (check.check):
            case '':
                db.set_check_status(0, datetime.now(), True, check.check_status_since if check.check_status_since else datetime.now(), None, None)
            case 'disk_space':
                disk_space(check)
            case 'value_age':
                pass
            case _:
                print(f"Unknown check: '{check.check}'", file=sys.stderr)
                report.send_email('Monitoring Engine', f'Unknown check: "{check.check}"', str(check))
