import json
from cgitb import text
from xmlrpc.client import Boolean
import serial
import serial.tools.list_ports
import numpy as np
import urllib.request
import time
import sys
import sqlite3
from flask_sqlalchemy import SQLAlchemy
import requests
import hashlib
from getpass import getpass

port_DEVICE = 'esp32'
# port_DEVICE = '5'
interval = 1
# server_ip = "172.20.10.11:5000"
server_ip = "172.20.10.13:5000"


# server_ip = "192.168.1.21:5000"


class Bridge():
    def __init__(self, uuid):
        self.isHome = None
        self.inbuffer = []
        self.ser = None
        self.portname = None
        self.my_uuid = uuid
        self.bridge_paired = False

    def setupSerial(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port_DEVICE in port.device.lower():
                self.portname = port.device

        try:
            self.ser = serial.Serial(self.portname, 9600, timeout=1)
            print("Collare connesso correttamente")
            self.isHome = True
            self.bridge_paired = (requests.get(f'http://{server_ip}/get_dog',
                                               params={'uuid': self.my_uuid, 'attribute': 'bridge_paired'})).text
            self.change_state(uuid=self.my_uuid, myDog=True)
            return True
        except:
            return False

    def loop(self):
        ts = time.time()
        # self.f = 1
        # self.paired = "False" #debug
        while True:
            if self.isHome:
                if self.ser is not None:

                    if self.bridge_paired == "False":
                        print("Connessione iniziale collare")
                        print(
                            "Non dimenticare di effettuare il login su telegram per non perdere neanche un messaggio utilizzando il comando '/start' !")
                        self.ser.write((self.my_uuid + "\n").encode())
                        self.bridge_paired = True
                        requests.post(f'http://{server_ip}/set_dog',
                                      data={'uuid': self.my_uuid, 'attribute': 'bridge_paired', 'val': 'True'})

                    # if time.time() - ts > interval:
                    # ts = time.time()
                    # print(self.inbuffer)
                    # if len(self.inbuffer) < 4:
                    try:
                        lastchar = self.ser.read(1)
                        # print(lastchar)

                        if lastchar == b'\xfe':
                            # print("\nValue received " + str(self.inbuffer))
                            self.message_handler()
                            self.inbuffer = []

                        elif lastchar != b'':
                            self.inbuffer.append(lastchar)

                    except serial.SerialException:
                        print('Il collare si è scollegato')
                        self.disconnection()

                # else:
                #     self.disconnection()
            else:
                if time.time() - ts > interval:
                    ts = time.time()
                    self.setupSerial()

    def disconnection(self):
        self.inbuffer = []
        self.isHome = False
        self.ser.close()
        self.change_state(uuid=self.my_uuid, myDog=True)

    def change_state(self, uuid, myDog: Boolean):
        state = requests.get(f'http://{server_ip}/get_dog', params={'uuid': uuid, 'attribute': 'state'})

        if myDog:
            if state.text == 'A':
                # Bot telegram che chiede e aggiorna lo stato in automatico

                requests.get(f'http://{server_ip}/walk_telegram', params={'uuid': uuid})

            elif state.text == 'P' or state.text == 'S' or state.text == 'T' or state.text == 'W':
                requests.post(f'http://{server_ip}/set_dog', data={'uuid': uuid, 'attribute': 'state', 'val': 'A'})

        else:
            requests.post(f'http://{server_ip}/set_dog', data={'uuid': uuid, 'attribute': 'state', 'val': 'T'})
            requests.get(f'http://{server_ip}/dog_found_telegram', params={'other_uuid': uuid, "my_uuid": self.my_uuid})

    def message_handler(self):
        if len(self.inbuffer) < 3:
            return

        message_type = self.inbuffer.pop(0)

        # messaggio in arrivo da un altro cane
        if message_type == b'\xff':
            uuid = []
            for c in self.inbuffer:
                uuid.append(c.decode('utf-8'))

            uuid = "".join(uuid)
            print(f"UUID CANE PERSO : {uuid}")
            self.change_state(uuid=uuid, myDog=False)

        # messaggio in arrivo dal mio cane 
        elif message_type == b'\xfa':

            '''
            self.my_uuid = []
            for c in self.inbuffer:
                self.my_uuid.append(c.decode('utf-8'))

            self.my_uuid = "".join(self.my_uuid)
            print(f"MIO UUID : {self.my_uuid}")
            
            if not self.isHome:
                # self.change_state(uuid=self.my_uuid, myDog=True)
                requests.post(f'http://{server_ip}/set_dog', data={'uuid': self.my_uuid, 'attribute': 'state', 'val': 'A'})
                self.isHome = True
                '''


def greetings():
    print("Benvenuto nel manager dei collari FINDOG")
    print("Email")
    email = input()
    password = getpass()
    password = hashlib.sha256(password.encode()).hexdigest()
    user = requests.get(f'http://{server_ip}/bridge_login', params={'email': email, 'password': password})
    flag_uuid = True
    if user.text != 'auth_error':
        while (flag_uuid):
            print("Qual è il nome del cane di cui vuoi collegare il collare ?")
            dog_name = input()
            uuid = requests.get(f'http://{server_ip}/bridge_name_to_uuid',
                                params={'user': user.text, 'dog_name': dog_name.lower()})
            if uuid.text == 'dog_error':
                print("Il nome del cane che hai inserito non è registrato")
            else:
                flag_uuid = False
                data = {'email': hashlib.sha256(email.encode()).hexdigest(),
                        'password': hashlib.sha256(password.encode()).hexdigest(),
                        'uuid': uuid.text}
                file = open('json_data.json', 'a+')
                json.dump(data, file)
                print("Ora accoppia tramite bluetooth il tuo collare Findog")
        return True
    else:
        print("Email o password errati")
        return False


if __name__ == '__main__':
    try:
        json_file = open('json_data.json')
    except FileNotFoundError:
        flag = False
        while not flag:
            flag = greetings()
    with open('json_data.json') as json_file:
        data = json.load(json_file)

    br = Bridge(data['uuid'])
    connected = False
    ts = time.time()
    while not connected:
        if time.time() - ts > interval:
            ts = time.time()
            connected = br.setupSerial()
    br.loop()
