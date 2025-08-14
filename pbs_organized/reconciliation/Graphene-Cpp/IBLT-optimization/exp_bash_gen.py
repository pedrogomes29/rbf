#!/usr/bin/env python3
import numpy as np
import json
import os.path

STARTER_FILE = "../diff_starter.json"
N_TEST = 1000
UNION_SIZE = 100000
EST_FILENAME_PAT = '../../test-sets/diff_estimates_with_tow_{}_128_9012.txt'
INFLATION_RATIO = 1.4

def diff_start_gen():
    if os.path.exists(STARTER_FILE):
        with open(STARTER_FILE, 'r') as fp:
            return json.load(fp)
    diffs = "10 20 30 60 100 200 400 700 1000 1400 2500 4000 8000 10000 16000 30000 50000 100000"
    diff_sizes = [int(s) for s in diffs.split()]
    starter = [0] + list(np.cumsum(diff_sizes)[:-1])
    starter = [int(x) for x in starter]

    j_obj = dict(zip([str(d) for d in diff_sizes], starter))
    with open(STARTER_FILE, 'w') as fp:
        json.dump(j_obj, fp, indent=4)
    return j_obj

def keydigest_cmd(binary, diffs):
    starter = diff_start_gen()
    assert starter is not None
    for d in [int(s) for s in diffs.split()]:
        print(f'echo "./{binary} -n {N_TEST} -d {d} -s {starter[str(d)]} -u {UNION_SIZE} -e {EST_FILENAME_PAT.format(d)}"')
        print(f'./{binary} -n {N_TEST} -d {d} -s {starter[str(d)]} -u {UNION_SIZE} -e {EST_FILENAME_PAT.format(d)}')


if __name__ == '__main__':
    keydigest_cmd('KeyDigest', "10 20 30 60 100 200 400 700 1000 1400 2500 4000 8000 10000")