import dpkt
import socket
# import datetime
import sys
import os
import pickle
import operator
import ast
import json
from pytz import timezone
import settings
from settings import *

LG_NUM = len(LG_LIST)

result_each_time = []

def get_valid_ip(src, dst):
    if (src in MACHINE_IPS) or (src in PRIVATE_IPS):
        return dst
    else:
        return src

# start_time & end_time timestamp list
time_lists = []

for m_idx in range(0, len(MACHINE_IPS)):
    time_list = []
    with open(f'{RESULT_DIR}/{m_idx}_send.txt', 'r') as srcfile:
        # 2 rows in a pair, start and end
        for idx in range(LG_NUM):
            start_time = float(srcfile.readline().strip())
            end_time = float(srcfile.readline().strip())
            time_list.append((start_time, end_time))
    time_lists.append(time_list)

    ip_count_list = [{} for idx in range(LG_NUM)]

# log the timestamp of the icmp packet
icmp_timestamp_list = [[], []]
for m_idx in range(0, len(MACHINE_IPS)):
    with open(f'{RESULT_DIR}/{m_idx}_receive.warts', 'rb') as fr:
        pcap = dpkt.pcap.Reader(fr)
        for timestamp, buffer in pcap:
            # 解包, 物理层
            ethernet = dpkt.ethernet.Ethernet(buffer)
            # 判断网络层是否存在
            if not isinstance(ethernet.data, dpkt.ip.IP):
                continue
            ip = ethernet.data
            # 判断是否是 ICMP
            if not isinstance(ip.data, dpkt.icmp.ICMP):
                continue

            icmp = ip.data
            src_ip = socket.inet_ntoa(ip.src)
            dst_ip = socket.inet_ntoa(ip.dst)
            this_ip = get_valid_ip(src_ip, dst_ip)
            # mark the timestamp of the icmp packet
            icmp_timestamp_list[m_idx].append((timestamp, this_ip))
        # sort by timestamp, ascending
        icmp_timestamp_list[m_idx].sort(key=operator.itemgetter(0))

# intersection the icmp timestamp with time_list duration 
intersect_list = [[set() for _ in range(LG_NUM)] for _ in range(len(MACHINE_IPS))]
for m_idx in range(0, len(MACHINE_IPS)):
    for lg_idx in range(LG_NUM):
        start_time, end_time = time_lists[m_idx][lg_idx]
        cur_idx = 0
        while icmp_timestamp_list[m_idx][cur_idx][0] <= start_time:
            cur_idx += 1
        for timestamp, this_ip in icmp_timestamp_list[m_idx][cur_idx:]:
            if timestamp < end_time:
                intersect_list[m_idx][lg_idx].add(this_ip)
            else:
                break    
        
dict_lg_info = {}
bad_lg_info = []
for lg_idx in range(LG_NUM):
    lg_intersections = [intersect_list[m_idx][lg_idx] for m_idx in range(len(MACHINE_IPS))]
    candiates = list(set.intersection(*lg_intersections))
    print(candiates)
    print('----------------------')
    if len(candiates) == 1:
        dict_lg_info[candiates[0]] = LG_LIST[lg_idx]
    else:
        # log the infomation of the lg
        bad_lg_info.append(LG_LIST[lg_idx])

print('dst: ', len(dict_lg_info))
print('bad: ', len(bad_lg_info))

pickle.dump(dict_lg_info, open(f'{DST_DIR}/dict_lg_info.bin', 'wb'))
json.dump(bad_lg_info, open(f'{DST_DIR}/bad_lg_info.json', 'w'), indent=4, ensure_ascii=False)