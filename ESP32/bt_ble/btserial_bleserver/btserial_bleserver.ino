#include <Arduino.h>
#include <BLEDevice.h>
#include "BluetoothSerial.h"
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLE2902.h>
#include <BLEAdvertising.h>



BluetoothSerial SerialBT;
static  BLECharacteristic* pCharacteristic; 
bool initBtSerial();
void initBLEserver();

void setup() {
  // Initialize Serial
  Serial.begin(9600);
  // Initialize BT serial interface
  initBtSerial();


  // Initialize BLE server
  initBLEserver();
  SerialBT.register_callback(serial_callback);


}

void loop() {
    SerialBT.write(0xff);
    SerialBT.write(0x01);
    SerialBT.write(0x01);
    SerialBT.write(0xfe);
}

void serial_callback(esp_spp_cb_event_t event, esp_spp_cb_param_t *param){
    if(event == ESP_SPP_CLOSE_EVT ){
        pCharacteristic->setValue("Scappato");
        }
    else if(event = ESP_SPP_SRV_OPEN_EVT){
        pCharacteristic->setValue("In Casa");
       }
}

bool initBtSerial() {

  if (!SerialBT.begin("ESP32BT_2")) {
    Serial.println(" Failed to start BTSerial");
    return false;
  }

  return true;
}


// List of Service and Characteristic UUIDs
#define SERVICE_UUID        "4fafc201-1fb5-459e-8fcc-c5c9c331914b"
#define CHARACTERISTIC_UUID "beb5483e-36e1-4688-b7f5-ea07361b26a8"
//... more UUIDs
//

/** Characteristic for client notification */
BLECharacteristic *pCharacteristicNotify;
//
// ... more characteristics
//

/** BLE Advertiser */
BLEAdvertising* pAdvertising;
/** BLE Service */
BLEService *pService;
/** BLE Server */
BLEServer *pServer;

/** Flag if a client is connected */
bool bleConnected = false;

/** Digital output value received from the client */
uint8_t digitalOut = 0;
/** Flag for change in digital output value */
bool digOutChanged = false;

/**
 * MyServerCallbacks
 * Callbacks for client connection and disconnection
 */
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
    }
};

/**
 * MyCallbackHandler
 * Callbacks for client write requests

class MyCallbackHandler: public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) {
//
// ... Handle the incoming value
//
    }
  }
};
 */
void initBLEserver() {



  if (!SerialBT.begin("ESP32_BT2" )) {
    Serial.write(" Failed to start BTSerial");
  }


// Initialize BLE
  BLEDevice::init("ESP32BLE" );
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

  pCharacteristic->setValue("In casa");
//
// add other characteristics
//

  // Start the service
  pService->start();

  // Start advertising
  pAdvertising = pServer->getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);  // functions that help with iPhone connections issue
  pAdvertising->setMinPreferred(0x12);

  pAdvertising->start();

  Serial.println(" BLE active now");
}
