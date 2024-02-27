# 爬去 insecam 网站的信息, 正确结果储存在 ./data/2_insecam_good.csv

from bs4 import BeautifulSoup, Comment
import re
import requests
from retrying import retry
import math
import concurrent.futures

insecam_good = open('../data/0_insecam_good.csv', 'w')
insecam_wrong = open('../data/0_insecam_wrong.csv', 'w')
insecam_failed_instance = open('../data/0_insecam_failed_instance.txt', 'w')
insecam_failed_pages = open('../data/0_insecam_failed_pages.txt', 'w')

headers = {
    'User-Agent': "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
}

# 检测是否是 v4, 要求输入是字符串
def is_ipv4(ip):
    m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip)
    return bool(m) and all(map(lambda n: 0 <= int(n) <= 255, m.groups()))

# rubust decorator
@retry(stop_max_attempt_number=5)
def get_response(url):
    req = requests.get(url, timeout=10, headers=headers)
    return req

def get_all_cams_in_page(url) -> list | str : 
    try:
        req = get_response(url)
    except Exception as e:
        return url
    soup = BeautifulSoup(req.text, "html.parser")
    return soup.find_all('a', { 'class': 'thumbnail-item__wrap' })

def extract_ip_location(cam) -> tuple:
    link = cam.find('img')['src']
    ip = link.split('/')[2].split(':')[0]
    # get the detailed page, then parse the latitude and longitude
    # <a class="thumbnail-item__wrap" href="/en/view/1010251/"
    sub_url = cam['href']
    detailed_url = f'http://www.insecam.org{sub_url}'
    try:
        d_req = get_response(detailed_url)
    except Exception as e:
        return (detailed_url)
    d_soup = BeautifulSoup(d_req.text, "html.parser")
    # get the latitude and longitude using regex
    '''
    <div class="camera-details__row">
        <div class="camera-details__cell">
            Latitude:
        </div><div class="camera-details__cell">
            34.727581
        </div>
    </div>
    '''
    '''
    <div class="camera-details__row">
        <div class="camera-details__cell">
            Longitude:
        </div>
        <div class="camera-details__cell">
            -86.567359
        </div>
    </div>
    '''
    candidates = d_soup.find_all('div', { 'class': 'camera-details__cell' })
    for c in candidates:
        if 'Latitude' in c.text:
            lat = c.find_next_sibling().text.strip()
        elif 'Longitude' in c.text:
            lon = c.find_next_sibling().text.strip()
    if is_ipv4(ip) and lat and lon:
        return (ip, lat, lon)
    else:
        return (detailed_url)

# 通过该 API 可以请求国家和对应的个数
jsoncountry_url = 'http://www.insecam.org/en/jsoncountries/'
req = get_response(jsoncountry_url)
# print(req.text)

list_country = []

for k, v in eval(req.text).get('countries').items():
    list_country.append((k, v['count']))

# 记录所有失败的url，并跳过这些url
homepage = 'http://www.insecam.org/en/bycountry'

print("Start crawling insecam")
processed_count = 0
pages_future_list = []
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    # 并行地爬取所有页，拿到所有的摄像头
    for one_country in list_country:
        iso_code = one_country[0]
        page_max = math.ceil(one_country[1] / 6)    
    # 每页有六个摄像头，并行地爬取
        for i in range(1, page_max+2):
            this_url = f'{homepage}/{iso_code}/?page={i}'
            pages_future_list.append(executor.submit(get_all_cams_in_page, this_url))
            

# 从结果中得到所有的cam列表
finished_count = 0
cam_list = []
for future in concurrent.futures.as_completed(pages_future_list):
    # get the results
    res = future.result()
    # update the global variables
    if isinstance(res, str):
        insecam_failed_pages.writelines(res + '\n')
    else:
        cam_list.extend(res)
    finished_count += 1
    print("Finished {} pages".format(finished_count))

print("Finished all pages, {} cams in total".format(len(cam_list)))

# 并行爬取所有的cam
cam_future_list = []
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor: 
    for cam in cam_list:
        cam_future_list.append(executor.submit(extract_ip_location, cam))

# 获取结果
finished_count = 0
for future in concurrent.futures.as_completed(cam_future_list):
    result = future.result()
    finished_count += 1
    if finished_count % 100 == 0:
        print(f"Finished {finished_count} cams")
    if len(result) == 3:
        ip, lat, lon = result
        insecam_good.writelines(ip + ',' + lat + ',' + lon + '\n')
    else:
        insecam_failed_instance.writelines(result[0] + '\n')