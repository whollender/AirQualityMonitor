import time
import board
import busio
from digitalio import DigitalInOut, Direction, Pull
from adafruit_pm25.i2c import PM25_I2C
import numpy as np
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import collections

# Breakpoints from AirNow.gov's calculator source
pm25ConcBreakpoints = np.array([0,12.1,35.5,55.5,150.5,250.5,350.5,500.5])
aqiBreakpoints = np.array([0,50,100,150,200,300,400,500])
aqiMsgs = ['Good','Moderate','Unhealthy For Sensitive Groups','Unhealthy','Very Unhealthy','Hazardous','Hazardous']


reset_pin = None

# Create library object, use 'slow' 100KHz frequency!
i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
# Connect to a PM2.5 sensor over I2C
pm25 = PM25_I2C(i2c, reset_pin)

print("Found PM2.5 sensor, reading data...")

data = []

raw10MinAvgArray = collections.deque(maxlen=1000)
aqiValArray = collections.deque(maxlen=1000)
aqiCatIndexArray = collections.deque(maxlen=1000)
dateTimeArray = collections.deque(maxlen=1000)

idx = 0

while True:
    time.sleep(1)

    try:
        aqdata = pm25.read()
        # print(aqdata)
        data.append(aqdata["pm25 env"])

        # Make sure we only have 10 minutes of data at any one time
        while(len(data) > 600):
            data.pop(0)

    except RuntimeError:
        print("Unable to read from sensor, retrying...")
        continue


    # This rounds the avg concentration to the nearest tenth
    tenMinAvg = np.floor(10*np.mean(np.array(data))) / 10

    # calculate AQI
    aqiVal = np.round(np.interp(tenMinAvg,pm25ConcBreakpoints,aqiBreakpoints))
    aqiCatIdx = 0 if aqiVal < 1 else np.max(np.nonzero(aqiVal > aqiBreakpoints))

    idx = idx+1
    if(idx > 599):
        # Generate things
        idx = 0
        dateTimeArray.append(datetime.datetime.now())
        raw10MinAvgArray.append(tenMinAvg)
        aqiValArray.append(aqiVal)
        aqiCatIndexArray.append(aqiCatIdx)

        fig,ax = plt.subplots(1,1)
        ax.plot(dateTimeArray,raw10MinAvgArray, linewidth=2)
        ax.set_ylabel('PM2.5')
        ax.set_title('PM2.5 concentration, 10 minute rolling average')
        plt.savefig('/var/www/html/airquality/raw.png', format='png', bbox_inches="tight")
        plt.close()

        fig,ax = plt.subplots(1,1)
        ax.plot(dateTimeArray,aqiValArray, linewidth=2)
        ax.set_ylabel('AQI')
        ax.set_title('Air quality index from PM2.5 concentration')
        plt.savefig('/var/www/html/airquality/aqival.png', format='png', bbox_inches="tight")
        plt.close()

        # write a new index.html with files updated to prevent caching issues
        indexHtml = open('/var/www/html/airquality/index.html', 'w', encoding='utf-8')
        indexHtml.write('<!DOCTYPE html>\n<html>\n<body>\n')
        indexHtml.write(f'Current AQI is {aqiMsgs[aqiCatIdx]}<br>\n')
        indexHtml.write(f'<img src="raw.png?{time.time()}"><br>\n')
        indexHtml.write(f'<img src="aqival.png?{time.time()}"><br>\n')
        indexHtml.write(f'Last updated: {datetime.datetime.now()}<br>\n')
        indexHtml.write(f'</body>\n</html>')
        indexHtml.close()
