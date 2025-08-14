import json
import sys
import random
import numpy as np
from math import ceil, exp, log, sqrt
from pybloom_live import BloomFilter
# sys.path.append('.')
import os.path
from datetime import datetime

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(CURRENT_PATH)
# PYBLT_PATH = '/home/pinar/IBLT-optimization/'
# sys.path.append(PYBLT_PATH)
PYBLT_PATH = os.path.join(os.path.dirname(CURRENT_PATH), 'IBLT-optimization')
# sys.path.append(PYBLT_PATH)
sys.path.append(PYBLT_PATH)
from pyblt import PYBLT
from search_params import search_params

PYBLT.set_parameter_filename(
    PYBLT_PATH + '/param.export.0.995833.2018-07-17.csv')

# Constants
# PATH = '.'
PATH = os.path.dirname(CURRENT_PATH)  # '.'
TXN_SHORT_BYTES_CB = 6
TXN_SHORT_BYTES = 4  # 8
# number of bytes per transaction, converted to bits per transaction
BITSIZE = TXN_SHORT_BYTES * 8
TAU = 12  # bytes per IBLT cell

TEST_SETS = "../../test-sets/sets_100000_1000_32_1574465740.txt"

DIFF_STARTS = json.load(open("../../test-sets/diff_starter.json", 'r'))

# SET_FD = open(TEST_SETS, 'r')
# for _ in range(3):
#     SET_FD.readline()

BLK_SIZE = [200, 2000, 10000]  # num of txns in block
#DIFF_SIZES = [int(d) for d in "10 20 30 60 100 200 400 700 1000 1400 2500 4000 8000 10000".split()]
# DIFF_SIZES = [int(d) for d in "1400 2500 4000 8000 10000".split()]
DIFF_SIZES = [1000]
# BLK_SIZE = [200]
B = [1 / 240]
# FRACTION = np.arange(1, 0, -0.05)
# FRACTION = [1.0-0.5e-1]
FRACTION = [1.0]
NUM_TRIAL = 1000
UNION_SIZE = 100000


def create_mempools(mempool_size, fraction, blk_size, num_doesnt_have):
    # create a random set of transactions in a mempool
    blk = [random.getrandbits(BITSIZE) for x in range(blk_size)]
    num_has = int(blk_size * fraction)  # fraction of txns receiver has
    # print('num has', num_has)
    in_blk = random.sample(blk, num_has)
    # num_doesnt_have = mempool_size - num_has # rest of txns in mempool
    in_mempool = [random.getrandbits(BITSIZE) for x in range(num_doesnt_have)]
    receiver_mempool = in_blk + in_mempool
    return blk, receiver_mempool


# def create_mempools_v2(mempool_size, fraction, blk_size, num_doesnt_have):
#     global SET_FD
#     # create a random set of transactions in a mempool
#     blk = [random.getrandbits(BITSIZE) for x in range(blk_size)]
#     num_has = int(blk_size * fraction)  # fraction of txns receiver has
#     with open(TEST_SETS, 'r') as fp:
#         for _ in range(3):
#             fp.readline()

#     # print('num has', num_has)
#     in_blk = random.sample(blk, num_has)
#     # num_doesnt_have = mempool_size - num_has # rest of txns in mempool
#     in_mempool = [random.getrandbits(BITSIZE) for x in range(num_doesnt_have)]
#     receiver_mempool = in_blk + in_mempool
#     return blk, receiver_mempool

# Check whether bk was reconstructed properly
def decode_blk(result, passed, blk):
    not_in_blk = set()
    t_s = datetime.now()
    in_blk = set()
    for key in result:
        if result[key][1] == 1:
            not_in_blk.add(key)
        elif result[key][1] == -1:
            in_blk.add(key)
    t_e = datetime.now()
    t_decoding = (t_e - t_s).microseconds

    possibly_in_blk = set(passed)
    possibly_in_blk.difference_update(not_in_blk)
    reconstructed_blk = list(in_blk.union(possibly_in_blk))
    flag = set(reconstructed_blk) == set(blk)
    return flag, in_blk, t_decoding


def try_ping_pong(first_IBLT, second_IBLT, in_blk, not_in_blk):
    flag = False
    first_boolean, result = second_IBLT.list_entries()
    if len(result) == 0:
        second_boolean, result = first_IBLT.list_entries()
        flag = True
    if len(result) == 0:  # both results are zero
        if first_boolean == True and second_boolean == True:
            return True, in_blk, not_in_blk
        else:
            return False, in_blk, not_in_blk
    for key in result:
        if result[key][1] == 1:
            not_in_blk.add(key)
            second_IBLT.erase(key, 0x0)
            first_IBLT.erase(key, 0x0)
        elif result[key][1] == -1:
            in_blk.add(key)
            second_IBLT.insert(key, 0x0)
            first_IBLT.insert(key, 0x0)
    if flag == True:
        return try_ping_pong(first_IBLT, second_IBLT, in_blk, not_in_blk)
    else:
        return try_ping_pong(second_IBLT, first_IBLT, in_blk, not_in_blk)


def trial(fd):
    params = search_params()
    for diff_size in DIFF_SIZES:
        true_false_positives = diff_size

        o_fp = open(f'{UNION_SIZE}_{diff_size}_0_Graphene.txt', 'w')
        o_fp.write('#tid,round,transmitted_bytes,succeed,encoding_time,decoding_time,ibt_ratio,scaling_ratio\n')

        set_fd = open(TEST_SETS, 'r')
        for _ in range(3):
            set_fd.readline()
        for bound in B:
            for fraction in FRACTION:

                # True_positives is the number of txns in the blk the receiver has
                true_positives = UNION_SIZE - \
                                 true_false_positives  # int(blk_size * fraction)
                mempool_size = true_false_positives + true_positives

                print(
                    'Running %d trials for parameter combination: extra txns in mempool %d diff size %d fraction %f' % (
                        NUM_TRIAL, true_false_positives, diff_size, fraction))

                # Size of Compact block (inv + getdata)
                # getdata = (1 - fraction) * blk_size * TXN_SHORT_BYTES_CB
                # inv = blk_size * TXN_SHORT_BYTES_CB
                # compact = inv + getdata
                compact = 0

                for i in range(NUM_TRIAL):
                    elemements = [int(e) for e in set_fd.readline().split()]
                    # blk, receiver_mempool = create_mempools(mempool_size, fraction, blk_size, true_false_positives)
                    blk = [elemements[i] for i in range(0, DIFF_STARTS[str(diff_size)])] + [elemements[i] for i in
                                                                                            range(DIFF_STARTS[str(
                                                                                                diff_size)] + diff_size,
                                                                                                  UNION_SIZE)]
                    receiver_mempool = [e for e in elemements]
                    diffs = set([elemements[i] for i in
                                 range(DIFF_STARTS[str(diff_size)], DIFF_STARTS[str(diff_size)] + diff_size)])
                    blk_size = len(blk)
                    # Sender creates BF of blk

                    t_s = datetime.now()
                    a, fpr_sender, iblt_rows_first = params.solve_a(
                        mempool_size, blk_size, blk_size, 0)
                    bloom_sender = BloomFilter(blk_size, fpr_sender)
                    tmp = blk_size + 0.5
                    exponent = (-bloom_sender.num_slices * tmp) / (bloom_sender.num_bits - 1)
                    real_fpr_sender = (1 - exp(exponent)
                                       ) ** bloom_sender.num_slices
                    # exponent = (-bloom_sender.num_slices*blk_size) / bloom_sender.num_bits
                    # tmp = (1-exp(exponent)) ** bloom_sender.num_slices
                    # real_fpr_sender = max(tmp, fpr_sender)
                    # assert real_fpr_sender >= fpr_sender

                    # Sender creates IBLT of blk
                    a_old = a
                    # CHANGED: here we re-calculate `a` based on `real_fpr_sender`
                    a = real_fpr_sender * (mempool_size - blk_size)
                    beta = 239 / 240
                    s = - log(1.0 - beta) / a 
                    # Using Chernoff Bound
                    delta = 0.5 * (s + sqrt(s + sqrt(s**2 + 8.0*s)))
                    a_star = (1 + delta) * a 
                    a = ceil(a_star)
                    iblt_rows_first_old = iblt_rows_first

                    
                    if a - 1 >= 1000:
                        iblt_rows_first = ceil(1.362549 * a)
                    else:
                        iblt_rows_first = params.params[a - 1][3]

                    iblt_sender_first = PYBLT(a, TXN_SHORT_BYTES)

                    # Add to BF and IBLT
                    for txn in blk:
                        bloom_sender.add(txn)
                        iblt_sender_first.insert(txn, 0x0)

                    # Receiver computes how many items pass through BF of sender and creates IBLT
                    iblt_receiver_first = PYBLT(a, TXN_SHORT_BYTES)
                    Z = []
                    for txn in receiver_mempool:
                        if txn in bloom_sender:
                            Z.append(txn)
                            iblt_receiver_first.insert(
                                txn, 0x0)  # (id and content)

                    t_e = datetime.now()
                    t_encoding = (t_e - t_s).microseconds

                    t_s = datetime.now()
                    z = len(Z)
                    observed_false_positives = z - true_positives

                    # Eppstein subtraction
                    T = iblt_receiver_first.subtract(iblt_sender_first)
                    boolean, result = T.list_entries()

                    t_e = datetime.now()
                    t_decoding = (t_e - t_s).microseconds

                    # assert boolean == False

                    # Check whether decoding successful
                    if boolean:

                        flag, in_blk, decoding_time = decode_blk(result, Z, blk)
                        t_decoding += decoding_time

                        # Each component of graphene blk size
                        first_IBLT = (iblt_rows_first * TAU)
                        first_BF = (bloom_sender.num_bits / 8.0)
                        extra = (len(in_blk) * TXN_SHORT_BYTES)

                        # Compute size of Graphene block
                        graphene = first_IBLT + first_BF + extra

                        # '#tid,round,transmitted_bytes,succeed,encoding_time,decoding_time,num_recovered,num_cells,num_hashes,first_BF,first_BF_fpr,first_IBLT,second_BF,second_BF_fpr,secondIBLT\n'
                        o_fp.write(
                            f"{i + 1},1,{graphene},{int(flag)},{t_encoding},{t_decoding},{first_IBLT/graphene},{(first_IBLT + extra)/graphene}\n"
                        )
                        # print(str(true_false_positives) + '\t' + str(blk_size) + '\t' + str(bound) + '\t' + str(
                        #     fraction) + '\t' + str(mempool_size) + '\t' + str(fpr_sender) + '\t' + str(
                        #     real_fpr_sender) + '\t' + str(0) + '\t' + str(a) + '\t' + str(0) + '\t' + str(
                        #     0) + '\t' + str(0) + '\t' + str(z) + '\t' + str(0) + '\t' + str(
                        #     observed_false_positives) + '\t' + str(boolean and flag) + '\t' + str(False) + '\t' + str(
                        #     graphene) + '\t' + str(first_IBLT) + '\t' + str(first_BF) + '\t' + str(0) + '\t' + str(
                        #     0) + '\t' + str(extra) + '\t' + str(iblt_rows_first) + '\t' + str(0) + '\t' + str(
                        #     compact))
                        fd.write(str(true_false_positives) + '\t' + str(blk_size) + '\t' + str(bound) + '\t' + str(
                            fraction) + '\t' + str(mempool_size) + '\t' + str(fpr_sender) + '\t' + str(
                            real_fpr_sender) + '\t' + str(0) + '\t' + str(a) + '\t' + str(0) + '\t' + str(
                            0) + '\t' + str(0) + '\t' + str(z) + '\t' + str(0) + '\t' + str(
                            observed_false_positives) + '\t' + str(boolean and flag) + '\t' + str(False) + '\t' + str(
                            graphene) + '\t' + str(first_IBLT) + '\t' + str(first_BF) + '\t' + str(0) + '\t' + str(
                            0) + '\t' + str(extra) + '\t' + str(iblt_rows_first) + '\t' + str(0) + '\t' + str(
                            compact) + '\t' + str(a_old) + '\t' + str(iblt_rows_first_old) + '\n')
                    else:
                        # Each component of graphene blk size
                        first_IBLT = (iblt_rows_first * TAU)
                        first_BF = (bloom_sender.num_bits / 8.0)
                        extra = 0

                        # Compute size of Graphene block
                        graphene = first_IBLT + first_BF + extra

                        # '#tid,round,transmitted_bytes,succeed,encoding_time,decoding_time,num_recovered,num_cells,num_hashes,first_BF,first_BF_fpr,first_IBLT,second_BF,second_BF_fpr,secondIBLT\n'
                        o_fp.write(
                            f"{i + 1},1,{graphene},0,{t_encoding},{t_decoding},{first_IBLT/graphene},{(first_IBLT + extra)/graphene}\n"
                        )
                        flag = False
                        # print(str(true_false_positives) + '\t' + str(blk_size) + '\t' + str(bound) + '\t' + str(
                        #     fraction) + '\t' + str(mempool_size) + '\t' + str(fpr_sender) + '\t' + str(
                        #     real_fpr_sender) + '\t' + str(0) + '\t' + str(a) + '\t' + str(0) + '\t' + str(
                        #     0) + '\t' + str(0) + '\t' + str(z) + '\t' + str(0) + '\t' + str(
                        #     observed_false_positives) + '\t' + str(boolean and flag) + '\t' + str(False) + '\t' + str(
                        #     graphene) + '\t' + str(first_IBLT) + '\t' + str(first_BF) + '\t' + str(0) + '\t' + str(
                        #     0) + '\t' + str(extra) + '\t' + str(iblt_rows_first) + '\t' + str(0) + '\t' + str(
                        #     compact))
                        fd.write(str(true_false_positives) + '\t' + str(blk_size) + '\t' + str(bound) + '\t' + str(
                            fraction) + '\t' + str(mempool_size) + '\t' + str(fpr_sender) + '\t' + str(
                            real_fpr_sender) + '\t' + str(0) + '\t' + str(a) + '\t' + str(0) + '\t' + str(
                            0) + '\t' + str(0) + '\t' + str(z) + '\t' + str(0) + '\t' + str(
                            observed_false_positives) + '\t' + str(boolean and flag) + '\t' + str(False) + '\t' + str(
                            graphene) + '\t' + str(first_IBLT) + '\t' + str(first_BF) + '\t' + str(0) + '\t' + str(
                            0) + '\t' + str(extra) + '\t' + str(iblt_rows_first) + '\t' + str(0) + '\t' + str(
                            compact) + '\t' + str(a_old) + '\t' + str(iblt_rows_first_old) +'\n')
                        # o_fp.write(
                        #     f"{i + 1},1,0,0,{t_encoding},{t_decoding}\n"
                        # )
                        #
                        # # Receiver creates BF of txns that passed through sender's BF
                        # # print('z', z)
                        # # print('bound', bound)
                        #
                        # t_s = datetime.now()
                        # x_star = params.search_x_star(
                        #     z, mempool_size, real_fpr_sender, bound, blk_size)
                        # temp = (mempool_size - x_star) * real_fpr_sender
                        # y_star = params.CB_bound(temp, real_fpr_sender, bound)
                        # # print('y_star', y_star)
                        # y_star = ceil(y_star)
                        # b, fpr_receiver, iblt_rows_second = params.solve_a(
                        #     blk_size, z, x_star, y_star)
                        #
                        # bloom_receiver = BloomFilter(z, fpr_receiver)
                        # for txn in Z:
                        #     bloom_receiver.add(txn)
                        #
                        # # Receiver determines IBLT size
                        # iblt_sender_second = PYBLT(b + y_star, TXN_SHORT_BYTES)
                        # # Sender creates IBLT of blk again and sends txns that do not pass through BF of receiver
                        # count = 0
                        # for txn in blk:
                        #     iblt_sender_second.insert(txn, 0x0)
                        # if txn not in bloom_receiver:
                        #     # add txns just received to subtracted IBLT
                        #     T.insert(txn, 0x0)
                        # Z = Z + [txn]  # sends the txn to the receiver
                        # count = count + 1
                        #
                        # iblt_receiver_second = PYBLT(b + y_star, TXN_SHORT_BYTES)
                        # for txn in Z:
                        #     iblt_receiver_second.insert(txn, 0x0)
                        #
                        # t_e = datetime.now()
                        # t_encoding = (t_e - t_s).microseconds
                        #
                        # # Eppstein subtraction
                        # t_s = datetime.now()
                        # T_second = iblt_receiver_second.subtract(
                        #     iblt_sender_second)
                        # boolean, result = T_second.list_entries()
                        # t_e = datetime.now()
                        # t_decoding = (t_e - t_s).microseconds
                        # # print(boolean)
                        # # print('Z', z)
                        #
                        # # Check whether blk was reconstructed properly
                        # flag, in_blk, decoding_time = decode_blk(result, Z, blk)
                        #
                        # t_decoding += decoding_time
                        #
                        # final = False
                        # if boolean == False or flag == False:
                        #     t_s = datetime.now()
                        #     final, in_blk, not_in_blk = try_ping_pong(
                        #         T, T_second, set(), set())
                        #     t_decoding += (t_e - t_s).microseconds
                        #     # print('Ping pong result', final)
                        #     if final:
                        #         possibly_in_blk = set(Z)
                        #         possibly_in_blk.difference_update(not_in_blk)
                        #         reconstructed_blk = list(
                        #             in_blk.union(possibly_in_blk))
                        #         assert set(reconstructed_blk) == set(blk)
                        #
                        # # Each component of graphene blk size
                        # first_IBLT = (iblt_rows_first * TAU)
                        # first_BF = (bloom_sender.num_bits / 8.0)
                        # second_IBLT = (iblt_rows_second * TAU)
                        # second_BF = (bloom_receiver.num_bits / 8.0)
                        # extra = (len(in_blk) * TXN_SHORT_BYTES)
                        # # Compute size of Graphene block
                        # graphene = first_IBLT + first_BF + second_IBLT + second_BF + extra
                        #
                        # o_fp.write(
                        #     f"{i + 1},2,{graphene},{(boolean and flag) or (final)},{t_encoding},{t_decoding}\n"
                        # )
                        #
                        # print(str(true_false_positives) + '\t' + str(blk_size) + '\t' + str(bound) + '\t' + str(
                        #     fraction) + '\t' + str(mempool_size) + '\t' + str(fpr_sender) + '\t' + str(
                        #     real_fpr_sender) + '\t' + str(fpr_receiver) + '\t' + str(a) + '\t' + str(b) + '\t' + str(
                        #     x_star) + '\t' + str(y_star) + '\t' + str(z) + '\t' + str(count) + '\t' + str(
                        #     observed_false_positives) + '\t' + str(boolean and flag) + '\t' + str(final) + '\t' + str(
                        #     graphene) + '\t' + str(first_IBLT) + '\t' + str(first_BF) + '\t' + str(
                        #     second_IBLT) + '\t' + str(second_BF) + '\t' + str(extra) + '\t' + str(
                        #     iblt_rows_first) + '\t' + str(iblt_rows_second) + '\t' + str(compact))
                        # fd.write(str(true_false_positives) + '\t' + str(blk_size) + '\t' + str(bound) + '\t' + str(
                        #     fraction) + '\t' + str(mempool_size) + '\t' + str(fpr_sender) + '\t' + str(
                        #     real_fpr_sender) + '\t' + str(fpr_receiver) + '\t' + str(a) + '\t' + str(b) + '\t' + str(
                        #     x_star) + '\t' + str(y_star) + '\t' + str(z) + '\t' + str(count) + '\t' + str(
                        #     observed_false_positives) + '\t' + str(boolean and flag) + '\t' + str(final) + '\t' + str(
                        #     graphene) + '\t' + str(first_IBLT) + '\t' + str(first_BF) + '\t' + str(
                        #     second_IBLT) + '\t' + str(second_BF) + '\t' + str(extra) + '\t' + str(
                        #     iblt_rows_first) + '\t' + str(iblt_rows_second) + '\t' + str(compact) + '\n')

                    fd.flush()
        o_fp.close()
        set_fd.close()


def main():
    fd = open(PATH + '/results/protocol-I-CB-%d.csv' %
              (random.getrandbits(25)), 'w')
    trial(fd)
    fd.close()


if __name__ == "__main__":
    main()
