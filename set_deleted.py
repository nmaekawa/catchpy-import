#!/usr/bin/env python
import contextlib
import json
import os
import sys


@contextlib.contextmanager
def _smart_open(filename, mode='Ur'):
    if filename == '-':
        if mode is None or mode == '' or 'r' in mode:
            fh = sys.stdin
        else:
            fh = sys.stdout
    else:
        fh = open(filename, mode)

    try:
        yield fh
    finally:
        if filename is not '-':
            fh.close()

def set_deleted(content):

    catcha_list = json.loads(content)

    for c in catcha_list:
        c['platform']['deleted'] = True

    print('{}'.format(json.dumps(catcha_list, indent=4)))


if __name__ == '__main__':
    if len(sys.argv) > 1:
        args = sys.argv[1]
    else:
        args = '-'

    with _smart_open(args) as handle:
        content = handle.read()

    set_deleted(content)


