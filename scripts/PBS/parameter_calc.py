#!/usr/bin/env python3
import numpy as np

TARGET_FAILURE_RATE = 1/3000
TARGET_SUCCESS_RATE = 1 - TARGET_FAILURE_RATE
AVG_DIFF = 5
MAX_ROUND = 3
SPLIT_NUM = 3
INF_RATIO = 1.38


balls_into_bins_dict = {}
transition_dict = {}
round_table_dict = {}


def calc_balls_into_bins(n_bins, n_balls):
    # result[i, j, k] is the probability of putting i balls into n_bins bins causing j bins are empty and k bins have exactly 1 ball
    result = np.zeros((n_balls + 1, n_bins + 1, n_balls + 2))
    result[0, n_bins, 0] = 1
    result[1, n_bins - 1, 1] = 1
    for i in range(2, n_balls + 1):
        for j in range(n_bins - i, n_bins):
            for k in range(0, n_bins + 1 - j):
                result[i, j, k] = (
                    result[i - 1, j + 1, k - 1] * (j + 1) / n_bins
                    + result[i - 1, j, k + 1] * (k + 1) / n_bins
                    + result[i - 1, j, k] * (n_bins - j - k) / n_bins
                )
    return result


def get_balls_into_bins(n_bins, n_balls):
    if (n_bins, n_balls) not in balls_into_bins_dict:
        balls_into_bins_dict[(n_bins, n_balls)] = calc_balls_into_bins(n_bins, n_balls)
    return balls_into_bins_dict[(n_bins, n_balls)]


def calc_transition(balls_into_bins, max_decode_size):
    n_balls = balls_into_bins.shape[0] - 1
    n_bins = balls_into_bins.shape[1] - 1
    result = np.zeros((n_balls + 1, n_balls + 1))
    for i in range(0, n_balls + 1):
        for j in range(0, i + 1):
            result[i, j] = np.sum(
                balls_into_bins[i, n_bins - max_decode_size : n_bins + 1, i - j]
            )
    for i in range(max_decode_size + 1, n_balls + 1):
        result[i, i] = 1 - np.sum(result[i, 0:i])
    return result


def get_transition(n_bins, n_balls, max_decode_size):
    balls_into_bins = get_balls_into_bins(n_bins, n_balls)
    n_bins = balls_into_bins.shape[1] - 1
    n_balls = balls_into_bins.shape[0] - 1
    if (n_bins, n_balls, max_decode_size) not in transition_dict:
        transition_dict[(n_bins, n_balls, max_decode_size)] = calc_transition(
            balls_into_bins, max_decode_size
        )
    return transition_dict[(n_bins, n_balls, max_decode_size)]


def calc_round(n_bins, n_balls, max_decode_size, max_round):
    transition = get_transition(n_bins, n_balls, max_decode_size)
    result = np.zeros((n_balls + 1, max_round + 1))
    iter = transition
    for r in range(1, max_round + 1):
        result[:, r] = 1 - iter[:, 0]
        iter = np.matmul(iter, transition)
    result[:, 0] = 1
    return result


def get_round(n_bins, n_balls, max_decode_size, max_round):
    if (n_bins, n_balls, max_decode_size, max_round) not in round_table_dict:
        round_table_dict[(n_bins, n_balls, max_decode_size, max_round)] = calc_round(
            n_bins, n_balls, max_decode_size, max_round
        )
    return round_table_dict[(n_bins, n_balls, max_decode_size, max_round)]


def calc_prob_fail_upperbound_no_split(
    total_balls, n_groups, n_bins, max_round, split_num, max_decode_size, round_table
):
    prob = (1 - 1 / n_groups) ** total_balls
    prob_fail = 0
    prob_tail = 1 - prob
    for n_balls in range(1, max_decode_size):
        prob = prob * (total_balls - n_balls + 1) / n_balls / (n_groups - 1)
        prob_fail += prob * round_table[n_balls + 1, max_round]
        prob_tail -= prob
    prob_fail += prob_tail
    prob_fail_upperbound = 2 * (1 - (1 - prob_fail) ** n_groups)
    return prob_fail_upperbound


def calc_prob_fail_upperbound(
    total_balls, n_groups, n_bins, max_round, split_num, max_decode_size, round_table
):
    m = min(200, n_bins - 1)
    prob = (1 - 1 / n_groups) ** total_balls
    prob_fail = 0
    prob_tail = 1 - prob
    for n_balls in range(1, max_decode_size):
        prob = prob * (total_balls - n_balls + 1) / n_balls / (n_groups - 1)
        prob_fail += prob * round_table[n_balls + 1, max_round]
        prob_tail -= prob
    for n_balls in range(max_decode_size, m):
        prob = prob * (total_balls - n_balls + 1) / n_balls / (n_groups - 1)
        prob_fail += prob * calc_prob_fail_upperbound_no_split(
            n_balls,
            split_num,
            n_bins,
            max_round - 1,
            split_num,
            max_decode_size,
            round_table,
        )
        prob_tail -= prob

    prob_fail += prob_tail
    if prob_fail >= 1:
        return 1.0
    prob_fail_upperbound = 2 * (1 - (1 - prob_fail) ** n_groups)
    if prob_fail_upperbound >= 1:
        return 1.0
    return prob_fail_upperbound


def get_best_param(diff, avg_diff, max_round, split_num, success_rate):
    min_cost = 1e10
    opt_n = 1
    opt_t = 1
    opt_prob = -1
    for n in range(6, 15):
        t = n
        n_bins = 2 ** n - 1
        m = min(200, n_bins - 1)
        prob = 0
        while prob < success_rate and t < min([200, n_bins - 1, 5 * avg_diff]):
            t += 1
            round_table = get_round(n_bins, m, t, max_round)
            prob = 1 - calc_prob_fail_upperbound(
                diff,
                diff / avg_diff,
                n_bins,
                max_round,
                split_num,
                t,
                round_table,
            )
        if t < min([200, n_bins - 1, 5 * avg_diff]):
            cost = n * t
            if cost < min_cost:
                min_cost = cost
                opt_n = n
                opt_t = t
                opt_prob = prob
    return opt_prob, opt_n, opt_t