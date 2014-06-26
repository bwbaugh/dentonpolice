# -*- coding: utf-8 -*-
"""Convert the inmate logs from Python to JSON representation."""
import ast
import sys

from dentonpolice.inmate import Inmate


for line in sys.stdin:
    data = ast.literal_eval(line)
    data.pop('posted', None)
    inmate = Inmate(**data)
    sys.stdout.write(inmate.to_json() + '\n')
