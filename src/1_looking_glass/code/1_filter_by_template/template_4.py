# 使用了模板 'freshmeat' 的网页, 但是网页信息中没有 'freshmeat' 字样

from typing import Dict, Union
from bs4 import BeautifulSoup, Comment

# 1. using this template and get information sucessfully
# 2. using this template but fail to get information
# 3. not using this template
def get_items_from_webpage(soup: BeautifulSoup):
    def get_nodes_info(node_label, nodes_list):
        node_details = node_label.find_all('option')
        for node_detail in node_details:
            node_value = node_detail.get('value')
            node_description = node_detail.get_text().strip()
            nodes_list.append((node_value, node_description))

    node_items = soup.body.form.table.find('select', {'name': 'router'})
    node_labels = node_items.find_all('optgroup')

    result = {}
    if node_labels:
        for node_label in node_labels:
            label_name = node_label.get('label')
            result[label_name] = []
            get_nodes_info(node_label, result[label_name])
    else:
        result['default'] = []
        get_nodes_info(node_items, result['default'])
    return result

def check_one_soup(soup: BeautifulSoup):
    try:
        if soup.body.form.table.find('select', {'name': 'router'}):
            try:
                ths_list = soup.body.form.table.find_all('th')
                ths_list = [x.get_text() for x in ths_list]
                if len(ths_list) == 3:
                    if 'Node' in ths_list[2] or 'Router' in ths_list[2]:
                        return get_items_from_webpage(soup)
            except:
                pass
            return 'TBD'
    except:
        pass
    return 'BAD'

def filter_by_template_4(website_name, src_file_path) -> Union[str, list[Dict]]:
    with open(src_file_path, 'r') as srcfile:
        result = check_one_soup(BeautifulSoup(srcfile.read(), "lxml"))
        if isinstance(result, str):
            return result
        else:
            router_list = []
            for label, routers in result.items():
                for one_router in routers:
                    router_list.append({
                        'website': website_name,
                        'geohint': (label, one_router[0], one_router[1]),
                        'ipv4hint': '',
                        'ipv6hint': '',
                    })
            return router_list
