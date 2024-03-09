# here we update the valid geocam data to the database

import pymysql
import base64
import pickle as pkl

DST_DIR = '../../pickle_bin/'

# using private IP address
MYSQL_HOST = '172.29.45.143'
USER = 'root'
PASSWD = 'netsys_galileo'
DATABASE = 'galileo'
TABLE_NAME = 'lookingglass'
PORT = 3309

# Connect to the database
connection = pymysql.connect(host=MYSQL_HOST,
                            port=PORT,
                            user=USER,
                            password=PASSWD,
                            db=DATABASE,
                            charset='utf8mb4',
                            cursorclass=pymysql.cursors.DictCursor)

'''
build the table if not exists
ip: int PRIMARY KEY
lat: float
lon: float
city:varchar 40
website:varcahr 70
'''
with connection.cursor() as cursor:
    # Create a new record
    sql = f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} (ip INT UNSIGNED PRIMARY KEY, lat FLOAT, lon FLOAT, city VARCHAR(40), website VARCHAR(70))"
    cursor.execute(sql)
    # query the table
    sql = f"SELECT * FROM {TABLE_NAME}"
    cursor.execute(sql)
    result = cursor.fetchall()
    print(result[0:100])

dict_lg_info = pkl.load(open(f'{DST_DIR}/dict_lg_info.bin', 'rb'))

# add the valid geocam data to the database
with connection.cursor() as cursor:
    for ip, info in dict_lg_info.items():
        # Create a new record
        lat = info['coordinate'][0]
        lon = info['coordinate'][1]
        city = info['city']
        website = info['website']
        website_base64 = base64.b64encode(website.encode('utf-8')).decode('utf-8')
        ip_int = sum([256**j*int(i) for j,i in enumerate(ip.split('.')[::-1])])
        sql = f"INSERT INTO {TABLE_NAME} (ip, lat, lon, city, website) VALUES ({ip_int}, {lat}, {lon} , '{city}', '{website_base64}')"
        try:
            cursor.execute(sql)
        except Exception as e:
            print(e)
# commit result
connection.commit()

print("Finish updating the valid landmark data to the database.")