# here we update the valid geocam data to the database

import pymysql
import pandas as pd

# using private IP address
MYSQL_HOST = '172.29.45.143'
# MYSQL_HOST = '182.92.82.138'
USER = 'root'
PASSWD = 'netsys_galileo'
DATABASE = 'galileo'
TABLE_NAME = 'endpoint'
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
'''
with connection.cursor() as cursor:
    # Create a new record
    sql = f"CREATE TABLE IF NOT EXISTS {TABLE_NAME} (ip INT UNSIGNED PRIMARY KEY, lat FLOAT, lon FLOAT)"
    cursor.execute(sql)
    # query the table
    sql = f"SELECT * FROM {TABLE_NAME}"
    cursor.execute(sql)
    result = cursor.fetchall()
    print(result[0:100])

# read from the csv file
results = [
    pd.read_csv('../data/0_insecam_good.csv', header=None),
    pd.read_csv('../data/0_pictimo_good.csv', header=None)
]

for result in results:
    result.columns = ['ip', 'lat', 'lon']
    # add the valid geocam data to the database
    with connection.cursor() as cursor:
        for index, row in result.iterrows():
            # Create a new record
            ip = row['ip']
            lat = row['lat']
            lon = row['lon']
            ip_int = sum([256**j*int(i) for j,i in enumerate(ip.split('.')[::-1])])
            sql = f"INSERT INTO {TABLE_NAME} (ip, lat, lon) VALUES ({ip_int}, {lat}, {lon})"
            try:
                cursor.execute(sql)
            except Exception as e:
                print(e)
# commit result
connection.commit()
print("Finish updating the valid geocam data to the database.")