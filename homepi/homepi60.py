#!/mnt/ssd/home/thomas/Develop/Monitoring/venv/bin/python

import os
import sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/lib")

import db
from subprocess import check_output, CalledProcessError, PIPE

try:
    apt = check_output(['apt', 'list', '--upgradable'], stderr=PIPE).decode('utf-8')
    packaes = db.DbData('hompi', 'outdated_packages',  str(apt.count('\n') - 1), apt)
except Exception as e:
    packaes = db.DbData('hompi', 'outdated_packages',  None, str(e))

db.set_values([packaes])
