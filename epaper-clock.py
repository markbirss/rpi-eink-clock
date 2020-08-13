#!/usr/bin/env python3

##
# epaper-clock.py
#
# Copyright (C) Emanuele Goldoni 2020
#
# original author: Jukka Aittola (jaittola(at)iki.fi) 2017
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
##


import epd2in7
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

import RPi.GPIO as GPIO

from datetime import datetime
import time
import locale
import subprocess
import psutil
import socket
#import sys
import os

LOCALE="it_IT.UTF8"
DATEFORMAT = "%a %x"
TIMEFORMAT = "%H:%M"
FONT = '/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf'
BOUNCETIME = 500

PIN_BTN1 = 5
PIN_BTN2 = 6
PIN_BTN3 = 13
PIN_BTN4 = 19

DISPMODE_LOGO = 1
DISPMODE_SYSSTATS = 2
DISPMODE_CLOCK = 3
DISPMODE_UNDEF = 4

class Fonts:
    def __init__(self, timefont_size, datefont_size, infofont_size):
        self.timefont = ImageFont.truetype(FONT, timefont_size)
        self.datefont = ImageFont.truetype(FONT, datefont_size)
        self.infofont = ImageFont.truetype(FONT, infofont_size)

class Display:
    
    epd = None
    fonts = None
    mode = DISPMODE_LOGO
    
    def __init__(self):
        locale.setlocale(locale.LC_ALL, LOCALE)
        self.fonts = Fonts(timefont_size = 75, datefont_size = 26, infofont_size = 18)
        
        self.epd = epd2in7.EPD()
        self.epd.init()
        self.read_buttons()

    def start(self):
        while True:
            if DISPMODE_SYSSTATS == self.mode:
                self.draw_system_data()
            elif DISPMODE_CLOCK == self.mode:
                self.draw_clock_data()
            else:
                self.draw_rpi_logo()
            self.sleep1min()
    
    def sleep1min(self):
        now = datetime.now()
        seconds_until_next_minute = 60 - now.time().second
        time.sleep(seconds_until_next_minute)

    def draw_rpi_logo(self):
        Himage = Image.open(os.path.join('.', 'raspberry.bmp'))
        self.epd.display(self.epd.getbuffer(Himage))


    def draw_clock_data(self):
        datetime_now = datetime.now()
        datestring = datetime_now.strftime(DATEFORMAT).capitalize()
        timestring = datetime_now.strftime(TIMEFORMAT)

        Limage = Image.new('1', (self.epd.height, self.epd.width), 255)  # 255: clear the frame
        draw = ImageDraw.Draw(Limage)
        draw.text((20, 20), timestring, font = self.fonts.timefont, fill = 0)
        draw.text((20, 100), datestring, font = self.fonts.datefont, fill = 0)
        self.epd.display(self.epd.getbuffer(Limage))

    def draw_system_data(self):
        corestring = 'CPU freq: ' + str(psutil.cpu_freq().current) + ' MHz';
        usagestring = 'CPU usage: ' + str(psutil.cpu_percent());
        tempstring = 'CPU temp. ' + str(round(psutil.sensors_temperatures(fahrenheit=False)['cpu_thermal'][0].current)) + ' \u00b0C';
        memstring = 'Free RAM: ' + str(int(psutil.virtual_memory().available/(1024*1024))) + ' MiB';
        psstring = 'Running ps: ' + str(len(psutil.pids()))
                
        #iflist = [name for name in psutil.net_if_addrs().keys()]
        ifaddresses = [ifname+' '+str(ip.address) for ifname in psutil.net_if_addrs().keys() for ip in psutil.net_if_addrs()[ifname] if ip.family == socket.AF_INET]
        
        sysstring = corestring + '\n' + usagestring + '\n' + tempstring + '\n' + memstring + '\n' + psstring
        netstring = '\n'.join(ifaddresses)

        Limage = Image.new('1', (self.epd.height, self.epd.width), 255)
        draw = ImageDraw.Draw(Limage)
        draw.text((10, 10), sysstring, font = self.fonts.infofont, fill = 0)
        draw.text((10, 110), netstring, font = self.fonts.infofont, fill = 0)
        self.epd.display(self.epd.getbuffer(Limage))

    def read_buttons(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(PIN_BTN1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(PIN_BTN1, GPIO.FALLING, callback=self.button_pressed, bouncetime=BOUNCETIME)
        GPIO.setup(PIN_BTN2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(PIN_BTN2, GPIO.FALLING, callback=self.button_pressed, bouncetime=BOUNCETIME)
        GPIO.setup(PIN_BTN3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(PIN_BTN3, GPIO.FALLING, callback=self.button_pressed, bouncetime=BOUNCETIME)
        GPIO.setup(PIN_BTN4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(PIN_BTN4, GPIO.FALLING, callback=self.button_pressed, bouncetime=BOUNCETIME)

    def button_pressed(self, pin):
        #print("Button %d was pressed..." % pin)
        if PIN_BTN1 == pin:
            self.draw_rpi_logo()
            self.mode = DISPMODE_LOGO
        elif PIN_BTN2 == pin:
            self.draw_system_data()
            self.mode = DISPMODE_SYSSTATS
        elif PIN_BTN3 == pin:
            self.draw_clock_data()
            self.mode = DISPMODE_CLOCK
        elif PIN_BTN4 == pin:
            self.mode = DISPMODE_UNDEF
            print("Shutting down system...")
            #subprocess.call(["sudo", "poweroff"])

if __name__ == '__main__':
    display = Display()
    display.start()
