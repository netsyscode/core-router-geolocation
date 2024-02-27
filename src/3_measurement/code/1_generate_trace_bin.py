import os
import pickle
import geopy.distance

# Parameters
SRC_DIR = '../src'
DATA_DIR = './result'
DST_DIR = '../pickle_bin'

os.system(f'mkdir -p {DST_DIR}')

dict_server_info = pickle.load(open(f'{SRC_DIR}/dict_server_info.bin', 'rb'))

# iterate over the files in the result directory
dict_trace_info = {}
src_dst_pairs = [x[0:-4] for x in os.listdir(DATA_DIR)]

count = 0

for src_dst in src_dst_pairs:
    src, dst = src_dst.split('_')
    src_info = dict_server_info[src]
    dst_info = dict_server_info[dst]
    distance = geopy.distance.distance(src_info['coordinate'], dst_info['coordinate']).km
    # print(f'{src} -> {dst}, {src_info["city"]} -> {dst_info["city"]} : {distance} km')
    # TODO: can I turn this into .warts file?
    with open(f'{DATA_DIR}/{src_dst}.txt', 'r') as srcfile:
        # skip the first two lines
        # hop, hostname, ip, rtt
        raw_trace = srcfile.readlines()
        useful_trace = [x.strip().split('\t') for x in raw_trace[2:]]
        if len(useful_trace) > 0:
            is_success = dst in useful_trace[-1][2]
            if is_success:
                # check if the distance is over the signal speed
                # 300,000 km/s -> 300 km/ms (light) -> 200 km/ms (signal) -> 100 km/ms (rtt)
                if distance > 100 * float(useful_trace[-1][3]):
                    # print(f'{src} -> {dst}, {src_info["city"]} -> {dst_info["city"]} : {distance} km')
                    pass
                else:
                    dict_trace_info[src_dst] = {
                        'success': is_success,
                        'hop': useful_trace[-1][0],
                        'distance': distance,
                        'rtt': useful_trace[-1][3],
                        'trace': useful_trace
                    }
    
    count += 1
    if count % 100 == 0:
        print(f'Processed {count} files')

pickle.dump(dict_trace_info, open(f'{DST_DIR}/dict_trace_rtt.bin', 'wb'))
