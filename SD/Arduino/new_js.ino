#include <mcp_can.h>
#include <SPI.h>
#include <algorithm>
#include <stdio.h>
#include <EEPROM.h>
// MCP2515 CAN setup
#define SCK 18
#define MOSI 19
#define MISO 16
#define CAN_INT 20
MCP_CAN CAN(17);
// Joystick pins
#define XAXI 27 
#define YAXI 26
#define ZAXI 28
// Button setup
const int BTN1 = 5;
const int BTN2 = 7;
const int BTN3 = 9;
const int BTN4 = 11;
const int BTN5 = 13;
const int BTN6 = 3;
bool button_value[6];
const int BUTTON_PINS[] = {BTN1, BTN2, BTN3, BTN4, BTN5, BTN6};
// Can value storage
long unsigned int rxId;
unsigned char len = 0;
unsigned char rxBuf[8] = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
// Sending frequency
unsigned long prevMillis = 0;
const long interval = 50;
// Joystick center
const int CENTER_X = 0;
const int CENTER_Y = 0;
const int DEAD_ZONE = 75;
// LED setup
const int LED1 = 6;
const int LED2 = 8;
const int LED3 = 10;
const int LED4 = 12;
const int LED5 = 14;
const int LED6 = 2;
const int LED7 = 4;
const int LED8 = 1;
const int LED9 = 0;
const int getLedPin[9] = {LED1, LED2, LED3, LED4, LED5, LED6, LED7, LED8, LED9};
int led_status[9] = {0, 0, 0, 0, 0, 0, 0, 0, 0};
int flash = 0;
// CAN ID setup
const char ID_LIST[] = {0xF1, 0xF2, 0xF3, 0xF4, 0xF5, 0xF6};
const int NUM_IDS = 6;
int buttonToIdMap[] = {0, 1, 2, 3, 4, 5};
int selectedIDIndex = 0;
unsigned long extendedID;
unsigned long lastID;
bool stopFlag = false;
void setup()
{
  // Init serial, eeprom, and CAN
  Serial.begin(115200);
  EEPROM.begin(512);
  SPI.setSCK(SCK);
  SPI.setTX(MOSI);
  SPI.setRX(MISO);
  if (CAN.begin(MCP_STDEXT, CAN_500KBPS, MCP_8MHZ) == CAN_OK)
    Serial.println("MCP2515 Initialized Successfully!");
  else
    Serial.println("Error Initializing MCP2515...");
  pinMode(CAN_INT, INPUT);
  // CAN Filter
  CAN.init_Mask(0, 0, 0x1FFFFFFF);
  CAN.init_Filt(0, 0, 0x18EFF1FD);
  CAN.init_Mask(1, 0, 0x1FFFFFFF);
  CAN.init_Filt(1, 1, 0x18EFF102);
  CAN.init_Filt(2, 1, 0x00000000);
  CAN.init_Filt(3, 1, 0x00000000);
  CAN.init_Filt(4, 1, 0x00000000);
  CAN.init_Filt(5, 1, 0x00000000);
  CAN.setMode(MCP_NORMAL);
  // If joystick have not written to eeprom, set default ID F1
  lastID = EEPROM.read(0);
  if (lastID == 0xFF)
  {
    lastID = ID_LIST[0];
  }
  // Joystick 12 bit
  analogReadResolution(12);
  // BTN
  pinMode(BTN1, INPUT_PULLUP);
  pinMode(BTN2, INPUT_PULLUP);
  pinMode(BTN3, INPUT_PULLUP);
  pinMode(BTN4, INPUT_PULLUP);
  pinMode(BTN5, INPUT_PULLUP);
  pinMode(BTN6, INPUT_PULLUP);
    for (int i = 0; i < 6; i++)
  {
    button_value[i] = digitalRead(BUTTON_PINS[i]);
  }
  // LED
  pinMode(LED1, OUTPUT);
  pinMode(LED2, OUTPUT);
  pinMode(LED3, OUTPUT);
  pinMode(LED4, OUTPUT);
  pinMode(LED5, OUTPUT);
  pinMode(LED6, OUTPUT);
  pinMode(LED7, OUTPUT);
  pinMode(LED8, OUTPUT);
  pinMode(LED9, OUTPUT);
}
void loop()
{
  // CAN ID Menu
  if (digitalRead(BTN1) == LOW && digitalRead(BTN6) == LOW)
  {
    while (digitalRead(BTN1) == LOW && digitalRead(BTN6) == LOW)
    {
      delay(50);
    };
    // Stop tasks
    stopFlag = true;
    // Blink LEDs
    unsigned long start_time = millis();
    while (millis() - start_time <= 5000)
    {
      for (int i = 0; i <= 8; i++)
      {
        digitalWrite(getLedPin[i], HIGH);
      }
      delay(100);
      for (int i = 0; i <= 8; i++)
      {
        digitalWrite(getLedPin[i], LOW);
      }
      delay(100);
    }
    while (stopFlag)
    {
      // Select ID
      for (int i = 0; i < NUM_IDS; i++)
      {
        if (digitalRead(BUTTON_PINS[i]) == LOW)
        {
          int getLedPin = BUTTON_PINS[i];
          digitalWrite(getLedPin, HIGH);
          delay(100);
          digitalWrite(getLedPin, LOW);
          delay(100);
          lastID = ID_LIST[i];
          // Write new ID to eeprom
          EEPROM.write(0, lastID);
          EEPROM.commit();
          // Starts tasks
          stopFlag = false;
          break;
        }
      }
    }
  }
  else
  {
    // Joystick readings, setting middle 
    int x_list[500];
    int y_list[500];
    for (int i = 0; i < 500; i++)
    {
      x_list[i] = map(analogRead(XAXI), 0, 4095, -4096, 4096);
      y_list[i] = map(analogRead(YAXI), 0, 4095, -4096, 4096);
    }
    std::sort(x_list, x_list + 500);
    std::sort(y_list, y_list + 500);
    int xaxi = x_list[250];
    int yaxi = y_list[250];
    if (abs(xaxi - CENTER_X) < DEAD_ZONE)
    {
      xaxi = CENTER_X;
    }
    if (abs(yaxi - CENTER_Y) < DEAD_ZONE)
    {
      yaxi = CENTER_Y;
    }
    // Check if buttons are pressed
    button_value[0] = (digitalRead(BTN1));
    button_value[1] = (digitalRead(BTN2));
    button_value[2] = (digitalRead(BTN3));
    button_value[3] = (digitalRead(BTN4));
    button_value[4] = (digitalRead(BTN5));
    button_value[5] = (digitalRead(BTN6));
    // Check incoming CAN messages
    if (!digitalRead(CAN_INT))
    {
      CAN.readMsgBuf(&rxId, &len, (byte *)rxBuf);
    }
    processCANMessage();
    // Send CAN messages
    unsigned long currentMillis = millis();
    if (currentMillis - prevMillis >= interval)
    {
      prevMillis = currentMillis;
      sendCANMessage(xaxi, yaxi, button_value);
      // Flash the LEDs ...
      if (++flash > 20)
      {
        flash = 0;
        for (int i = 0; i < 9; i++)
        {
          if (led_status[i] > 1)
          {
            digitalWrite(getLedPin[i], digitalRead(getLedPin[i]) ^ 1);
          }
        }
      }
    }
  }
}
void processCANMessage()
{
  // If message is for LED control
  if ((rxId & 0x7FFF0000) == 0x18ef0000)
  {
    for (int i = 0; i < 9; i++)
    {
      if (i % 2)
      {
        led_status[i] = rxBuf[i / 2] & 0x0f;
      }
      else
      {
        led_status[i] = (rxBuf[i / 2] >> 4) & 0x0f;
      }
      if (led_status[i] <= 1)
      {
        // Set LED
        digitalWrite(getLedPin[i], led_status[i] == 1 ? LOW : HIGH);
      }
    }
  }
}
void sendCANMessage(int x_calculated, int y_calculated, bool button_value[])
{
  // Setting up sending values
  unsigned long fixedID = (lastID) | 0x18fdd600;
  unsigned char data[8] = {0x01, 0x00, 0x01, 0x00, 0xff, 0x00, 0x00, 0x1f};
  // Button values
  if (!button_value[0])
  {
    data[5] = data[5] | 0x40;
  }
  if (!button_value[1])
  {
    data[5] = data[5] | 0x10;
  }
  if (!button_value[2])
  {
    data[5] = data[5] | 0x04;
  }
  if (!button_value[3])
  {
    data[5] = data[5] | 0x01;
  }
  if (!button_value[4])
  {
    data[6] = data[6] | 0x04;
  }
  if (!button_value[5])
  {
    data[6] = data[6] | 0x40;
  }
  // Joystick values
  data[0] = 0x03;
  data[2] = 0x03;
  if (x_calculated < 0)
    data[0] |= 0x10;
  if (y_calculated < 0)
    data[2] |= 0x10;
  x_calculated = abs(x_calculated);
  y_calculated = abs(y_calculated);
  data[0] |= ((x_calculated >> 2) & 0xC0);
  data[0] |= ((x_calculated >> 8) & 0x0c);
  data[1] = x_calculated & 0xFF;
  data[2] |= ((y_calculated >> 2) & 0xC0);
  data[2] |= ((y_calculated >> 8) & 0x0c);
  data[3] = y_calculated & 0xFF;
  // Sending message
  CAN.sendMsgBuf(fixedID, 1, 8, data);
}