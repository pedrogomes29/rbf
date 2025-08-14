#!/usr/bin/env python3
import numpy as np
import json
import os.path

STARTER_FILE = "../reconciliation/test-sets/diff_starter.json"


def diff_start_gen():
    if os.path.exists(STARTER_FILE):
        with open(STARTER_FILE, "r") as fp:
            return json.load(fp)
    return None
    # diffs = "10 20 30 60 100 200 400 700 1000 1400 2500 4000 8000 10000 16000 30000 50000 100000"
    # diff_sizes = [int(s) for s in diffs.split()]
    # starter = [0] + list(np.cumsum(diff_sizes)[:-1])
    # starter = [int(x) for x in starter]
    #
    # j_obj = dict(zip([str(d) for d in diff_sizes], starter))
    # with open(STARTER_FILE, 'w') as fp:
    #     json.dump(j_obj, fp, indent=4)
    # return j_obj


def tow_estimator_cmd(binary, diffs, num_sketch, seed):
    starter = diff_start_gen()
    assert starter is not None
    for d in [int(s) for s in diffs.split()]:
        print(
            f'echo "./{binary} -d {d} -s {starter[str(d)]} -n {num_sketch} -S {seed}"'
        )
        print(f"./{binary} -d {d} -s {starter[str(d)]} -n {num_sketch} -S {seed}")

if __name__ == "__main__":
    tow_estimator_cmd(
        "tow_estimator",
        "10 20 30 60 100 200 400 700 1000 1400 2500 4000 8000 10000",
        256,
        9012,
    )

