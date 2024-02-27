# 筛选使用了模板 LookingGlass 的网页
from typing import Dict, Union
from bs4 import BeautifulSoup

# 1. using this template and get information sucessfully
# 2. using this template but fail to get information
# 3. not using this template
def get_items_from_webpage(soup: BeautifulSoup):
    node_items = soup.body.find('select', {'id': 'routers'}).find_all('option')
    result = []
    for x in node_items:
        result.append((x.get('value'), x.get_text()))
    return result

keyword = 'Looking Glass'
def check_one_soup(soup: BeautifulSoup):
    try:
        footer_bar = soup.body.find('div', {'class': 'footer_bar'})
        if footer_bar and keyword in footer_bar.get_text():
            return get_items_from_webpage(soup)
        return 'BAD'
    except:
        return 'BAD'

def filter_by_template_3(website_name, src_file_path) -> Union[str, list[Dict]]:
    with open(src_file_path, 'r') as srcfile:
        result = check_one_soup(BeautifulSoup(srcfile.read(), "lxml"))
        if isinstance(result, str):
            return result
        else:
            router_list = []
            for one_router in result:
                router_list.append({
                    'website': website_name,
                    'geohint': ('', one_router[0], one_router[1]),
                    'ipv4hint': '',
                    'ipv6hint': '',
                })
            return router_list
