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
#define XAXI 26 
#define YAXI 27
//#define ZAXI 28

// Button and LED
struct Button {
    int pin;
    bool value;
};

struct Led {
    int pin;
    int status;
};

Button buttons[] = {
    {5, true},
    {7, true},
    {9, true},
    {11, true},
    {13, true},
    {3, true}
};

Led leds[] = {
    {6, 0},
    {8, 0},
    {10, 0},
    {12, 0},
    {14, 0},
    {2, 0},
    {4, 0},
    {1, 0},
    {0, 0}
};

// Sampling
const int SAMPLE_SIZE = 500;
int x_samples[SAMPLE_SIZE];
int y_samples[SAMPLE_SIZE];

// Can storage
long unsigned int rxId;
unsigned char len = 0;
unsigned char rxBuf[8];

// Button and LED setup
void setupButton(Button &button) {
    pinMode(button.pin, INPUT_PULLUP);
    button.value = digitalRead(button.pin);
}

void setupLed(Led &led) {
    pinMode(led.pin, OUTPUT);
}

void setup()
{
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
    
    // CAN Filter - 
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

    for (Button &button : buttons) {
        setupButton(button);
    }

    for (Led &led : leds) {
        setupLed(led);
    }

    // Boot-up light sequence
    for (Led &led : leds) {
        digitalWrite(led.pin, LOW); // Turn on LED
        delay(100); // Wait 100ms
        digitalWrite(led.pin, HIGH); // Turn off LED
    }

    // Leave the last LED on power.
    digitalWrite(leds[sizeof(leds)/sizeof(Led) - 1].pin, LOW);
}

void send_CAN_message(int data, bool isSpeed) {
    // if (isSpeed){}
    // Convert the data to bytes
    byte data_bytes[4];
    data_bytes[0] = (data >> 24) & 0xFF;
    data_bytes[1] = (data >> 16) & 0xFF;
    data_bytes[2] = (data >> 8) & 0xFF;
    data_bytes[3] = data & 0xFF;

    // Create the data for the CAN message
    byte msg_data[4];

    msg_data[0] = data_bytes[0];
    msg_data[1] = data_bytes[1];
    msg_data[2] = data_bytes[2];
    msg_data[3] = data_bytes[3];

    // Send the CAN message
    // if (isSpeed){}
    CAN.sendMsgBuf(0x00000341, 1, 4, msg_data);
}

void send_speed(int speed) 
{
    send_CAN_message(speed, true);
}

void send_position(int position) 
{
    send_CAN_message(position, false);
}

void loop()
{
    // Joystick center
    const int CENTER_X = 0;
    const int CENTER_Y = 0;
    const int DEAD_ZONE = 3000;
    
    // Sampling
    for (int i = 0; i < SAMPLE_SIZE; i++)
    {
        x_samples[i] = map(analogRead(XAXI), 0, 4095, -30000, 30000);
        //y_samples[i] = map(analogRead(YAXI), 0, 4095, -512, 512);
    }
    
    std::sort(x_samples, x_samples + SAMPLE_SIZE);
    //std::sort(y_samples, y_samples + SAMPLE_SIZE);
    
    int xaxi = x_samples[SAMPLE_SIZE / 2]; // Median
    //int yaxi = y_samples[SAMPLE_SIZE / 2]; // Median

    // Deadzone handling
    if (abs(xaxi - CENTER_X) < DEAD_ZONE)
    {
        xaxi = CENTER_X;
    }
   
    //if (abs(yaxi - CENTER_Y) < DEAD_ZONE)
    //{
    //    yaxi = CENTER_Y;
    //}
    send_speed(xaxi);
    //send_position(yaxi);
    //delay(10);
}
