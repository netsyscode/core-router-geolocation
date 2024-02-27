# 筛选使用了模板 LookingGlass 的网页
import re
from typing import Dict, Union
from bs4 import BeautifulSoup, Comment

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
            if ':' not in info: continue

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

lg_keyword = 'LookingGlass'
info_keyword = 'network information'
info_keyword_cn = '网络信息'
def check_one_soup(soup: BeautifulSoup):
    footer = soup.footer
    if footer:
        if re.search(lg_keyword, footer.get_text()):
            if re.search(info_keyword, soup.get_text(), re.IGNORECASE):
                return get_items_from_webpage(soup, 'location:')
            elif re.search(info_keyword_cn, soup.get_text(), re.IGNORECASE):
                return get_items_from_webpage(soup, '位置:')
            # some websites use comments to hide the 'network information'
            # find all the comments with substring matched 'network information'
            else:
                comments = soup.find_all(string=lambda text: isinstance(text, Comment))
                for comment in comments:
                    if re.search(info_keyword, comment, re.IGNORECASE):
                        return get_items_from_webpage(soup, 'location:')
                return 'TBD'
    return 'BAD'

def filter_by_template_0(website_name, src_file_path) -> Union[str, list[Dict]]:
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