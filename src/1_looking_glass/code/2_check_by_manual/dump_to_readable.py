# dump the pkl file from the previous step to a readable format

import pickle

SRC_BIN_DIR = '../1_filter_by_template/result'
FILE_FORMAT = 'template_{}.pkl'

for idx in range(0, 5):
    ROUTER_BIN = f'{SRC_BIN_DIR}/{FILE_FORMAT.format(idx)}'
    for jdx, one_router in enumerate(pickle.load(open(ROUTER_BIN, 'rb'))):
        print(one_router)
        break
    break