import os
import pickle

MACHINE_IPS = ['39.105.58.249', '182.92.165.113']
# maybe the machine uses its private ip
PRIVATE_IPS = ['172.29.45.139', '172.29.45.143']

FORMER_RESULT_DIR = '../4_filter_by_api/result'
LG_LIST = pickle.load(open(f'{FORMER_RESULT_DIR}/list_good_routers.bin', 'rb'))

RESULT_DIR = f'./result'

LG_DIR = '../../'
DST_DIR = f'{LG_DIR}/pickle_bin/'
os.system(f'mkdir -p {DST_DIR}')
