#!/usr/bin/env python

import os
import sys
parent_dir_name = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.append(parent_dir_name + "/lib")

import db
from subprocess import run, CalledProcessError, PIPE

try:
    yay = run(['yay', '-Qum'], stdout=PIPE, stderr=PIPE)
    out = yay.stdout.decode('utf-8')
    packaes = db.DbData('dionysos', 'outdated_packages', str(out.count('\n')), out)

except Exception as e:
    packaes = db.DbData('dionysos', 'outdated_packages',  None, str(e))

db.set_values([packaes])
