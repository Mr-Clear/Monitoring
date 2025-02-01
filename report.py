#!/usr/bin/env python3

import smtplib

from email.mime.text import MIMEText
import configparser

def send_email(sender: str, subject: str, message: str):
    msg = MIMEText(message)
    msg['Subject'] = subject

    config = configparser.ConfigParser()
    config.read('mailconfig.ini')
    config_default = config['DEFAULT']

    msg['From'] = f'{sender} <{config_default["from"]}>'
    msg['To'] = config_default["to"]

    with smtplib.SMTP(config_default['server'], config_default['port']) as server:
        server.starttls()
        server.login(config_default['username'], config_default['password'])
        server.sendmail(msg['From'], msg['To'], msg.as_string())
    
    
if __name__ == '__main__':
    send_email('Tester', 'Mail Test', 'Test Content')