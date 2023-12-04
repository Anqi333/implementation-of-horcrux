import networkx as nx
import numpy as np
import random
import collections

within_data = {}
inter_data = {}
all_inter_data = {}
G = None
tx_8 = []

network_file = './network/lightning_simplified_component.edgelist'
payment_value_file = './payment_value/payment_value_satoshi_03.csv'

payment_value_threshold = 466359
tx_load = 50000
repeat = 10


def tuple_sort(a):
    return tuple(sorted(a))


def tuple_trans(a, b):
    a = set(a)  # (0,1)
    b = set(b)  # (0,3)
    common = list(a & b)[0]  # (0,)
    other = list(a ^ b)  # (1,3)
    return (common, min(other), max(other))


def get_within(Alice, Bob):

    # get the balance allocation within channel (Alice, Bob)
    # return (Alice's balance, Bob's balance)

    global within_data

    zchannel = tuple_sort((Alice, Bob))
    if zchannel[0] == Alice:
        return within_data[zchannel]
    elif zchannel[0] == Bob:
        return within_data[zchannel][::-1]


def get_total_amount(Alice):

    # get Alice's total balances in all her channels

    global G

    amt = 0
    for neighbor in G[Alice]:
        amt += get_within(Alice, neighbor)[0]
    return amt


def update_within(Alice, Bob, bal_A, bal_B):

    # for channel (Alice, Bob), update Alice's balance to bal_A and Bob's balance to bal_B

    global within_data

    zchannel = tuple_sort((Alice, Bob))
    if zchannel[0] == Alice:
        within_data[zchannel] = (bal_A, bal_B)
    elif zchannel[0] == Bob:
        within_data[zchannel] = (bal_B, bal_A)
    if bal_A < 0 or bal_B < 0:
        print('wrong channel update')


def initialize(channel_rate, seed):
    global G
    global tx_8
    G = nx.Graph()
    tx_8 = []

    global within_data
    global inter_data
    global all_inter_data
    within_data = {}
    inter_data = {}
    all_inter_data = {}

    random.seed(seed)
    np.random.seed(seed)

    with open(network_file, "r") as f:
        for line in f:
            tmp = line.split()
            nodeA = int(tmp[0])
            nodeB = int(tmp[1])
            capacity = int(int(tmp[2]) * channel_rate)
            G.add_edge(nodeA, nodeB)
            capacity += capacity % 2
            bal_A = capacity // 2
            bal_B = capacity // 2

            if(nodeA < nodeB):
                within_data[((nodeA, nodeB))] = (bal_A, bal_B)
            else:
                within_data[((nodeB, nodeA))] = (bal_B, bal_A)

    with open(payment_value_file, "r") as f:
        for line in f:
            tmp = int(float(line))

            if payment_value_threshold == None:
                if 0 < tmp:
                    tx_8.append(tmp)
            else:
                if 0 < tmp <= payment_value_threshold:
                    tx_8.append(tmp)
    # print('the number of payments:', len(tx_8))
    random.shuffle(tx_8)
    # print('the size of network:', G.size())


def work(method, seed, channel_rate, mode, skew_param):

    initialize(channel_rate, seed)
    znode = list(G.nodes())

    total_tx_number = 0
    success_tx_number = 0
    total_tx_amount = 0
    success_tx_amount = 0

    # select a path
    for i in range(tx_load):
        if mode == "uniform":
            while True:
                t1 = random.choice(znode)
                t2 = random.choice(znode)
                if t1 != t2:
                    break
        else:
            while True:
                t1 = len(znode)
                while t1 >= len(znode):
                    t1 = int(np.random.exponential(len(znode)/skew_param))
                t2 = random.choice(znode)
                if t1 != t2:
                    break

        path = nx.shortest_path(G, source=t1, target=t2)
        amt = tx_8[i]

        flag = True

        for j in range(len(path) - 1):
            z_r = get_within(path[j], path[j + 1])[0]
            if z_r >= amt:
                continue
            elif j > 0:
                z_l = get_within(path[j - 1], path[j])[1]
                if z_l + z_r >= amt:
                    continue
                else:
                    flag = False
                    break
            else:
                flag = False
                break

        if flag:
            success_tx_number += 1
            success_tx_amount += amt

            # perform the payment
            for j in range(len(path) - 1):
                z0 = get_within(path[j], path[j + 1])[0]
                z1 = get_within(path[j], path[j + 1])[1]
                if j == 0 and z0 >= amt:
                    update_within(path[j], path[j + 1], z0 - amt, z1 + amt)
                    continue
                else:
                    z0_l = get_within(path[j - 1], path[j])[0]
                    z1_l = get_within(path[j - 1], path[j])[1]
                    if z1_l - amt >= amt:
                        update_within(path[j - 1], path[j], z0_l, z1_l - amt)
                        update_within(path[j], path[j + 1], z0, z1 + amt)  # shift coins
                    else:
                        update_within(path[j - 1], path[j], z0_l, amt)
                        update_within(path[j], path[j + 1], z1_l + z0 - 2*amt, z1 + amt)  # shift coins

        total_tx_number += 1
        total_tx_amount += amt
    total_channel_depletion_number = network_test()
    return success_tx_number/total_tx_number, success_tx_amount, total_tx_amount, total_channel_depletion_number


def network_test():
    znode = list(G.nodes())

    total_dry_channel_number = 0
    for node in znode:
        for neighbor in G[node]:
            z0 = get_within(node, neighbor)[0]
            z1 = get_within(node, neighbor)[1]
            if z0 == 0 and z1 != 0:
                total_dry_channel_number += 1
    # result = total_dry_channel_number / G.size()
    return total_dry_channel_number


def uniform_capacity(capacity, method):
    results = []
    for s in range(repeat):
        cur_res = work(method=method, seed=s,
                       channel_rate=capacity, mode='uniform', skew_param=None)
        results.append((cur_res))
        print(cur_res)
    ave_result = [0] * len(results[0])
    for i in range(len(results)):
        for j in range(len(results[0])):
            ave_result[j] += (results[i][j] / len(results))

    print('average success ratio:', ave_result[0])
    print('average success volume:', ave_result[1])
    print('average total volume:', ave_result[2])
    print('average depleted channel number:', ave_result[3])


def test_uniform_capacity(capacity: object):
    print('performance under uniform payments, varying the channel capacity:')

    for obj in capacity:
        print('capacity factor:', obj)
        print('Capybara result:')
        uniform_capacity(method="Capybara", capacity=obj)


def multi_work(method, mode, skew_param):
    znode = list(G.nodes())

    total_tx_number = 0
    success_tx_number = 0
    total_tx_amount = 0
    success_tx_amount = 0

    # select a path
    for i in range(tx_load):
        if mode == "uniform":
            while True:
                t1 = random.choice(znode)
                t2 = random.choice(znode)
                if t1 != t2:
                    break
        else:
            while True:
                t1 = len(znode)
                while t1 >= len(znode):
                    t1 = int(np.random.exponential(len(znode)/skew_param))
                t2 = random.choice(znode)
                if t1 != t2:
                    break

        path = nx.shortest_path(G, source=t1, target=t2)
        amt = tx_8[i]

        flag = True

        for j in range(len(path) - 1):
            z_r = get_within(path[j], path[j + 1])[0]
            if z_r >= amt:
                continue
            elif j > 0:
                z_l = get_within(path[j - 1], path[j])[1]
                if z_l + z_r >= amt:
                    continue
                else:
                    flag = False
                    break
            else:
                flag = False
                break

        if flag:
            success_tx_number += 1
            success_tx_amount += amt

            # perform the payment
            for j in range(len(path) - 1):
                z0 = get_within(path[j], path[j + 1])[0]
                z1 = get_within(path[j], path[j + 1])[1]
                if j == 0 and z0 >= amt:
                    update_within(path[j], path[j + 1], z0 - amt, z1 + amt)
                    continue
                else:
                    z0_l = get_within(path[j - 1], path[j])[0]
                    z1_l = get_within(path[j - 1], path[j])[1]
                    if z1_l - amt >= amt:
                        update_within(path[j - 1], path[j], z0_l, z1_l - amt)
                        update_within(path[j], path[j + 1], z0, z1 + amt)  # shift coins
                    else:
                        update_within(path[j - 1], path[j], z0_l, amt)
                        update_within(path[j], path[j + 1], z1_l + z0 - 2*amt, z1 + amt)  # shift coins

        total_tx_number += 1
        total_tx_amount += amt
    total_channel_depletion_number = network_test()
    return success_tx_number/total_tx_number, success_tx_amount, total_tx_amount, total_channel_depletion_number


def multi_uniform_capacity(capacity, method):
    results = []
    repeat_time = 20

    for i in range(repeat):
        seed = i
        initialize(channel_rate=capacity, seed=seed)
        for s in range(repeat_time):
            cur_res = multi_work(method=method, skew_param=None, mode='uniform')
            if s >= repeat_time - 1:
                results.append((cur_res))
                print(cur_res)

    # seed = random.randint(1, repeat_time)
    # initialize(channel_rate=capacity, seed=seed)
    # for s in range(repeat_time):
    #     cur_res = multi_work(method=method, mode='uniform', skew_param=None)
    #     results.append((cur_res))
    #     print(cur_res)

    ave_result = [0] * len(results[0])
    max_depleted_channel_number = 0
    for i in range(len(results)):
        for j in range(len(results[0])):
            ave_result[j] += (results[i][j] / len(results))
        # if max_depleted_channel_number < results[i][3]:
        #     max_depleted_channel_number = results[i][3]
    print('average success ratio:', ave_result[0])
    print('average success volume:', ave_result[1])
    print('average total volume:', ave_result[2])
    print('ave depleted channel number:', ave_result[3])


def test_multi_uniform(capacity):
    print('multi_test performance under uniform payments, varying the depleted channel number:')

    # print('Capybara result for running 200 times with capacity 8:')
    # multi_uniform_capacity(method="Capybara", capacity=8)

    for obj in capacity:
        print('capacity factor:', obj)
        print('Capybara result:')
        multi_uniform_capacity(method="Capybara", capacity=obj)


def skew(skew_param, method):
    results = []
    for s in range(repeat):
        cur_res = work(method=method, seed=s,
                       skew_param=skew_param, channel_rate=10, mode='skew')
        results.append((cur_res))
        print(cur_res)
    ave_result = [0] * len(results[0])
    for i in range(len(results)):
        for j in range(len(results[0])):
            ave_result[j] += (results[i][j] / len(results))

    print('average success ratio:', ave_result[0])
    print('average success volume:', ave_result[1])
    print('average total volume:', ave_result[2])


def test_skew(skew_factor):
    print('performance under skewed payments, varying the skewness factor:')

    for obj in skew_factor:
        print('skewness factor:', obj)
        # print('LN result:')
        # skew(method="LN", bind_mode=None, skew_param=obj)

        print('Capybara result:')
        skew(method="Capybara", skew_param=obj)


def main():
    # test_multi_uniform([obj for obj in range(1, 26)])
    test_uniform_capacity([obj for obj in range(1, 26)])
    # test_skew([obj for obj in range(1, 9)])

if __name__ == "__main__":
    main()
