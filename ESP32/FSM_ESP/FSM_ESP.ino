#include <WiFi.H>
#include "BLEDevice.h"
#include "BLEScan.h"
#include "BluetoothSerial.h"

enum states {
  connected, not_connected
};

#define FREQ 20
long timestamp;

states currentState;

const char* ssid = "Nome WiFi";
const char* psw = "psw WiFi";
const uint16_t port = 8090;
const char* host = "indirizzo IP computer host";

void setup() {
  // Setup per connessione Bluetooth 
  // Non so se ci ho messo tutto --> CONTROLLARE
  Serial.begin(115200);
  Serial.println("Starting Arduino BLE Client application...");
  BLEDevice::init("BLE-MASTER");
  
  //bt_2.0 inizialization
  SerialBT.begin("MyDog"); //Bluetooth device name
  Serial.println("Bt_2.0 started, now you can pair it with bluetooth!");

  // Retrieve a Scanner and set the callback we want to use to be informed when we
  // have detected a new device.  Specify that we want active scanning and start the
  // scan to run for 5 seconds.
  BLEScan* pBLEScan = BLEDevice::getScan();
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setInterval(1349);
  pBLEScan->setWindow(449);
  pBLEScan->setActiveScan(true);
  pBLEScan->start(5, false);

  // Setup per connessione WiFi
  WiFi.begin(ssid, psw);
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print("...");
  }

  Serial.print("WiFi connected with IP: ");
  Serial.println(WiFi.localIP());

  timestamp = millis();
  currentState = not_connected;
}

void loop() {
  states futureState;
  WiFiClient client;

  // Controllo ogni FREQ millisecondi
  if (millis() - timestamp > FREQ) {
    timestamp = millis();
  }

  futureState = currentState;

  if (currentState == connected) {
    // Controllo connessione WiFI
    // WiFi.status() per check connessione a WiFi
    // client.connected() per check connessione a socket 
    // dovrebbe essere una cosa del genere --> if (WiFi.status() && client.connected()) 

    // Se è tutto ok 
    futureState = currentState;
    // Se non è connesso
    futureState = not_connected;
    
    // Fare scan 

    // Se trovo uuid mandare a socket 
    client.print("uuid del cane");

    // Scrivere a bridge con bluetooth
    SerialBT.println(0xfa);
    SerialBT.println(0x01);
    SerialBT.println(0x01);
    SerialBT.println(0xfe);
  }

  if (currentState == not_connected) {
    // Provo a connettermi

    if(!client.connect(host, port)) {
      Serial.println("Connection to host failed");
      futureState = currentState;

      delay(1000);
      return;
    }

    // Se va a buon fine 
    Serial.println("Connected to server successful!");
    futureState = connected;
    
    // Mandare il proprio uuid in broadcast
  }

  currentState = futureState;
  
}
