#include <mcp_can.h>
#include <SPI.h>

#define CAN0_INT 2                              // Set INT to pin 2
MCP_CAN CAN0(10);                               // Set CS to pin 10

#define myID  0x0041
#define myID2 0x0300 | myID

void setup()
{
    Serial.begin(115200);
    while (CAN_OK != CAN0.begin(CAN_500KBPS))    // Init CAN baudrate to 500Kbps
    {
        Serial.println("CAN init fail, retry...");
        delay(100);
    }
    Serial.println("CAN init ok!");
}

void send_speed(long speed)
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
    CAN0.sendMsgBuf(myID, 0, 8, data);
    Serial.print("Sent speed ");
    Serial.print(speed);
}


void send_position(long position)
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
    CAN0.sendMsgBuf(myID, 0, 8, data);
    Serial.print("Sent position ");
    Serial.println(position);
}

void loop()
{
    long speed = 1000;
    long position = 1000;

    send_speed(speed);    
    send_position(position);
    
    delay(10); 
}
