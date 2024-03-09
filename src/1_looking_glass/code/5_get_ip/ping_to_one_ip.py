import os
import time
import pickle
from typing import Tuple
import requests
from functools import partial
import concurrent.futures
from settings import * 

os.system(f'mkdir -p {DST_DIR}')

requests_get = partial(requests.get, timeout=30, verify=False)
requests_post = partial(requests.post, timeout=30, verify=False)

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
print('src: ', len(input_list))

# mark the start and end time for each probe
def ping_to_one_machine(m_idx) -> Tuple[int, list]:
    os.system(f'mkdir -p {DST_DIR}/{m_idx}_record')
    timestamp_list = []
    for idx, one_router in enumerate(input_list):
        begin_time = str(time.time())
        timestamp_list.append(begin_time)
        test_api = list_test_api[one_router['api_type']]
        result = test_api(one_router['website'], client_ip=MACHINE_IPS[m_idx], items=one_router['geohint'])
        with open(f'{DST_DIR}/{m_idx}_record/{idx}.txt', 'w') as RECORD_FILE:
            RECORD_FILE.writelines(result)
        # sleep for 5 seconds
        time.sleep(5)

    end_time = str(time.time())
    timestamp_list.append(end_time)
    return m_idx, timestamp_list

TASK_NUM = 5
futures = []
with concurrent.futures.ProcessPoolExecutor(max_workers=TASK_NUM) as executor:
    futures.extend([executor.submit(ping_to_one_machine, m_idx) for m_idx in range(len(MACHINE_IPS))])
    # get the result and write to file
    for future in concurrent.futures.as_completed(futures):
        m_idx, timestamp_list = future.result()
        print(timestamp_list)
        with open(f'{DST_DIR}/{m_idx}_send.txt', 'w') as TIME_FILE:
            TIME_FILE.writelines('\n'.join(timestamp_list))
            print(f'Finish {m_idx} machine, {len(timestamp_list)} lines in TIME_FILE')