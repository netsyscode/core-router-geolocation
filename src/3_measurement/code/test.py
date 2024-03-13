import os
import re
import pickle
import random
from typing import Dict, List
import pymysql
import requests
import concurrent.futures
import reverse_geocode
from functools import partial

requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

# Parameters
GEOBIN_DIR = '../../0_location_hint/pickle_bin'
SRC_DIR = '../src'
DST_DIR = './result'
TEST_DIR = './test'
FAIL_DIR = './failed'
TASK_NUM = 30 * 2
dict_city_alter_name = pickle.load(open(f'{GEOBIN_DIR}/dict_city_alter_to_name.bin', 'rb'))

server_ip = "77.81.242.205"
server_city = 'amsterdam'
client_ip = "114.179.35.69"
client_city = 'tokyo'

dict_server_info = pickle.load(open(f'{SRC_DIR}/dict_server_info.bin', 'rb'))

requests_get = partial(requests.get, timeout=30, verify=False)
requests_post = partial(requests.post, timeout=30, verify=False)

HOSTNAME_REGEX = r'^((([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9]))$'
IP_ADDR_REGEX = r'.*(\d+\.\d+\.\d+\.\d+).*'
DELAY_REGEX = r'^(\d+\.)?\d+$'  # float number or integer

STOP_WORDS = [
    (u'&nbsp;', ' ') ,
    (r'<br(.*?)/>', '\n')
    ]

TRACE_REGEX_1 = r'traceroute to (.*)(msec|ms)'
TRACE_REGEX_2 = r'Tracing the route to (.*)(msec|ms)'
TRACE_REGEX_3 = r'Command(.*)(msec|ms)'

REGEX_LIST = [TRACE_REGEX_1, TRACE_REGEX_2, TRACE_REGEX_3]

def make_trace_str(website):
    if '.php' in website.split('/')[-1]:
        website = website[:website.rfind('/')]
    if '?lang=' in website:
        website = website[:website.rfind('?lang=')]
    if website[-1] != '/':
        website = website + '/'
    return website

# process the info of one hop
# maybe several interfaces in one hop
def process_one_hop(info: List[str]) -> Dict:
    interface_dict = {}
    # check if there re more than one interface
    # everyinterface should have: 0-1 hostname / 1 ip / 1-3 time
    # there're 3 conditions: hostname (ip) / ip (ip) / ip
    ip = None
    hostname = None
    # mark a new interface
    clear_tag = False
    for i in range(0, len(info)):
        item: str = info[i]
        # an ip maybe matched with the hostname regex
        # we should determine the hostname and ip here
        # maybe '*' or 'ms' 'msec' or sth else 
        if re.match(DELAY_REGEX, item):
            if (not ip) and hostname:
                hostname, ip = '', hostname
            time = float(item)
            # add it if not exist, or update if the time is smaller
            if (ip, hostname) not in interface_dict or (time < interface_dict[(ip, hostname)]):
                interface_dict[(ip, hostname)] = time
            clear_tag = False
        elif re.search(r'\.', item) and re.match(HOSTNAME_REGEX, item):
            if not clear_tag:
                clear_tag = True
                ip = ''
            hostname = item.strip('()[]\{\}')
        elif re.search(IP_ADDR_REGEX, item):
            if not clear_tag:
                clear_tag = True
                hostname = ''
            ip = item.strip('()[]\{\}')
        else:
            continue
    return interface_dict

def extract_trace_res(text: str) -> List[List[List[str]]]:
    for raw, replace in STOP_WORDS:
        text = re.sub(raw, replace, text, flags=re.S)
    # match the regex, until their is a match
    for regex in REGEX_LIST:
        match = re.search(regex, text, flags=re.S)
        if match:
            break
    # split the match to lines
    lines = match.group(0).split('\\n')
    new_lines = []
    for line in lines:
        splited_lines = line.split('\n')
        new_lines.extend([line.strip() for line in splited_lines])

    # extract everyhop of the trace
    idx = 0
    useful_lines = []
    # skip the lines don't start with a number
    while idx < len(new_lines) and not re.match(r'^\d', new_lines[idx]):
        idx += 1
    # get the lines with a ip address
    while idx < len(new_lines) and re.search(r'(\d+\.\d+\.\d+\.\d+|\*)', new_lines[idx]):
        useful_lines.append(new_lines[idx])
        idx += 1
    # extract all lines start with a number
    hops: list[dict] = []
    for line in useful_lines:
        # a stardard hop: number hostname (ip) time1 time2 time3
        # duplicate hop: number? (hostname (ip) time+)+
        info = line.split()
        if re.match(r'^\d+$', info[0]):
            hop = int(info[0])
            info = info[1:]
            hops.append({})
        hop_info = process_one_hop(info)
        # merge the dict into one
        # if there are two same ip, update the smaller time
        if len(hop_info):
            hops[-1].setdefault
            for key, value in hop_info.items():
                if key not in hops[-1] or value < hops[-1][key]:
                    hops[-1][key] = value
# change to the format of list
    hops_list = []
    for hop in hops:
        hops_list.append([(key[0], key[1], value) for key, value in hop.items()])
    return hops_list if len(hops_list) else None

def test_api_0(website, client_ip='8.8.8.8', items=None):
    try:
        trace_str = make_trace_str(website) 
        trace_str += 'ajax.php?cmd=traceroute&host={}'
        req = requests_get(trace_str.format(client_ip))
        return req.text
    except Exception as e:
        pass
    return None

def test_api_1(website, client_ip='8.8.8.8', items=None):
    try:
        trace_str = make_trace_str(website)
        trace_str += '?query=trace&protocol=IPv4&addr={}&router='
        trace_str += items[1].replace(' ', '+')
        req = requests_get(trace_str.format(client_ip))
        return req.text
    except Exception as e:
        pass
    return None

def test_api_2(website, client_ip='8.8.8.8', items=None):
    try:
        trace_str = make_trace_str(website)
        trace_str += '?command=trace&protocol=ipv4&query={}&router='
        trace_str += items[1].replace(' ', '+')
        req = requests_get(trace_str.format(client_ip), timeout=10)
        return req.text
    except Exception as e:
        pass
    return None

def test_api_3(website, client_ip='8.8.8.8', items=None):
    try:
        trace_str = make_trace_str(website)
        trace_json = {
            'query': 'trace',
            'protocol': 'IPv4',
            'addr': client_ip,
            'router': items[1].replace(' ', '+'),
        }
        req = requests_post(trace_str, data=trace_json)
        return req.text
    except Exception as e:
        pass
    return None

def test_api_4(website, client_ip='8.8.8.8', items=None):
    try:
        trace_str = make_trace_str(website)
        trace_str += 'action.php?mode=looking_glass&action=trace'
        trace_json = {
            'id': items[1],
            'domain': client_ip,
        }
        req = requests_post(trace_str, data=trace_json)
        return req.text
    except Exception as e:
        pass
    return None

def test_api_5(website, client_ip='8.8.8.8', items=None):
    try:
        trace_str = make_trace_str(website)
        trace_str += 'execute.php'
        trace_json = {
            'routers': items[1].replace(' ', '+'),
            'query': 'traceroute',
            'parameter': client_ip,
            'dontlook': '',
        }
        req = requests_post(trace_str, data=trace_json)
        return req.text
    except Exception as e:
        pass
    return None

api_func_list = [
    test_api_0, 
    test_api_1, 
    test_api_2, 
    test_api_3,
    test_api_4,
    test_api_5,
]

def request_one_pair(one_pair):
    server_ip, client_ip = one_pair

    server_info = dict_server_info[server_ip]
    api_type  = dict_server_info[server_ip]['api_type']

    req = None
    try:
        make_api_func = api_func_list[api_type]
        raw_text = make_api_func(server_info['website'], client_ip, server_info['geohint'])
        return raw_text
    except:
        return None

executor = concurrent.futures.ThreadPoolExecutor(max_workers=TASK_NUM)
    
# with open(f'./{server_ip}_{client_ip}.txt', 'w') as srcfile:
#     # read all lines of the file
#     raw_text = request_one_pair((server_ip, client_ip))
#     if raw_text:
#         try:
#             trace_list = extract_trace_res(raw_text)
#             if trace_list:
#                 for idx, hops in enumerate(trace_list):
#                     for hop in hops:
#                         hop_info = "\t".join([str(item) for item in hop])
#                         srcfile.write(f'{idx+1}\t{hop_info}\n')
#             with open(f'{TEST_DIR}/{server_ip}_{client_ip}.txt', 'w') as test_file:
#                 test_file.write(raw_text)
#         except Exception as e:
#             with open(f'{FAIL_DIR}/{server_ip}_{client_ip}_failed.txt', 'w') as fail_file:
#                 fail_file.write(raw_text)
#             pass

with open(f'{TEST_DIR}/{server_ip}_{client_ip}.txt', 'r') as srcfile:
    # read all lines of the file
    raw_text = srcfile.readlines()
    raw_text = ''.join(raw_text)
    if raw_text:
        trace_list = extract_trace_res(raw_text)
        if trace_list:
            for idx, hops in enumerate(trace_list):
                for hop in hops:
                    hop_info = "\t".join([str(item) for item in hop])
                    print(f'{idx+1}\t{hop_info}')