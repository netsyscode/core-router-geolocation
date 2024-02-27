import os
import pickle
from template_0 import filter_by_template_0 as temp_0
from template_1 import filter_by_template_1 as temp_1
from template_2 import filter_by_template_2 as temp_2
from template_3 import filter_by_template_3 as temp_3
from template_4 import filter_by_template_4 as temp_4

SRC_WEBSITES_PATH = os.path.realpath('../../data/websites.txt')
WEBPAGES_DIR = f'../../data/webpages/'
EACH_TEMPLATE_DIR = './result'

# build list of webpages for each template
filter_funcs = [temp_0, temp_1, temp_2, temp_3, temp_4]
TEMPLATE_NUM = len(filter_funcs)
good_routers_list : list[list] = [list() for i in range(TEMPLATE_NUM)]
bad_routers_list : list = []
tbd_routers_list : list = []

# iterate all websites in websites.txt
for idx, row in enumerate(open(SRC_WEBSITES_PATH, encoding='utf-8')):
    website = row.strip()
    filename = website.replace('/', '_').replace(':', '.')
    filepath = f'{WEBPAGES_DIR}/{filename}.txt'
    
    # if the website is not crawled, skip it
    if not os.path.exists(filepath):
        continue
    bad_flag = 2
    for i in range(TEMPLATE_NUM):
        try:
            result = filter_funcs[i](website, filepath)
            if isinstance(result, list):
                good_routers_list[i].extend(result)
                bad_flag = 0
                break
            elif result == 'TBD':
                bad_flag = 1
        except Exception as e:
            print(f'error when processing {website} with template {i}')
    # mark the website as bad or tbd
    if bad_flag:
        if bad_flag == 1:
            tbd_routers_list.append(website)
        else:
            bad_routers_list.append(website)
    if idx % 100 == 0:
        print(f'processed {idx} websites')
            
for i in range(TEMPLATE_NUM):
    with open(f'{EACH_TEMPLATE_DIR}/template_{i}.pkl', 'wb') as f:
        pickle.dump(good_routers_list[i], f)
    print(f'good routers of template {i} are written to file, count: {len(good_routers_list[i])}')
with open(f'{EACH_TEMPLATE_DIR}/bad.txt', 'w') as f:
    for router in bad_routers_list:
        f.write(str(router) + '\n')
print(f'bad routers are written to file, count: {len(bad_routers_list)}')
with open(f'{EACH_TEMPLATE_DIR}/tbd.txt', 'w') as f:
    for router in tbd_routers_list:
        f.write(str(router) + '\n')
print(f'tbd routers are written to file, count: {len(tbd_routers_list)}')