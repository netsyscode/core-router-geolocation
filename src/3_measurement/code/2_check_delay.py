import os
import numpy as np
import pickle
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

# Parameters
SRC_DIR = '../src'
DATA_DIR = './result'
DST_DIR = '../pickle_bin'
FIG_DIR = './figure'


os.system(f'mkdir -p {FIG_DIR}')

dict_server_info = pickle.load(open(f'{SRC_DIR}/dict_server_info.bin', 'rb'))
dict_trace_info = pickle.load(open(f'{DST_DIR}/dict_trace_rtt.bin', 'rb'))

# test features, using model to fit the data
# using the model to fit the data, try to find the relationship between distance and rtt
# then plot the data and fitted curve on one figure, then store the figure

# combination 1: distance, rtt
X_1 = []
Y_1 = []
valid_count = 0
for src_dst in dict_trace_info:
    src, dst = src_dst.split('_')
    src_info = dict_server_info[src]
    dst_info = dict_server_info[dst]
    traces = dict_trace_info[src_dst]
    # count hostname
    host_name_count = 0
    for trace in traces['trace']:
        if trace[1] != '':
            host_name_count += 1
    rtt = float(traces['rtt'])
    dist = float(traces['distance'])
    if rtt > 400:
        continue
    if host_name_count > 1:
        valid_count += 1
    # transform the data to numpy array, convert string to float
    X_1.append([rtt])
    Y_1.append([dist])
X_1 = np.array(X_1)
Y_1 = np.array(Y_1)

print(f'valid count: {valid_count}')
print(f'X_1: {X_1.shape}, Y_1: {Y_1.shape}')

# linear
model_1 = LinearRegression().fit(X_1, Y_1)
print("Relent = {}".format(model_1.score(X_1, Y_1)))
print("Distance = {} * RTT + {}".format(model_1.coef_[0][0], model_1.intercept_[0]))
plt.scatter(X_1, Y_1, color='blue')
plt.plot(X_1, 100 * X_1, color='red')
plt.xlabel('rtt')
plt.ylabel('distance')
plt.title('distance vs rtt')
plt.savefig(f'{FIG_DIR}/distance_vs_rtt_1.png')
plt.close()



# TODO：分成不同的城市对，之后分开作图？

# # combination 2: distance, rtt and hop
# X_1 = []
# Y_1 = []
# for src_dst in dict_trace_info:
#     src, dst = src_dst.split('_')
#     src_info = dict_server_info[src]
#     dst_info = dict_server_info[dst]
#     rtt = float(dict_trace_info[src_dst]['rtt'])
#     hop = float(dict_trace_info[src_dst]['hop'])
#     dist = float(dict_trace_info[src_dst]['distance'])
#     if rtt > 1000:
#         continue
#     # transform the data to numpy array, convert string to float
#     X_1.append([dist, hop])
#     Y_1.append([rtt])
# X_1 = np.array(X_1)
# Y_1 = np.array(Y_1)

# # linear
# model_1 = LinearRegression().fit(X_1, Y_1)
# print("Relent = {}".format(model_1.score(X_1, Y_1)))
# print("RTT = {} * Distance + {} * Hop + {}".format(model_1.coef_[0][0], model_1.coef_[0][1], model_1.intercept_[0]))
# plt.scatter(X_1[:, 0], Y_1, color='blue')
# plt.scatter(X_1[:, 1], Y_1, color='red')
# plt.plot(X_1[:, 0], model_1.predict(X_1), color='green')
# plt.plot(X_1[:, 1], model_1.predict(X_1), color='yellow')
# plt.xlabel('distance and hop')
# plt.ylabel('rtt')
# plt.title('rtt vs distance and hop')
# plt.savefig(f'{FIG_DIR}/rtt_vs_distance_hop_2.png')
# plt.close()

# # combination 3: distance, rtt and city
# city_pairs = {}
# X_1 = []
# Y_1 = []
# valid_count = 0
# for src_dst in dict_trace_info:
#     src, dst = src_dst.split('_')
#     src_info = dict_server_info[src]
#     dst_info = dict_server_info[dst]
#     src_city = src_info['city'] if src_info['city'] != '洛杉矶' else 'losangeles'
#     dst_city = dst_info['city'] if src_info['city'] != '洛杉矶' else 'losangeles'
#     traces = dict_trace_info[src_dst]
#     if float(traces['rtt']) > 400:
#         continue
#     # sort
#     if src_city > dst_city:
#         src_city, dst_city = dst_city, src_city
#     if (src_city, dst_city) not in city_pairs:
#         city_pairs[(src_city, dst_city)] = []
#     city_pairs[(src_city, dst_city)].append(traces)
    
# example_pairs = [
#     # ('chicago', 'tokyo'),
#     # ('london', 'losangeles'),
#     # ('johannesburg', 'moscow'),
#     ('frankfurt', 'singapore')
# ]

# # # print above pairs and traces detail to independent files
# # for pair in example_pairs:
# #     src_city, dst_city = pair
# #     with open(f'{src_city}_{dst_city}.txt', 'w') as srcfile:
# #         srcfile.write(f'{src_city} -> {dst_city}\n')
# #         # print each hop of each trace
# #         # sort by rtt
# #         city_pairs[pair].sort(key=lambda x: float(x['rtt']))
# #         for trace in city_pairs[pair]:
# #             srcfile.write(f'{trace["rtt"]}\n')
# #             for hop in trace['trace']:
# #                 srcfile.write(f'{hop}\n')
# #             srcfile.write('\n')


# # collect rtt in each city pair
# # draw each trace with different color
# traces = []
# hop_delay = []
# trace_idx = []
# count = 0
# for pair in example_pairs:
#     src_city, dst_city = pair
#     for trace in city_pairs[pair]:
#         rtt = float(trace['rtt'])
#         # if rtt > 200:
#         #     continue
#         dist = float(trace['distance'])
#         hops = trace['trace']
#         hop_counts = [float(hop[0]) for hop in hops]
#         hop_rtt = [float(hop[-1]) for hop in hops]
#         per_hop_delay = [0 for _ in range(len(hop_rtt))]
#         # iterate reverse
#         max_rtt = hop_rtt[-1]
#         for i in range(len(hop_rtt) - 1, 0, -1):
#             if hop_rtt[i] > max_rtt:
#                 hop_rtt[i] = max_rtt
#             else:
#                 max_rtt = hop_rtt[i]
#         for i in range(len(hop_rtt) - 1, 0, -1):
#             per_hop_delay[i] = 0 if hop_rtt[i] < hop_rtt[i - 1] else hop_rtt[i] - hop_rtt[i - 1] 
#         traces.append([hop_counts, hop_rtt])
#         hop_delay.extend(per_hop_delay)
#         trace_idx.extend([count for _ in range(len(per_hop_delay))])
#         count += 1
# # draw
# # hop vs delay
# fig, ax = plt.subplots()
# for trace in traces:
#     ax.plot(trace[0], trace[1])
# ax.set_xlabel('hop')
# ax.set_ylabel('rtt')
# ax.set_title('rtt vs hop')
# plt.savefig(f'{FIG_DIR}/rtt_vs_hop_3.png')

# # scatter of hop_delay
# fig, ax = plt.subplots()
# ax.scatter(trace_idx, hop_delay)
# ax.set_xlabel('trace')
# ax.set_ylabel('per_hop_delay')
# plt.savefig(f'{FIG_DIR}/per_hop_delay.png')