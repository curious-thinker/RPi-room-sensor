#!/usr/bin/env python3

'''

This is the main executable for Project Exhale

##################################################

Programmer: Steve Manzo
Contact: smmanzo@gmail.com
Version: 0.1
Updated: 3/27/2020


##################################################

The purpose of this program to control a custom PiHat that records
CO2, VOCS, Temperature and Humidity.  

The sensor the collect CO2 and VOCS is the 
Adafruit SPG30 https://circuitpython.readthedocs.io/projects/sgp30/en/latest/api.html

The sensor to collect Temperature and Humidity is the
Adafruit SHT31D https://circuitpython.readthedocs.io/projects/sht31d/en/latest/api.html

This programming collects the data from these sensors, the humidity and temperature are used
in a CO2 correction factor for the SPG30. On the Pi hat there are also three LEDs, green, yellow 
and red.  These LEDS indicate the realtive levels of C02 and VOCs in the room, when these levels begin
to reach dangerous levels the colors change accordingly.  Green indicates good air quality, while yellow is a 
warning and red indicates dangerous levels of either CO2 or VOCS.

'''

import busio
import numpy as np
import RPi.GPIO as GPIO

import adafruit_sgp30
import adafruit_sht31d
import board
import os
import sys
import time

from db import Session, engine, Base
from models import SensorData



def rh_to_mc(temp, rh):

    # vp_water uses the  August-Roche-Magnus equation
    # https://en.wikipedia.org/wiki/Vapour_pressure_of_water
    vp_water = 1000 * (0.61094 * np.exp((17.625 * temp) / (temp + 243.04)))
    e = vp_water * (rh / 100)
    mass_conc = (e / (461.5 * (temp + 273.15))) * 1000

    return mass_conc

class LedState(object):
    def __init__(self):
        # GPIO LEDs 17 = Green, 18 = yellow, 27 = red
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(17,GPIO.OUT)
        GPIO.setup(18,GPIO.OUT)
        GPIO.setup(27,GPIO.OUT)

    def self_test(self):
        GPIO.output(17,GPIO.HIGH)
        time.sleep(1)
        GPIO.output(17,GPIO.LOW)
        time.sleep(0.5)
        GPIO.output(18, GPIO.HIGH)
        time.sleep(1)
        GPIO.output(18,GPIO.LOW)
        time.sleep(0.5)
        GPIO.output(27,GPIO.HIGH)
        time.sleep(1)
        GPIO.output(27,GPIO.LOW)
    
    def set_state(self, cotwo, voc):
        if cotwo <= 999 and voc <= 199:
            GPIO.output(17, GPIO.HIGH)
            GPIO.output(18, GPIO.LOW)
            GPIO.output(27, GPIO.LOW)
        elif 2000 > cotwo > 1000 or 500 > voc > 200:
            GPIO.output(17, GPIO.LOW)
            GPIO.output(18, GPIO.HIGH)
            GPIO.output(27, GPIO.LOW)
        elif cotwo >= 2001 or voc >= 501:
            GPIO.output(17, GPIO.LOW)
            GPIO.output(18, GPIO.LOW)
            GPIO.output(27, GPIO.HIGH)
    
    def shutdown(self):
        GPIO.output(17, GPIO.LOW)
        GPIO.output(18, GPIO.LOW)
        GPIO.output(27, GPIO.LOW)
    
i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)

# Create library object on our I2C port
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)
sensor = adafruit_sht31d.SHT31D(i2c)

print("SGP30 serial #", [hex(i) for i in sgp30.serial])

sgp30.iaq_init()
sgp30.set_iaq_baseline(0x8973, 0x8aae)


def main():

    elapsed_sec = 0
    loopcount = 0

    while True:

        print("\nTemperature: %0.1f C" % sensor.temperature)
        print("Humidity: %0.1f %%" % sensor.relative_humidity)
        t = sensor.temperature
        rh = sensor.relative_humidity
        loopcount += 1
        time.sleep(2)
        # every 10 passes turn on the heater for 1 second
        if loopcount == 10:
            loopcount = 0
            sensor.heater = True
            print("Sensor Heater status =", sensor.heater)
            time.sleep(1)
            sensor.heater = False
            print("Sensor Heater status =", sensor.heater)

        mass_conc = rh_to_mc(temp=t, rh=rh)
        sgp30.set_iaq_humidity(mass_conc)

        print("eCO2 = %d ppm \t TVOC = %d ppb" % (sgp30.eCO2, sgp30.TVOC))
        co2 = sgp30.eCO2
        voc = sgp30.TVOC
        led.set_state(cotwo=sgp30.eCO2, voc=sgp30.TVOC)

        time.sleep(1)
        elapsed_sec += 1
        if elapsed_sec > 10:
            elapsed_sec = 0
            print("**** Baseline values: eCO2 = 0x%x, TVOC = 0x%x"
                  % (sgp30.baseline_eCO2, sgp30.baseline_TVOC))

        data = SensorData(temperature=t, humidity=rh, carbondioxide=co2, voc=voc)
        session.add(data)
        session.commit()
        session.close()
        #time.sleep(10)

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    session = Session()
    try:
        led = LedState()
        led.self_test()
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            # System is off
            print("Caught Keyboard exit, gracefully shutting down")
            sensor.heater = False
            led.shutdown()
            sys.exit(0)


        except SystemExit:
            # System is off
            print("Caught keyboard exit, gracefully shutting down")
            sensor.heater = False
            led.shutdown()
            os._exit(0)
