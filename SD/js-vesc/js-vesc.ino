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

const int SAMPLE_SIZE = 500;

// Sampling
int x_samples[SAMPLE_SIZE];
int y_samples[SAMPLE_SIZE];

// Cruise setup
bool cruiseControlMode = false;
int lastX = 0;
int lastY = 0;
int maxSpeed = 0;
int increment = 100;
int lastJoystickDirection = 0; // -1 for down, 0 for center, 1 for up

#define myID  0x0041
#define myID2 0x0300 | myID

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
    // Convert the data to bytes
    byte data_bytes[4];
    data_bytes[0] = (data >> 24) & 0xFF;
    data_bytes[1] = (data >> 16) & 0xFF;
    data_bytes[2] = (data >> 8) & 0xFF;
    data_bytes[3] = data & 0xFF;

    // Create a dummy value
    byte dummy_bytes[4] = {0, 0, 0, 0};

    // Create the data for the CAN message
    byte msg_data[8];

    if (isSpeed) {
        msg_data[0] = 0;
        msg_data[1] = dummy_bytes[0];
        msg_data[2] = dummy_bytes[1];
        msg_data[3] = dummy_bytes[2];
        msg_data[4] = dummy_bytes[3];
        msg_data[5] = data_bytes[0];
        msg_data[6] = data_bytes[1];
        msg_data[7] = 0;
    } else {
        msg_data[0] = 0;
        msg_data[1] = data_bytes[0];
        msg_data[2] = data_bytes[1];
        msg_data[3] = data_bytes[2];
        msg_data[4] = data_bytes[3];
        msg_data[5] = dummy_bytes[0];
        msg_data[6] = dummy_bytes[1];
        msg_data[7] = 0;
    }

    // Send the CAN message
    CAN.sendMsgBuf(myID, 0, 8, msg_data);
    Serial.print("Sent ");
    Serial.print(isSpeed ? "speed " : "position ");
    Serial.println(data);
}

void send_speed(int speed) 
{
  send_CAN_message(speed, true);
}

void send_position(int position) 
{
  send_CAN_message(position, false);
}

void read_button() {
    static bool previousButtonValue[6] = {false, false, false, false, false, false};
    int i = 0;
    for (Button &button : buttons) {
        bool currentButtonValue = digitalRead(button.pin);

        if (!previousButtonValue[i] && currentButtonValue) {
            cruiseControlMode = !cruiseControlMode;

            // Update LED0 status
            leds[0].status = cruiseControlMode ? LOW : HIGH;

            // Actually turn the LED on or off
            digitalWrite(leds[0].pin, leds[0].status);
        }

        previousButtonValue[i] = currentButtonValue;
        i++;
    }
}

void loop()
{
    // Joystick center
    const int CENTER_X = 0;
    const int CENTER_Y = 0;
    const int DEAD_ZONE = 350;
    
    // Sampling
    for (int i = 0; i < SAMPLE_SIZE; i++)
    {
        x_samples[i] = map(analogRead(XAXI), 0, 4095, -4096, 4096);
        y_samples[i] = map(analogRead(YAXI), 0, 4095, -4096, 4096);
    }
    
    std::sort(x_samples, x_samples + SAMPLE_SIZE);
    std::sort(y_samples, y_samples + SAMPLE_SIZE);
    
    int xaxi = x_samples[SAMPLE_SIZE / 2]; // Median
    int yaxi = y_samples[SAMPLE_SIZE / 2]; // Median

       // Deadzone handling
    if (abs(xaxi - CENTER_X) < DEAD_ZONE)
    {
        xaxi = CENTER_X;
    }
    else if (cruiseControlMode) // Cruise control mode
    {
        int joystickDirection = xaxi > CENTER_X ? 1 : -1;

        if (joystickDirection == lastJoystickDirection) {
            // If the joystick is being held in the same direction as the last loop iteration,
            // increase or decrease speed according to the direction.
            maxSpeed = joystickDirection == 1 ? min(maxSpeed + increment, xaxi) : max(maxSpeed - increment, xaxi);
        }

        // Else, if the joystick has just been released, keep speed.
        // maxSpeed keeps its current value.

        xaxi = maxSpeed; // Set the current speed to the max speed
        lastJoystickDirection = joystickDirection;
    }

    if (abs(yaxi - CENTER_Y) < DEAD_ZONE)
    {
        yaxi = CENTER_Y;
    }

    send_speed(xaxi);    
    send_position(yaxi);
    read_button();
    delay(10);
}
