# after manual check, merge the checked results to the previous results
import jsonlines as jl
import pickle
from string import digits
# base geoinfo data structure
GEOBIN_DIR = '../../../0_location_hint/pickle_bin'
dict_city_by_name = pickle.load(open(f'{GEOBIN_DIR}/dict_city_by_name.bin', 'rb'))
dict_hasspace_city = pickle.load(open(f'{GEOBIN_DIR}/dict_hasspace_city.bin', 'rb'))
dict_iata_code = pickle.load(open(f'{GEOBIN_DIR}/dict_iata_code.bin', 'rb'))
dict_city_by_country = pickle.load(open(f'{GEOBIN_DIR}/dict_city_by_country.bin', 'rb'))
dict_city_alter_name = pickle.load(open(f'{GEOBIN_DIR}/dict_city_alter_to_name.bin', 'rb'))


def check_geoinfo(one_router):
    geohint = one_router['geohint']
    country_code = one_router['country_code']
    candidates = dict_city_by_country[country_code]
    city = one_router['city']
    # find the corresponding geoinfo
    try:
        candidate = candidates[city]
        one_router['coordinate'] = candidate[0]
        return True
    except Exception as e:
        return False


final_routers_list = []
# load the `bad_routers.jsonl`, re-geolocation the routers, and merge the results to the previous results
with open('./result/bad_routers.jsonl') as bad_routers:
    jl_reader = jl.Reader(bad_routers)
    # re-geolocation the router
    for one_router in jl_reader:
        res = check_geoinfo(one_router)
        if res:
            final_routers_list.append(one_router)
        # merge the results to the previous results

# TODO: near city process

# merge with checked results
with open('./result/checked_routers.jsonl') as checked_routers:
    jl_reader = jl.Reader(checked_routers)
    for one_router in jl_reader:
        final_routers_list.append(one_router)

# sort by city name, then print to file
final_routers_list.sort(key=lambda x: x['city'])
with open('./result/list_good_routers.jsonl', 'w') as final_routers:
    jl_writer = jl.Writer(final_routers)
    for one_router in final_routers_list:
        jl_writer.write(one_router)
    jl_writer.close()
with open('./result/list_good_routers.bin', 'wb') as final_routers:
    pickle.dump(final_routers_list, final_routers)