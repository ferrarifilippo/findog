### author: Roberto Vezzani

from os import truncate
import serial
import serial.tools.list_ports
import numpy as np
import requests
import time


### CHANGE THIS WITH YOURS INFORMATION ###

ADAFRUIT_IO_USERNAME = "ffes2021"
ADAFRUIT_IO_KEY = "aio_QxkL07wcMUHN8WRS2EH2zA5wOXWD"

class AFBridge():


    def setupSerial(self):
        # open serial port
        self.ser = None
        print("list of available ports: ")

        ports = serial.tools.list_ports.comports()
        self.portname=None
        for port in ports:
            print (port.device)
            print (port.description)
            if 'usbmodem' in port.device.lower():
                self.portname = port.device
        #print ("connecting to " + self.portname)
        self.inbuffer = []
        
        if self.portname is  None:
            print("nessuna connessione")
            self.ser = None
            return 0
        else:
            self.ser = serial.Serial(self.portname, 9600, timeout=0)
            return 1
            

        # self.ser.open()

        # internal input buffer from serial
        


    def setup(self):

        self.setupSerial()

    def loop(self):
        # infinite loop for serial managing
        #
        
        ts = time.time()
        f = 1
        while (True):
            if f == 1:
            # look for a byte from serialù
            #if ts - lasttime > 1:
                try:
                    if not self.ser is None:

                        if self.ser.in_waiting > 0:
                            # data available from the serial port
                            lastchar = self.ser.read(1)

                            if lastchar == b'#':  # EOL
                                print("\nValue received")
                                self.useData()
                                self.inbuffer = []
                            else:
                                # append
                                self.inbuffer.append(lastchar)
                except:
                    f = 0
            else:
                if time.time() - ts > 2:
                    ts = time.time()
                    self.inbuffer = [b'*',b'1',b'0',b'#']
                    self.useData()
                    if self.setupSerial() == 1:
                        f = 1
                    #self.setup()
                # get from feed each 2 seconds
               # lasttime = time.time()
                '''if ts-lasttime>2:

                feedname = 'elab'
                headers = {'X-AIO-Key': ADAFRUIT_IO_KEY}
                url = 'https://io.adafruit.com/api/v2/{}/feeds/{}/data/last'.format(ADAFRUIT_IO_USERNAME, feedname)
                print(url)
                myGET = requests.get(url, headers=headers)
                responseJsonBody= myGET.json()
                val = responseJsonBody.get('value',None)

                print(val)

                #if val == '1':
                    #self.ser.write(b'ON')

                #if val == '0':
                 #   self.ser.write(b'OFF')



                lasttime = time.time()'''



    def useData(self):
        # I have received a line from the serial port. I can use it
        if len(self.inbuffer) < 3:  # at least header, size, footer
            return False
        # split parts
        if self.inbuffer[0] != b'*':
            return False

        numval = int.from_bytes(self.inbuffer[1], byteorder='little')
        if numval>0:
            # uso solo il primo valore
            i=0
            val = int.from_bytes(self.inbuffer[i + 2], byteorder='little')
            strval = "Sensor %d: %d " % (i, val)
            print(strval)

            mypostdata = {'value': val}
            feedname = 'sensors'
            headers = {'X-AIO-Key': ADAFRUIT_IO_KEY}
            url = 'https://io.adafruit.com/api/v2/{}/feeds/{}/data'.format(ADAFRUIT_IO_USERNAME,feedname)
            print (url)
            myPOST = requests.post(url, data = mypostdata, headers=headers)
            print(myPOST.json())




if __name__ == '__main__':
    br=AFBridge()
    br.setup()
    br.loop()

