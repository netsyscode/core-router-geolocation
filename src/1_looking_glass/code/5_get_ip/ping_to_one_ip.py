import os
import random
import time
import pickle
from typing import Tuple
import requests
from functools import partial
import concurrent.futures
from settings import * 

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

os.system(f'mkdir -p {DST_DIR}')

requests_get = partial(requests.get, timeout=10, verify=False)
requests_post = partial(requests.post, timeout=10, verify=False)

def make_ping_str(website):
    if '.php' in website.split('/')[-1]:
        website = website[:website.rfind('/')]
    if '?lang=' in website:
        website = website[:website.rfind('?lang=')]
    if website[-1] != '/':
        website = website + '/'
    return website

def test_api_0(website, client_ip='8.8.8.8', items=None):
    try:
        ping_str = make_ping_str(website) 
        ping_str += 'ajax.php?cmd=ping&host={}'
        req = requests_get(ping_str.format(client_ip))
        return req.text
    except Exception as e:
        pass
    return ''

def test_api_1(website, client_ip='8.8.8.8', items=None):
    try:
        ping_str = make_ping_str(website)
        ping_str += '?query=ping&protocol=IPv4&addr={}&router='
        ping_str += items[1].replace(' ', '+')
        req = requests_get(ping_str.format(client_ip))
        return req.text
    except:
        pass
    return ''

def test_api_2(website, client_ip='8.8.8.8', items=None):
    try:
        ping_str = make_ping_str(website)
        ping_str += '?command=ping&protocol=ipv4&query={}&router='
        ping_str += items[1].replace(' ', '+')
        req = requests_get(ping_str.format(client_ip), timeout=10)
        return req.text
    except:
        pass
    return ''

def test_api_3(website, client_ip='8.8.8.8', items=None):
    try:
        ping_str = make_ping_str(website)
        ping_json = {
            'query': 'ping',
            'protocol': 'IPv4',
            'addr': client_ip,
            'router': items[1].replace(' ', '+'),
        }
        req = requests_post(ping_str, data=ping_json)
        return req.text
    except Exception as e:
        pass
    return ''

def test_api_4(website, client_ip='8.8.8.8', items=None):
    try:
        ping_str = make_ping_str(website)
        ping_str += 'action.php?mode=looking_glass&action=ping'
        ping_json = {
            'id': items[1],
            'domain': client_ip,
        }
        req = requests_post(ping_str, data=ping_json)
        return req.text
    except:
        pass
    return ''

def test_api_5(website, client_ip='8.8.8.8', items=None):
    try:
        ping_str = make_ping_str(website)
        ping_str += 'execute.php'
        ping_json = {
            'routers': items[1].replace(' ', '+'),
            'query': 'ping',
            'parameter': client_ip,
            'dontlook': '',
        }
        req = requests_post(ping_str, data=ping_json)
        return req.text
    except:
        pass
    return ''

list_test_api = [
    test_api_0, 
    test_api_1, 
    test_api_2, 
    test_api_3,
    test_api_4,
    test_api_5,
]

input_list = pickle.load(open(f'{FORMER_RESULT_DIR}/list_good_routers.bin', 'rb'))
LG_NUM = len(input_list)
print('src: ', LG_NUM)

# a function to ping to one lg
def ping_to_one_lg(m_idx, lg_idx) -> Tuple[int, int, int, list]:
    one_router = input_list[lg_idx]
    test_api = list_test_api[one_router['api_type']]
    start_time = time.time()
    result = test_api(one_router['website'], client_ip=MACHINE_IPS[m_idx], items=one_router['geohint'])
    return m_idx, lg_idx, start_time, result[0:10]

# generate tasks at random order
task_params = []
timestamp_list = []
for m_idx in range(len(MACHINE_IPS)):
    timestamp_list.append([0 for _ in range(2 * LG_NUM)])
    for lg_idx in range(len(input_list)):
        task_params.append((m_idx, lg_idx))
random.shuffle(task_params)
    
TASK_NUM = 4
futures = []
with concurrent.futures.ProcessPoolExecutor(max_workers=TASK_NUM) as executor:
    for m_idx, lg_idx in task_params:
        futures.append(executor.submit(ping_to_one_lg, m_idx, lg_idx))
    
    # get the result and write to file
    for future in concurrent.futures.as_completed(futures):
        m_idx, lg_idx, start_time, result = future.result()
        end_time = time.time()
        timestamp_list[m_idx][2 * lg_idx] = str(start_time)
        timestamp_list[m_idx][2 * lg_idx + 1] = str(end_time)
        print(f'machine {m_idx} lg {lg_idx}, duration:{end_time- start_time}, res: {result[:10]}')
        
for m_idx in range(len(MACHINE_IPS)):
    time_list = timestamp_list[m_idx]
    with open(f'{DST_DIR}/{m_idx}_send.txt', 'w') as TIME_FILE:
        TIME_FILE.writelines('\n'.join(time_list))

print(f'Finish all probing')