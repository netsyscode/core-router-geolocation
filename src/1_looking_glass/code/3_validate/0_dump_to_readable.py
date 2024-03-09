# dump the pkl file from the previous step to a readable format

import jsonlines as jl
import pickle

SRC_BIN_DIR = '../2_filter_by_geoinfo/result'
DST_JSON_DIR = './result'
GOOD_RES_FILE = 'list_good_routers'
TBD_RES_FILE = 'list_tbd_routers'

# GOOD_RES first
with open(f'{SRC_BIN_DIR}/{GOOD_RES_FILE}{".bin"}', 'rb') as f:
    good_res = pickle.load(f)
# write per router with jsonlines
with open(f'{DST_JSON_DIR}/{GOOD_RES_FILE}{".jsonl"}', 'w') as f:
    for one_router in good_res:
        jl.Writer(f).write(one_router)
    
# TBD_RES next
with open(f'{SRC_BIN_DIR}/{TBD_RES_FILE}{".bin"}', 'rb') as f:
    tbd_res = pickle.load(f)
# split by 'type' attribute
tbd_by_abbr = []
tbd_by_dist = []
for one_router in tbd_res:
    if one_router['type'] == 'near':
        tbd_by_dist.append(one_router)
    else:
        tbd_by_abbr.append(one_router)
with open(f'{DST_JSON_DIR}/{TBD_RES_FILE}{"_abbr.jsonl"}', 'w') as f:
    for one_router in tbd_by_abbr:
        jl.Writer(f).write(one_router)
with open(f'{DST_JSON_DIR}/{TBD_RES_FILE}{"_dist.jsonl"}', 'w') as f:
    for one_router in tbd_by_dist:
        jl.Writer(f).write(one_router)