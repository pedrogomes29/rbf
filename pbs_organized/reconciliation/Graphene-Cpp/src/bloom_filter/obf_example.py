#!/usr/bin/env python3
from open_bloom_filter import BloomFilter
import numpy as np

if __name__ == "__main__":
    entries = 1000000
    fpr = 0.01
    bf = BloomFilter(entries, fpr)
    print("size: %i, k: %i" % (len(bf), bf.num_hashes()))

    print(f"{entries}")
    for i in range(entries):
        bf.add(i)
    for i in range(entries):
        assert i in bf
    cf = 0
    ct = 0
    for i in range(entries, 2 * entries):
        if i in bf:
            cf += 1
        ct += 1
    # print(f'false positives: {cf}')
    print(f"fpr: {100.0 * cf / ct}%")

