import serial
import serial.tools.list_ports
import numpy as np
import urllib.request
import time
import sys
import telegram_send

# pip install pymqtt
import paho.mqtt.client as mqtt

port_DEVICE = 'hc-05'
interval = 0.1

class Bridge():

    def setupSerial(self):
        # open serial port
        self.ser = None
        print("list of available ports: ")

        ports = serial.tools.list_ports.comports()
        self.portname = None
        for port in ports:
            #print(port.device)
            #print(port.description)
            if port_DEVICE in port.device.lower():
                self.portname = port.device

        self.inbuffer = []
    
        try:
            self.ser = serial.Serial(self.portname, 9600, timeout=1)
            return 1
        except:
            return 0

        #self.ser.open()

    def setupMQTT(self):
        self.clientMQTT = mqtt.Client()
        self.clientMQTT.on_connect = self.on_connect
        self.clientMQTT.on_message = self.on_message
        print("connecting...")
        self.clientMQTT.connect("127.0.0.1", 1883, 60)

        self.clientMQTT.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        self.clientMQTT.subscribe("light")

    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))
        if msg.topic == 'light':
            self.ser.write(msg.payload)

    def setup(self):
        self.setupSerial()
        self.setupMQTT()

    def loop(self):
        # infinite loop for serial managing
        ts = time.time()
        f = 1
        while(True):
            # look for a byte from serial
            if f == 1:
                    if self.ser is not None:
                      
                        # data available from the serial port
                        try:

                            lastchar = self.ser.read(1)
                        except:
                            f = 0
                        if lastchar == b'\xfe': #EOL
                            print("\nValue received")
                            self.useData()
                            self.inbuffer =[]
                        else:
                            # append
                            self.inbuffer.append(lastchar)
                
            
            else:
                if time.time() - ts > interval:
                    ts = time.time()
                    self.clientMQTT.publish('test/1','scappato')
                    print('scappato')
                    telegram_send.send(messages=['scappato'])
                    if self.setupSerial() == 1:
                        f = 1

    def useData(self):
        # I have received a line from the serial port. I can use it
        if len(self.inbuffer)<3:   # at least header, size, footer
            return False
        # split parts
        if self.inbuffer[0] != b'\xff':
            return False

        
        val = int.from_bytes(self.inbuffer[2], byteorder='little')
        strval = "Sensor: %d " % (val)
        print(strval)
        self.clientMQTT.publish('sensor','{:d}'.format(val))

if __name__ == '__main__':
    br=Bridge()
    br.setup()
    br.loop()

