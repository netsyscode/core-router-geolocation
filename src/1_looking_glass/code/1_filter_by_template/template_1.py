# 查找网页中包含 'location:' 的网页
import re
from typing import Dict, Union
from bs4 import BeautifulSoup
  

# 1. using this template and get information sucessfully
# 2. using this template but fail to get information
# 3. not using this template
ipv4 = 'ipv4'
ipv6 = 'ipv6'
def get_items_from_webpage(soup: BeautifulSoup, pos_begin):
    (position, v4, v6) = ('None', 'None', 'None')
    for elem in soup(text=re.compile(pos_begin, re.IGNORECASE)):
        info_block = elem.parent.parent
        list_info = info_block.get_text().split('\n')

        for info in list_info:
            # 为了确保是 xx: yyy 的形式
            if len(info.split(':')) != 2: continue

            try:
                if re.search(pos_begin, info, re.IGNORECASE):
                    position = info.split(':')[1].strip()
                elif re.search(ipv4, info, re.IGNORECASE):
                    v4 = info.split(':')[1].split()[0]
                elif re.search(ipv6, info, re.IGNORECASE):
                    v6 = info[info.find(':')+1 : ].split()[0]
            except:
                pass
    return (position, v4, v6)

keywords_list = [ 'network information', 'location:', 'ipv4:' ]
def check_one_soup(soup: BeautifulSoup):
    raw_text = soup.get_text().lower()
    for keyword in keywords_list:
        if not re.search(keyword, raw_text, re.IGNORECASE):
            return 'BAD'

    items = get_items_from_webpage(soup, 'location:')
    return items

def filter_by_template_1(website_name, src_file_path) -> Union[str, list[Dict]]:   
    with open(src_file_path, 'r') as srcfile:
        result = check_one_soup(BeautifulSoup(srcfile.read(), "lxml"))
    if isinstance(result, str):
            return result
    else:
        return [{
            'website': website_name,
            'geohint': ('', result[0], ''),
            'ipv4hint': result[1],
            'ipv6hint': result[2],
        }]