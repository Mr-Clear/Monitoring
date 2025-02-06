#!/usr/bin/env python

import os
import sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/lib")

import db
from subprocess import check_output, CalledProcessError, PIPE

try:
    check_output(['yay', '-Sy'], stderr=PIPE)
    yay = check_output(['yay', '-Qum'], stderr=PIPE).decode('utf-8')
    packaes = db.DbData('dionysos', 'outdated_packages',  str(yay.count('\n')), yay)
except Exception as e:
    packaes = db.DbData('dionysos', 'outdated_packages',  None, str(e))

db.set_values([packaes])
