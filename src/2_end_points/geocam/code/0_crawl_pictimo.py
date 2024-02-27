# 爬去 pictimo 网站的信息, 正确结果储存在 ./data/2_pictimo_good.csv

from bs4 import BeautifulSoup, Comment
import re
import requests

wrong_result = open('../data/0_pictimo_wrong.csv', 'w')
good_result = open('../data/0_pictimo_good.csv', 'w')
  
homepage = 'https://www.pictimo.com'
country_url = homepage + '/' + 'country'

# 首先通过主页得到国家列表
req = requests.get(country_url, timeout=10)
soup = BeautifulSoup(req.text, "html.parser")

valid_landmarks = {}

# 检测是否是 v4, 要求输入是字符串
def is_ipv4(ip):
    m = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip)
    return bool(m) and all(map(lambda n: 0 <= int(n) <= 255, m.groups()))

def extract_ip_location(detailed_url) -> tuple:
    d_req = requests.get(detailed_url, timeout=10)
    d_soup = BeautifulSoup(d_req.text, "html.parser")
    # get ip:
    # <button type="button" class="play-btn" onclick="replaceWebcamPlaceholder(this, '.webcam-placeholder', 'img', 'http://125.213.209.53:80/webcapture.jpg?command=snap&amp;channel=1?COUNTER',null, null, 'camImage')
    try:
        button_list = d_soup.find_all('button', { 'class': 'play-btn' })
        candidates = button_list[0]['onclick'].split('\'')
        ip = candidates[5].split('/')[2].split(':')[0]
    except Exception as e:
        return None
    # get position:
    # <div id="map-canvas" data-latitude="34.528130" data-longitude="69.172330"
    try:
        # city_src = list_links[idx*2+1]['href']
        # ip = ip_src.split('/')[2].split(':')[0]
        # city = city_src.split('/')[2]
        map_list = d_soup.find_all('div', { 'id': 'map-canvas' })
        lat = map_list[0]['data-latitude']
        lon = map_list[0]['data-longitude']
    except Exception as e:
        return None
    return (ip, lat, lon)


# 发现网站中表示国家的 div 都用这个名字, 不保证以后都是这样
country_list = soup.find_all('div', { 'class': 'col-md-3 col-sm-3 col-xs-3' })
country_count = 0
for country in country_list:
    valid_count = 0
    country_name = (country['onclick']).split('\'')[1]
    # 得到这个国家的页面
    this_url = homepage + '/' + country_name
    country_name = country_name.split('/')[-1]
    print( f'country: {this_url}' )

    # 请求该页面, 找到所有摄像头对应的网页
    req = requests.get(this_url, timeout=10)
    soup = BeautifulSoup(req.text, "html.parser")

    div_1 = soup.find_all('div', { 'class': 'row templatemorow' })
    list_links = []
    for tmp_div in div_1:
        list_links.extend(tmp_div.find_all('a'))

    webcam_num = int(len(list_links) / 2)
    for idx in range(0, webcam_num):
        sub_url = list_links[idx*2+0]['href']
        detailed_url = homepage + sub_url
        try:
            ip, lat, lon = extract_ip_location(detailed_url)
        except Exception as e:
            continue
        
        if is_ipv4(ip):
            valid_count += 1
            valid_landmarks[ip] = (lat, lon)
        # else:
        #     wrong_result.writelines(new_line)
    country_count += 1
    print(f'country {country_name} has {webcam_num} webcams, {valid_count} valid webcams')
    print(f'processed {country_count} countries')

# 因为网页属于下拉响应, 所以直接通过 request 请求只能得到一部分
# 通过分析网络流得出该网站的 API
url = 'https://www.pictimo.com/get_infinitescroll_cams.php?page=country&countryID='
for i in range(0, 250):
    print(i)
    this_url = url + str(i)
    req = requests.get(this_url, timeout=10)

    for one_json in eval(req.text):
        # print(one_json)
        try:
            ip_src = one_json['imgLocation']
            city = one_json['City'].split(',')[0].lower()
            country = one_json['Country'].lower()
            sub_url = one_json['Link']
            detailed_url = homepage + sub_url
            try:
                ip, lat, lon = extract_ip_location(detailed_url)
            except Exception as e:
                continue
            
            if is_ipv4(ip):
                valid_landmarks[ip] = (lat, lon)
            #     good_result.writelines(new_line)
            # else:
            #     print('WRONG')
            #     wrong_result.writelines(new_line)
        except:
            continue
            # print('WRONG')
            # wrong_result.writelines(one_json)

for ip, (lat, lon) in valid_landmarks.items():
    new_line = f'{ip},{lat},{lon}\n'
    good_result.writelines(new_line)