import os
import re
import pickle
import random
from typing import List
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


dict_server_info = pickle.load(open(f'{SRC_DIR}/dict_server_info.bin', 'rb'))

# dict_client_info = pickle.load(open(f'{SRC_DIR}/dict_client_info.bin', 'rb'))

# load client ip from database

# using private IP address
MYSQL_HOST = '172.29.45.143'
# MYSQL_HOST = '182.92.82.138'
USER = 'root'
PASSWD = 'netsys_galileo'
DATABASE = 'galileo'
CLIENT_TABLE_NAME = 'endpoint'
PORT = 3309

# Connect to the database
connection = pymysql.connect(host=MYSQL_HOST,
                            port=PORT,
                            user=USER,
                            password=PASSWD,
                            db=DATABASE,
                            charset='utf8mb4',
                            cursorclass=pymysql.cursors.DictCursor)

os.system(f'mkdir -p {DST_DIR}')
os.system(f'mkdir -p {TEST_DIR}')
os.system(f'mkdir -p {FAIL_DIR}')

requests_get = partial(requests.get, timeout=20, verify=False)
requests_post = partial(requests.post, timeout=20, verify=False)

HOSTNAME_REGEX = r'^((([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9]))$'
IP_ADDR_REGEX = r'.*(\d+\.\d+\.\d+\.\d+).*'

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

def extract_trace_res(text: str) -> List[List[List[str]]]:
    for raw, replace in STOP_WORDS:
        text = re.sub(raw, replace, text, re.S)
    # match the regex, until their is a match
    for regex in REGEX_LIST:
        match = re.search(regex, text, re.S)
        if match:
            break
    # split the match to lines
    lines = match.group(0).split('\\n')
    new_lines = []
    for line in lines:
        new_lines.extend([line.strip() for line in line.split('\n')])

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
    hops = []
    for line in useful_lines:
        # a stardard hop: number hostname (ip) time1 time2 time3
        # duplicate hop: number? hostname (ip) time
        info = line.split()
        if re.match(r'^\d+$', info[0]):
            hop = int(info[0])
            info = info[1:]
            hops.append([])
        # get the min time
        min_time = 100000
        hostname = ''
        not_anoymous = False
        idx = 0
        for i in range(0, len(info)):
            item: str = info[i]
            if re.match(r'^(\d+\.)?\d+$', item):
                time = float(item)
                if time < min_time:
                    min_time = time
                not_anoymous = True
            elif re.search(IP_ADDR_REGEX, item) and not not_anoymous:
                ip = item.strip('()[]\{\}')
            elif re.search(r'\.', item) and re.match(HOSTNAME_REGEX, item) and not not_anoymous:
                hostname = item.strip('()[]\{\}')
        # collect the hostname, ip and min time
        if not_anoymous:
            hops[hop-1].append([hostname, ip, min_time])
    return hops if len(hops) else None

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


client_city_set = {}
server_city_set = set()

with connection.cursor() as cursor:
    # Read a single record
    sql = f"SELECT * FROM {CLIENT_TABLE_NAME}"
    cursor.execute(sql)
    result = cursor.fetchall()
    dict_client_info = {}
    for row in result:
        # using int_2_ip
        str_ip: str= '.'.join([str((row['ip'] >> 24) & 0xFF), str((row['ip'] >> 16) & 0xFF), str((row['ip'] >> 8) & 0xFF), str(row['ip'] & 0xFF)])
        coord = (row['lat'], row['lon'])
        city_info = reverse_geocode.search((coord,))[0]
        alt_city = city_info['city'].lower().replace(' ', '-')
        dict_client_info[str_ip] = {
                'city': alt_city,
                'coordinate': coord,
        }
        if alt_city not in client_city_set:
            client_city_set[alt_city] = 0
        client_city_set[alt_city] += 1
        # alter to standard city name
        # if alt_city in dict_city_alter_name:
        #     std_city = dict_city_alter_name[alt_city]
        #     dict_client_info[row['ip']] = {
        #         'ip': str_ip,
        #         'city': std_city,
        #         'coordinate': coord,
        #     }
        # else:
        #     print("City not found: ", alt_city)

for server_ip in dict_server_info:
    coord = dict_server_info[server_ip]['coordinate']
    alt_city = reverse_geocode.search((coord,))[0]['city'].lower().replace(' ', '-')
    dict_client_info[server_ip] = {
        'city': alt_city,
        'coordinate': coord
    }
    # TODO: modify this bad code
    # --------------------------------------------
    dict_server_info[server_ip]['city'] = alt_city
    # --------------------------------------------
    server_city_set.add(alt_city)
    if alt_city not in client_city_set:
        client_city_set[alt_city] = 0
    client_city_set[alt_city] += 1

# choose the top 100 most frequent city in the client set
client_city_list = sorted(client_city_set.items(), key=lambda x: x[1], reverse=True)[0:20]
client_city_list = [item[0] for item in client_city_list]
dict_client_info = {k: v for k, v in dict_client_info.items() if v['city'] in client_city_list}

print('client: ', len(dict_client_info))

# make the server to trace the client
# split the task into city pairs
pairs = []
for server_ip in dict_server_info:
    for client_ip in dict_client_info:
        # add to the pairs
        city_pair = (dict_server_info[server_ip]['city'], dict_client_info[client_ip]['city'])
        ip_pair = (server_ip, client_ip)
        pairs.append([ip_pair, city_pair])
        
random.shuffle(pairs)
print(f'Number of pairs: {len(pairs)}')

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

tasks_parm = {}
for one_pair in pairs:
    one_task = executor.submit(request_one_pair, one_pair[0])
    tasks_parm[one_task] = one_pair

count = 0

for one_task in concurrent.futures.as_completed(tasks_parm.keys()):
    ip_pair, city_pair = tasks_parm[one_task]
    # make dir for each city pair
    subdir = f'{DST_DIR}/{city_pair[0]}_{city_pair[1]}'
    # check if there is whitespace in the subdir path
    subdir = subdir.replace(' ', '-') 
    if not os.path.exists(subdir):
        os.system(f'mkdir -p {subdir}')
    
    with open(f'{subdir}/{ip_pair[0]}_{ip_pair[1]}.txt', 'w') as srcfile:
        # get the raw result from the task first
        raw_text = one_task.result()
        if raw_text:
            try:
                trace_list = extract_trace_res(raw_text)
                if trace_list:
                    for idx, hops in enumerate(trace_list):
                        for hop in hops:
                            hop_info = "\t".join([str(item) for item in hop])
                            srcfile.write(f'{idx+1}\t{hop_info}\n')
                # with open(f'{TEST_DIR}/{ip_pair[0]}_{ip_pair[1]}.txt', 'w') as test_file:
                #     test_file.write(raw_text)
            except Exception as e:
                # with open(f'{FAIL_DIR}/{ip_pair[0]}_{ip_pair[1]}_failed.txt', 'w') as fail_file:
                #     fail_file.write(raw_text)
                pass
        count += 1
        if count % 100 == 0:
            print(f'Finished {count} pairs')