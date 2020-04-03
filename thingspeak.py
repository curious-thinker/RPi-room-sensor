import requests
import time
import pandas as pd
import sqlite3

api_key=''

con = sqlite3.connect("core/core.db")
df = pd.read_sql_query("SELECT * from sensordata", con)


def sender():
    data = df.tail(1).values.astype(str)
    temp = data[0][2]
    humidity = data[0][3]
    cotwo = data[0][4]
    tvoc = data[0][5]

    payload = {'api_key': api_key, 'field1': temp, 'field2': humidity, 'field3': cotwo, 'field4': tvoc}
    r = requests.post('https://api.thingspeak.com/update', params=payload)
    print("Result: " + str(r.text))
    print("Payload: " + "Temp: " + temp + " humidity: " + humidity + " CO2: " + cotwo + " TVOC: " + tvoc)
    time.sleep(16)

def main():

    while True:
        sender()

if __name__ == '__main__':
    main()

