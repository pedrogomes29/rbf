import obf
import numpy as np


class BloomFilter:
    def __init__(self, entries, fpr, seed=0):
        self.bf_ptr = obf.new(np.uint32(entries), fpr, np.uint32(seed))

    def __del__(self):
        obf.delete(self.bf_ptr)

    def __contains__(self, key):
        return obf.check(self.bf_ptr, int(key)) == 1

    def add(self, key):
        obf.add(self.bf_ptr, int(key))

    def num_hashes(self):
        return obf.num_hashes(self.bf_ptr)

    def num_bits(self):
        return obf.num_bits(self.bf_ptr)

    def __len__(self):
        return self.num_bits()
