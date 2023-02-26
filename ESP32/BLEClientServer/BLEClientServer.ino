#include <Arduino.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>
#include <BLEAdvertising.h>
#include "BluetoothSerial.h"
#include "BLEDevice.h"
#include "BLEClient.h"
#include "EEPROM.h"

int addr = 0;
#define EEPROM_SIZE 64

//CLIENT: stato connected, effettua lo scan 
//SERVER: stato not connected, non effettua lo scan e credo non debba compiera azioni ma solo farsi leggere la caratteristica già creata nel setup

//stati: c = connected, not_c = not connected
enum states { //c corrisponde a 0, not_c corrisponde a 1
  c, not_c
};

BluetoothSerial SerialBT; 

#define LOOP_FREQ 2000 //tempo di attesa prima dell'esecuzione di ogni loop
#define BIND_FREQ 30000 //tempo di attesa prima della riconnessione allo stesso dispositivo
long timestamp;

states currentState;
states futureState;

//**SERVER PART START**
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"

//variabili utilizzate dal server 
BLEServer *pServer;
BLEService *pService;
static BLECharacteristic *pCharacteristic;
BLEAdvertising* pAdvertising;
bool bleConnected = false;

const byte numChars = 6;

static char *received_uuid = "0000";

String eeprom_uuid;

class MyServerCallbacks: public BLEServerCallbacks {
  // TODO this doesn't take into account several clients being connected
    void onConnect(BLEServer* pServer) {
      bleConnected = true;
      pAdvertising->start();
    };

    void onDisconnect(BLEServer* pServer) {
      if (pServer->getConnectedCount() == 0) {
        bleConnected = false;
      }
    };
};


//fase iniziale di configurazione del server
void initBLEserver() {

  if (!SerialBT.begin("Collare Findog")) { 
    Serial.write(" Failed to start BTSerial");
  }


  // Initialize BLE
  BLEDevice::setPower(ESP_PWR_LVL_P7);
  BLEServer *pServer = BLEDevice::createServer();
   // Set server callbacks
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService("4fafc201-1fb5-459e-8fcc-c5c9c331914b");
  pCharacteristic = pService->createCharacteristic(
                                         CHARACTERISTIC_UUID,
                                         BLECharacteristic::PROPERTY_READ |
                                         BLECharacteristic::PROPERTY_WRITE |
                                         BLECharacteristic::PROPERTY_NOTIFY

                                       );

  //characteristic with the UUID
  pCharacteristic->setValue(received_uuid); //CHANGE THIS


  // Start the service
  pService->start();

  // Start advertising
  pAdvertising = pServer->getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);  // functions that help with iPhone connections issue
  pAdvertising->setMinPreferred(0x12);

  pAdvertising->start();

  Serial.println(" BLE Server active now");
}
//**SERVER PART END**

//**CLIENT PART START**
//BLEScan* pBLEScan; //dichiarazione per lo scan

// The remote service we wish to connect to.
static BLEUUID serviceUUID("4fafc201-1fb5-459e-8fcc-c5c9c331914b");
// The characteristic of the remote service we are interested in.
static BLEUUID    charUUID("beb5483e-36e1-4688-b7f5-ea07361b26a8");

//variabili utilizzate dal client
static boolean doConnect = false;
static boolean connected = false;
static boolean doScan = false;
static BLERemoteCharacteristic* pRemoteCharacteristic;
static BLEAdvertisedDevice* myDevice;


static BLEScan* pBLEScan;                                           //BLE scan pointer
static BLEClient*  pClient;

static String dev_addr = "";
static String prev_dev_addr = "";

class MyClientCallback : public BLEClientCallbacks {
  void onConnect(BLEClient* pclient) {
  }

  void onDisconnect(BLEClient* pclient) { //Quando avviene l'errore di mismatch(0,1) finisce qui, come soluzione momentanea avevo messo ESP restart
    connected = false;
    Serial.println("onDisconnect");
    //delay(3000);
    //ESP.restart();
  }
};

//Client: funzione per connettersi all'esp trovato e leggere la sua caratteristica
String connectToServer(){
  if(millis() - timestamp > BIND_FREQ){
        timestamp = millis();
        dev_addr = "";
    }

  dev_addr = myDevice->getAddress().toString().c_str();
  Serial.print("Checking if the device ");
  Serial.print(dev_addr);
  Serial.println(" was previously connected");
  if(dev_addr == prev_dev_addr) {

    doConnect = false;
    return "\n\nThe device "+dev_addr+" was previuosly connected \n\n";
    }
  else {

      prev_dev_addr = dev_addr;
      Serial.print("Forming a connection to ");
      Serial.println(dev_addr);



      /* Connect to the remote BLE Server */
      pClient->connect(myDevice); // if you pass BLEAdvertisedDevice instead of address, it will be recognized type of peer device address (public or private)
      if(!pClient->isConnected()){
        doConnect = false;
        return "\n\nClient not connected \n\n";
      }
      Serial.println(" - Connected to server");

      /* Obtain a reference to the service we are after in the remote BLE server */
      BLERemoteService* pRemoteService = pClient->getService(serviceUUID);
      if (pRemoteService == nullptr)
      {
        Serial.println(serviceUUID.toString().c_str());
        pClient->disconnect();
        doConnect = false;
        return "\n\nFailed to find our service UUID: \n\n";
      }
      Serial.println(" - Found our service");


      /* Obtain a reference to the characteristic in the service of the remote BLE server */
      pRemoteCharacteristic = pRemoteService->getCharacteristic(charUUID);
      if (pRemoteCharacteristic == nullptr)
      {
        Serial.println(charUUID.toString().c_str());
        pClient->disconnect();
        doConnect = false;
        return "\n\n Failed to find our characteristic UUID: \n\n";
      }
      Serial.println(" - Found our characteristic");


      if(pRemoteCharacteristic->canRead())
      {
        std::string value = pRemoteCharacteristic->readValue();
        Serial.print("The characteristic value was: ");
        //Serial.println(value.c_str());
        bluetoothPrintLine(value.c_str());
      }

      connected = true;

      return "\n\nAll operations were performed correctly.\n\n";
      }
}

//Client: classe invocata nella fase di scan
class MyAdvertisedDeviceCallbacks: public BLEAdvertisedDeviceCallbacks
{
 /* Called for each advertising BLE server. */
  void onResult(BLEAdvertisedDevice advertisedDevice)
  {
    Serial.print("BLE Advertised Device found: ");
    Serial.println(advertisedDevice.toString().c_str());

    /* We have found a device, let us now see if it contains the service we are looking for. */
    if (advertisedDevice.haveServiceUUID() && advertisedDevice.isAdvertisingService(serviceUUID))
    {
      BLEDevice::getScan()->stop();
      myDevice = new BLEAdvertisedDevice(advertisedDevice);
      doConnect = true;
      doScan = true;

    }
  }
};


//funzione per scrivere la caratteristica trovata sul bridge
void bluetoothPrintLine(String line)
{
    unsigned l = line.length();
    SerialBT.write(0xff);
    for(int i=0; i<l; i++)
    {
        if(line[i]!='\0')
            SerialBT.write(byte(line[i]));
            Serial.write(byte(line[i]));
    }
    SerialBT.write(0xfe); // \n
}

void check_my_presence(){
    SerialBT.write(0xfa);
    //SerialBT.write(0x01);
    //SerialBT.write(0x01);
    SerialBT.print(received_uuid);
    SerialBT.write(0xfe);
}

//CLIENT PART END
//FUNZIONE PER IL CAMBIO DI STATO IN SEGUITO A CONNESSIONE E DISCONNESSIONE BRIDGE
void callback(esp_spp_cb_event_t event, esp_spp_cb_param_t *param){
  if(event == ESP_SPP_SRV_OPEN_EVT){
    Serial.println("Bridge Connected");
    futureState=c;
  }

  if(event == ESP_SPP_CLOSE_EVT ){
    Serial.println("Bridge Disconnected");
    futureState=not_c;
  }
}



void writeString(char add,String data)
{
  int _size = data.length();
  int i;
  for(i=0;i<_size;i++)
  {
    EEPROM.write(add+i,data[i]);
  }
  EEPROM.write(add+_size,'\0');   //Add termination null character for String Data
  EEPROM.commit();
}


String read_String(char add)
{
  int i;
  char data[100]; //Max 100 Bytes
  int len=0;
  unsigned char k;
  k=EEPROM.read(add);
  while(k != '\0' && len<500)   //Read until null character
  {    
    k=EEPROM.read(add+len);
    data[len]=k;
    len++;
  }
  data[len]='\0';
  return String(data);
}


void recv_uuid() {
    static byte ndx = 0;
    char endMarker = '\n';
    char rc;
    while (SerialBT.available() > 0) {
        char serial_uuid[numChars];
        Serial.println("Sto ricevendo");
        rc = SerialBT.read();
        if (rc != endMarker) {
            serial_uuid[ndx] = rc;
            ndx++;
            if (ndx >= numChars) {
                ndx = numChars - 1;
            }
        }
        else {
            serial_uuid[ndx] = '\0'; // terminate the string
            ndx = 0;
            
          Serial.println("Fine ricezione");
          //received_uuid = serial_uuid;
          writeString(0, String(serial_uuid));
          
          eeprom_uuid = read_String(0);
          received_uuid = &eeprom_uuid[0];
          pCharacteristic->setValue(received_uuid);
        }
    }
    
}

void clear_eeprom(){
  for(int i=0; i<8; i++){
    EEPROM.write(i,0);
    EEPROM.commit();
    eeprom_uuid = read_String(0);
    received_uuid = &eeprom_uuid[0];
  }
  
}

void setup() {
  // Initialize Serial
  Serial.begin(115200);
  Serial.println("Starting Arduino BLE Client application...");
  BLEDevice::init("Collare Findog"); //CHANGE THIS
  SerialBT.begin("Collare Findog"); //Bluetooth device name
  Serial.println("Bt_2.0 started, now you can pair it with bluetooth!");

  Serial.println("Starting Arduino BLE Server application...");

  
  
 if (!EEPROM.begin(EEPROM_SIZE)) {
        Serial.println("failed to init EEPROM");
        delay(1000000);
    }

  eeprom_uuid = read_String(0);
  received_uuid = &eeprom_uuid[0];
  Serial.println("UIID MEMORIZZATO :");
  Serial.println(received_uuid);
  // Initialize BLE server
  initBLEserver();
  //forzato per debug
  futureState=not_c;
  //futureState=c;
  //SerialBT.register_callback(callback);
  //currentState=futureState;
  pClient  = BLEDevice::createClient(); //created client
  pBLEScan = BLEDevice::getScan();
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setInterval(1349);
  pBLEScan->setWindow(449);
  pBLEScan->setActiveScan(true);

}


void loop() {
   //clear_eeprom();
  

  // Controllo ogni LOOP_FREQ millisecondi
  if (millis() - timestamp > LOOP_FREQ) {
    recv_uuid();
    //Serial.print("Read Data:");
    //Serial.println(received_uuid);
    timestamp = millis();

    SerialBT.register_callback(callback);
    currentState = futureState;

    if(currentState == c) //in casa
    {

      check_my_presence();


      //pBLEScan->start(5, false);
      if (pClient->isConnected()) pClient->disconnect();
      BLEScanResults foundDevices = pBLEScan->start(5, false);
      Serial.println("Devices found: ");
      Serial.println(foundDevices.getCount());
      Serial.println("Scan done!");
      pBLEScan->clearResults();   // delete results fromBLEScan buffer to release memory

      if (doConnect == true) {
          String result = (connectToServer());
          Serial.println(result);


        }


      pBLEScan->clearResults();
    }
  }

  //delay(1000);
}
