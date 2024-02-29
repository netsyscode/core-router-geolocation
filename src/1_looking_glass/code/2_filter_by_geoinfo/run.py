import os
import pickle
import re
from string import digits
from typing import List, Set, Tuple

# base geoinfo data structure
GEOBIN_DIR = '../../../0_location_hint/pickle_bin'
dict_city_by_name = pickle.load(open(f'{GEOBIN_DIR}/dict_city_by_name.bin', 'rb'))
dict_hasspace_city = pickle.load(open(f'{GEOBIN_DIR}/dict_hasspace_city.bin', 'rb'))
dict_iata_code = pickle.load(open(f'{GEOBIN_DIR}/dict_iata_code.bin', 'rb'))
dict_city_by_country = pickle.load(open(f'{GEOBIN_DIR}/dict_city_by_country.bin', 'rb'))
dict_city_alter_name = pickle.load(open(f'{GEOBIN_DIR}/dict_city_alter_to_name.bin', 'rb'))
# vowels characters
vowels = ['a', 'e', 'i', 'o', 'u']

# filtered LG routers
TEMPLATE_RESULT_DIR = '../1_filter_by_template/result'
# the number of filename start with `template``
TEMPLATE_NUM = int(os.popen(f'ls {TEMPLATE_RESULT_DIR} | grep template | wc -l').read().strip())
 
# 1. geolocate successfully
# 2. cannot ensure the correct of geolocatoin
# 3. cannot geolocate
DST_FILES_DIR = f'./result/'
os.system(f'mkdir -p {DST_FILES_DIR}')

list_good_routers = []
list_bad_routers = []
list_tbd_routers = []

def split_word(name: str):
    name_split = set()

    # remove digits
    table = str.maketrans('', '', digits)
    name = name.translate(table).lower()

    # check format 'xx, yy'
    if name.count(',') > 0 and '(' not in name:
        # 对于 '-' 字符, 有两种选择, 一个是删掉, 一个是替换为 ','
        new_name = name.replace('-', '')
        name_split.update([x.replace(' ', '') for x in new_name.split(',')])
        new_name = name.replace('-', ',')
        name_split.update([x.replace(' ', '') for x in new_name.split(',')])
    # check format 'xx (AS number)'
    elif '(as' in name:
        pass
    else:
        name = name.replace('(', ' ')
        name = name.replace(')', ' ')
        name = name.replace(',', ' ')
        name = name.replace('，', ' ')
        name = name.replace('/', ' ')

        # 对于 '-' 字符, 有两种选择, 一个是删掉, 一个是替换为 ','
        # name_split.update(name.replace('-','').split())
        name_split.update(name.replace('-',' ').split())

    return name_split


# check if the word is abbreviation of a place
def check_if_abbr(word: str, place: str) -> bool:
    # the first letter must be the same
    if word[0] != place[0]:
        return False
    i, j, k = 0, 0, 0
    # for those without space, the letters of abbreviation must be in very first places
    # vowels are always ignored, max one consonant difference is allowed
    while i < len(word) and j < len(place):
        if word[i] == place[j]:
            i += 1
        elif place[j] not in vowels:
            k += 1
        j += 1
    check_res = (i == len(word)) and (k <= 1)
    return check_res

# using depth-first search to check if the word is abbreviation of a place with space
# for those with space: 
# 1. the first letter of slice must be the first one appear in the word for each slice
# 2. all the letters of abbreviation must be in order, but can be missed
# 3. if current slice can not match the abbreviation, then move to next slice
# e.g. saint petersburg -> sp / stp / sntp / spb are all valid abbreviation
def check_if_abbr_with_space(word: str, slice_list: list[str], idx: int, jdx: int, kdx: int) -> bool:
    # idx for word char index, jdx for slice index, kdx for slice char index
    # fully matched
    if idx == len(word):
        return True
    # totally unmatched
    if jdx == len(slice_list):
        return False
    # the first letter must be the same
    if kdx == 0:
        if word[idx] != slice_list[jdx][0]:
            return False
        else:
            return check_if_abbr_with_space(word, slice_list, idx + 1, jdx, kdx + 1)
    while kdx < len(slice_list[jdx]):
        # try to match the abbreviation
        if word[idx] == slice_list[jdx][kdx]:
            if check_if_abbr_with_space(word, slice_list, idx + 1, jdx, kdx + 1):
                return True
        kdx += 1
    # if not finished yet, means the abbreviation is not matched in current slice
    # idx cannot over the length of word here, because every match will lead to a func call
    return check_if_abbr_with_space(word, slice_list, idx, jdx + 1, 0)

# get candidates of abbreviation, need further validation for true result
# **the abbr format is different when the city name has space**
def get_abbr_candidate(word : Set[str]) -> List:
    # if len(w) < 3, check if it is a contry code, filter out of these words
    word_short = [w for w in word if len(w) == 2]
    word_long = [w for w in word if len(w) >= 3]
    # TODO: what if there are combined word with country code + city name ???
    poss_country_code = []
    for w in word_short:
        if w in dict_city_by_country.keys():
            poss_country_code.append(w)
    # here we need to check city name with space for better result
    poss_cities = [city for code in poss_country_code for city in list(dict_city_by_country[code].keys())]
    poss_cities_with_space: list[str] = [key for key, value in dict_hasspace_city.items() if value[1] in poss_country_code]
    poss_candidates = []
    
    if len(poss_cities) == 0 or len(word_long) == 0:
        return None
    
    # abbr by total word
    # one abbreviation may have multiple candidates
    # only the most chosen results are selected
    # then we need to check the final result by manual
    for w in word_long:
        for city in poss_cities:
            if check_if_abbr(w, city):
                poss_candidates.append(city)
        for city in poss_cities_with_space:
            slice_list = re.split(r'\s+', city)
            if check_if_abbr_with_space(w, slice_list, 0, 0, 0):
                poss_candidates.append(dict_hasspace_city[city][3])

    # bad process, many alter names included
    # merge the candidates that indicates the same city
    set_candidates = set()
    for name in poss_candidates:
        city_name = dict_city_by_name[name][3]
        if city_name in dict_city_by_name.keys():
            standard_name = dict_city_alter_name[city_name]
            set_candidates.add(standard_name)
    
    if len(set_candidates) == 0:
        return None
    
    # choose the top-10 polulation city in candidates
    final_candidates = set()
    for _ in range(10):
        if len(set_candidates) == 0:
            break
        max_name = ''
        max_pop = 0
        for name in set_candidates:
            pop = dict_city_by_name[name][4]
            if pop > max_pop:
                max_name = name
                max_pop = pop
        final_candidates.add(max_name)
        set_candidates.remove(max_name)
            
    # TODO: verify the result using ping or traceroute
    return list(final_candidates)

def check_raw_word(raw_word, iata_code=True):
    raw_word = raw_word.lower()

    # check if the word is a city name with space
    for name in dict_hasspace_city:
        if name in raw_word:
            return ('GOOD', (dict_hasspace_city[name], 'space'))

    set_oneword = split_word(raw_word)

    candidates = list()
    for word in set_oneword:
        # 检查是否是 IATA CODE, 如果有则必须要有: 国家代码 / IXP
        if iata_code and word in dict_iata_code:
            if dict_iata_code[word][1] in set_oneword:
                candidates.append((dict_iata_code[word], 'iata'))
            if 'ixp' in set_oneword:
                candidates.append((dict_iata_code[word], 'iata'))

        # 检查是否是 城市名
        if word in dict_city_by_name:
            candidates.append((dict_city_by_name[word], 'name'))

   
    # 如果有两个候选，看一下是否 A 是 B 的所属州
    if len(candidates) == 2:
        _, _, admin_0, city_0, _  = candidates[0][0]
        _, _, admin_1, city_1, _  = candidates[1][0]
        if city_0 == admin_1:
            return ('GOOD', candidates[1])
        if city_1 == admin_0:
            return ('GOOD', candidates[0])    
    # 如果有多个候选，那么看一下他们的坐标是否相近
    if len(candidates) > 0:
        coor_candidates = [x[0][0] for x in candidates]
        for cdx_1 in range(0, len(coor_candidates)):
            for cdx_2 in range(cdx_1 + 1, len(coor_candidates)):
                if abs(coor_candidates[cdx_1][0] - coor_candidates[cdx_2][0]) > 0.5 or \
                    abs(coor_candidates[cdx_1][1] - coor_candidates[cdx_2][1]) > 0.5:
                    return ('TBD', ('near', candidates))
        return ('GOOD', candidates[0])
    # if not matched, check if the word is abbreviation
    elif len(candidates) == 0:
        candidates = get_abbr_candidate(set_oneword)
        if candidates:
            return ('TBD', ('abbr', candidates))
    return ('BAD', None)

def check_geoinfo(geohint):
    for i in range(0, 3):
        if len(geohint[i]):
            geoinfo = check_raw_word(geohint[i])
            if geoinfo[0] != 'BAD':
                return geoinfo
    return ('BAD', None)

# iterate all routers
for idx in range(TEMPLATE_NUM):
    ROUTER_BIN = f'{TEMPLATE_RESULT_DIR}/template_{idx}.pkl'
    for jdx, one_router in enumerate(pickle.load(open(ROUTER_BIN, 'rb'))):
        # print(jdx)
        geohint = one_router['geohint']
        result = check_geoinfo(one_router['geohint'])
        if result[0] == 'BAD':
            list_bad_routers.append(one_router)
        elif result[0] == 'TBD':
            one_router['candiates'] = result[1][1]
            one_router['type'] = result[1][0]
            list_tbd_routers.append(one_router)
        elif result[0] == 'GOOD':
            city_info = result[1][0]
            one_router['coordinate'] = city_info[0]
            one_router['country_code'] = city_info[1]
            one_router['city'] = city_info[3]
            list_good_routers.append(one_router)
            # print(one_router)
# print the count of routers
print(f'good routers: {len(list_good_routers)}')
pickle.dump(list_good_routers, open(f'{DST_FILES_DIR}/list_good_routers.bin', 'wb'))
print(f'tbd routers: {len(list_tbd_routers)}')
pickle.dump(list_tbd_routers, open(f'{DST_FILES_DIR}/list_tbd_routers.bin', 'wb'))
print(f'bad routers: {len(list_bad_routers)}')
pickle.dump(list_bad_routers, open(f'{DST_FILES_DIR}/list_bad_routers.bin', 'wb'))
