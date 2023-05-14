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

// Button setup
const int BTN1 = 5;
const int BTN2 = 7;
const int BTN3 = 9;
const int BTN4 = 11;
const int BTN5 = 13;
const int BTN6 = 3;
bool button_value[6];
const int BUTTON_PINS[] = {BTN1, BTN2, BTN3, BTN4, BTN5, BTN6};

#define myID  0x0041
#define myID2 0x0300 | myID

//Setup run once
void setup()
{
  // Init serial, eeprom, and CAN - Serial for debugging - eeprom for storage of can id's - can for communication
  Serial.begin(115200);
  // while(!Serial){};
  EEPROM.begin(512);

  SPI.setSCK(SCK);
  SPI.setTX(MOSI);
  SPI.setRX(MISO);

  if (CAN.begin(MCP_STDEXT, CAN_500KBPS, MCP_8MHZ) == CAN_OK)
    Serial.println("MCP2515 Initialized Successfully!");
  else
    Serial.println("Error Initializing MCP2515...");
  pinMode(CAN_INT, INPUT);
  
  // CAN Filter - Will only let through message ment for the Joystick: Led handling, and buzzer trigger.
  CAN.init_Mask(0, 0, 0x1FFFFFFF);
  CAN.init_Filt(0, 0, 0x18EFF1FD);
  CAN.init_Mask(1, 0, 0x1FFFFFFF);
  CAN.init_Filt(1, 1, 0x18EFF102);
  CAN.init_Filt(2, 1, 0x00000000);
  CAN.init_Filt(3, 1, 0x00000000);
  CAN.init_Filt(4, 1, 0x00000000);
  CAN.init_Filt(5, 1, 0x00000000);

  //Setting CANhat to run mode
  CAN.setMode(MCP_NORMAL);

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

void send_speed(int speed)
{
    speed = (int)speed;

    // Convert the speed to bytes
    byte speed_bytes[2];
    speed_bytes[0] = (speed >> 8) & 0xFF;
    speed_bytes[1] = speed & 0xFF;

    // Create a dummy position value
    byte pos_bytes[4] = {0, 0, 0, 0};

    // Create the data for the CAN message
    byte data[8] = {0, pos_bytes[0], pos_bytes[1], pos_bytes[2], pos_bytes[3], speed_bytes[0], speed_bytes[1], 0};

    // Send the CAN message
    CAN.sendMsgBuf(myID, 0, 8, data);
   // Serial.print("Sent speed ");
   // Serial.print(speed);
}


void send_position(int position)
{
    // Your position value should be an integer. If it's not, you should convert it to an integer value.
    position = (int)position;

    // Convert the position to bytes
    byte pos_bytes[4];
    pos_bytes[0] = (position >> 24) & 0xFF;
    pos_bytes[1] = (position >> 16) & 0xFF;
    pos_bytes[2] = (position >> 8) & 0xFF;
    pos_bytes[3] = position & 0xFF;

    // Create a dummy speed value
    byte speed_bytes[2] = {0, 0};

    // Create the data for the CAN message
    byte data[8] = {0, pos_bytes[0], pos_bytes[1], pos_bytes[2], pos_bytes[3], speed_bytes[0], speed_bytes[1], 0};

    // Send the CAN message
    CAN.sendMsgBuf(myID, 0, 8, data);
   // Serial.print("Sent position ");
    //Serial.println(position);
}

void loop()
{
    //long speed = 1000;
    //long position = 1000;
    
    // Joystick center
    const int CENTER_X = 0;
    const int CENTER_Y = 0;
    const int DEAD_ZONE = 350;
 
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

/*
    // Check if buttons are pressed
    button_value[0] = (digitalRead(BTN1));
    button_value[1] = (digitalRead(BTN2));
    button_value[2] = (digitalRead(BTN3));
    button_value[3] = (digitalRead(BTN4));
    button_value[4] = (digitalRead(BTN5));
    button_value[5] = (digitalRead(BTN6));
*/

    send_speed(xaxi);    
    send_position(yaxi);
    
    //delay(10); 
}




/*
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
*/