#!/usr/bin/env python3

import smtplib

from datetime import datetime
from email.mime.text import MIMEText
import configparser

import os

_path = os.path.dirname(os.path.realpath(__file__))

def send_email(sender: str, subject: str, message: str):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

    config = configparser.ConfigParser()
    config.read(f'{_path}/mailconfig.ini')
    config_default = config['DEFAULT']

    msg['From'] = f'{sender} <{config_default["from"]}>'
    msg['To'] = config_default["to"]

    with smtplib.SMTP(config_default['server'], config_default['port']) as server:
        server.starttls()
        server.login(config_default['username'], config_default['password'])
        server.sendmail(msg['From'], msg['To'], msg.as_string())
    
if __name__ == '__main__':
    send_email('Tester', 'Mäil Test', 'Test Content\nHeitzölrückstoßabdämpfung\n\nENDE')
