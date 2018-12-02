import pymysql
import sys
from decimal import Decimal
import boto3
import random
import datetime
from env_vars import *


cw = boto3.client('cloudwatch')

def save_events(event):
    """
    This function fetches content from mysql RDS instance
    """
    result = []
    conn = pymysql.connect(rds_host, user=name, passwd=password, db=db_name, connect_timeout=5)
    with conn.cursor() as cur:
        #cur.execute("""SELECT * from Persons;""")
        cur.execute("""SELECT 
    t.TABLE_SCHEMA,
    t.TABLE_NAME,
    `AUTO_INCREMENT` current_id, 
    if(m.max_id =-1,'18446744073709551615',m.max_id) max_id, 
    (m.max_id - `AUTO_INCREMENT`) free_id,
    (`AUTO_INCREMENT`/m.max_id*100) percent_used
FROM  
    INFORMATION_SCHEMA.TABLES t
    INNER JOIN 
    (
    SELECT 
        TABLE_NAME,
        TABLE_SCHEMA,
        CASE 
            WHEN COLUMN_TYPE LIKE "tinyint%unsigned"    THEN 255
            WHEN COLUMN_TYPE LIKE "tinyint%"    THEN 127
            WHEN COLUMN_TYPE LIKE "smallint%unsigned"   THEN 65535
            WHEN COLUMN_TYPE LIKE "smallint%"   THEN 32767
            WHEN COLUMN_TYPE LIKE "mediumint%unsigned"  THEN 16777215
            WHEN COLUMN_TYPE LIKE "mediumint%"  THEN 8388607
            WHEN COLUMN_TYPE LIKE "int%unsigned"    THEN 4294967295
            WHEN COLUMN_TYPE LIKE "int%"    THEN 2147483647
            WHEN COLUMN_TYPE LIKE "bigint%unsigned" THEN 18446744073709551615
            WHEN COLUMN_TYPE LIKE "bigint%" THEN 9223372036854775807
        END max_id
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE extra like "%auto_increment%" 
    ) m
    on 
        t.TABLE_NAME = m.TABLE_NAME
        AND t.TABLE_SCHEMA = m.TABLE_SCHEMA""")
        conn.commit()
        cur.close()
        for row in cur:
            result.append(list(row))
        print "Data from RDS..."
        #print result
        for elem in result:
	        if elem[5] > max_auto_increment_threshold:
        		print elem
        		print "SCHEMA " + elem[0] + " WITH TABLE" + " - " + elem[1] + "HAS AN AUTO-INCREMENT CONSUMPTION MORE THEN THE SET LIMIT, IT IS CRITICAL!!!"
        		print "Auto-increment % consumption: "
        		print elem[5]
        		val = str(elem[5])
        		print "Critical"
        		cw_put_metric_data(val, rds_host, db_name)
        		
def cw_put_metric_data(value, host, db):
    print "metric_hi"
    cw.put_metric_data(Namespace='Auto_increment',
                       MetricData=[
                           {
                               'MetricName': "Table Count",
                               'Timestamp': datetime.datetime.now(),
                               
                               'Unit': 'Count',
                               'Dimensions': [
                                   {
                                       'Name': 'Consumption',
                                       'Value': value
                                   },
                                   
                               ],
                           },
                       ])
    
def main(event, context):
    save_events(event)

    
        