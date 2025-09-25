#!/home/user/Monitoring/venv/bin/python

import os
import sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/lib")

from test_http import test_http
from db import set_values

if __name__ == "__main__":
    urls = [
        "https://www.klierlinge.de",
        "https://nextcloud.klierlinge.de",
        "https://mail.klierlinge.de",
        "https://klierlinge.de",
    ]
    for url in urls:
        set_values(test_http(url))
