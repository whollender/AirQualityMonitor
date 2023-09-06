import time
import board
import busio
from digitalio import DigitalInOut, Direction, Pull
from adafruit_pm25.i2c import PM25_I2C
import numpy as np

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

    print(f'\n\n\n\n\n')
    print(f'AQI: {aqiMsgs[aqiCatIdx]} ({aqiVal})')
    print(f'Ten minute avg PM2.5 concentration: {tenMinAvg}')
    print(f'Number of data points {len(data)}')
    print(f'Last reading: {data[-1]}')
