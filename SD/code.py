## Author: Steffen Rogne
## Brief:  Joystick handler for SeaDrive software. 
## Read canbus with filter, and sets LED states. Read Analog Joystick, and button states send states over can.
# 
#==================================================
#
#
#RS485 PINS
# MISO  - Pin 21 (GP16)
# CS    - Pin 22 (GP17)
# SCK   - Pin 24 (GP18)
# MOSI  - Pin 25 (GP19)
# GND   - Pin 38
# 3v3 Out - Pin 36
# LED Out - Pin 34(GP 28)
# Interrupt is not in use
#
#JOYSTICK PINS
#GP26_A0, GP27_A1#
#
#BUTTON PINS
#GP0, GP1, GP2, GP3, GP4, GP5#
#
#LED PINS #
#GP6, GP7, GP8, GP9, GP10, GP11, GP12, GP13, GP14#

"""
This program imports the necessary modules for reading analog joystick inputs, 
digital button inputs, and sending/receiving data over CANbus.

board       - provides access to the hardware on the board.
analogio    - provides an interface for reading analog inputs.
busio       - provides a common interface for communication protocols.
digitalio   - provides an interface for controlling digital inputs and outputs.
adafruit_mcp2515.canio  - provides a message interface for sending and receiving data over CANbus.
adafruit_mcp2515        - provides a library for accessing the MCP2515 CAN controller.
asyncio     - provides asynchronous I/O support for coroutines.
struct      - provides pack and unpack functions for working with variable-length binary data.
"""

import board
import analogio
import busio
from digitalio import DigitalInOut, Direction, Pull
from adafruit_mcp2515.canio import Message, Match
from adafruit_mcp2515 import MCP2515 as CAN
import asyncio
import struct

"""
Initializes the digital input/output and bus communication for the joystick inputs and CANbus.
Define and initialize the inputs for digital buttons and outputs for LEDs on the Pi Pico board.
cs      - a digital input/output for the Chip Select (CS) signal for the CAN controller.
spi     - a bus communication interface using the SPI protocol.
can_bus - an instance of the MCP2515 CAN controller using the specified spi and cs.
yaxi    - an analog input for the Y-axis of the joystick.
xaxi    - an analog input for the X-axis of the joystick.
buttons: list of digital inputs for the buttons on the Pi Pico board.
led_status: list of digital outputs for the LEDs on the Pi Pico board.
"""

##MCP2515 setup
cs = DigitalInOut(board.GP17)
cs.switch_to_output()
spi = busio.SPI(board.GP18, board.GP19, board.GP16)
can_bus = CAN(spi, cs)

##X and Y may switch pins.
xaxi = analogio.AnalogIn(board.GP26_A0)
yaxi = analogio.AnalogIn(board.GP27_A1)

##Button setup, final setup may change depending on soldering
buttons = [DigitalInOut(gpio) for gpio in [board.GP2, board.GP1, board.GP0, board.GP5, board.GP3, board.GP4]]
for btn in buttons:
    btn.direction = Direction.INPUT
    btn.pull = Pull.UP

##LED setup, final setup may change depending on soldering
led_status = [DigitalInOut(gpio) for gpio in [board.GP11, board.GP10, board.GP9, board.GP14, board.GP8, board.GP12, board.GP13, board.GP7, board.GP6]]
for led in led_status:
    led.direction = Direction.OUTPUT
    led.value = True

##Joystick resolution, calculations based on this Joystick resulution. Default: joy_res = 12
joy_res = 12

##Send joystick values, adapted to receiving software. Default: id = 0x18fdd6F1 -To speak with SeaDrive software.
async def send_joystick_position(x, y):
    id = 0x18fdd6F1 #ID mimics Grayhill
    
    ##Joystick calculations
    x = ((x/2**16)*(2**(joy_res+1)))-(2**joy_res) #Works pretty good 
    y = ((y/2**16)*(2**(joy_res+1)))-(2**joy_res) #Works pretty good
    #print(x,y)     #Debugging print
    
    ##CAN send array
    data = [0x01, 0x00, 0x01, 0x00, 0xff, 0x00, 0x00, 0x1f]
    
    ##Button send values,
    if not buttons[0]:
        data[5] = data[5] | 0x40
    if not buttons[1]:
        data[5] = data[5] | 0x10
    if not buttons[2]:
        data[5] = data[5] | 0x04
    if not buttons[3]:
        data[5] = data[5] | 0x01
    if not buttons[4]:
        data[6] = data[6] | 0x04
    if not buttons[5]:
        data[6] = data[6] | 0x40
    
    ##Joystick send values
    if joy_res == 12:
        data[0] = 0x03
        data[2] = 0x03
    elif joy_res == 10:   
        data[0] = 0x03
        data[2] = 0x00
    else:
        data[0] = 0x00
        data[2] = 0x00
    if x < 0: data[0] = data[0] | 0x10
    if y < 0: data[2] = data[2] | 0x10

    tmp = int(abs(x)).to_bytes(2,'big', signed=False)
    data[0] = data[0] | ((tmp[0] << 6) & 0xC0)  # 10 bit ... 
    data[0] = data[0] | (tmp[0] & 0x0c)         # 12 bit ... 
    data[1] = tmp[1]                            #  8 bit ... 
    tmp = int(abs(y)).to_bytes(2,'big', signed=False)
    data[2] = data[2] | ((tmp[0] << 6) & 0xC0)   
    data[2] = data[2] | (tmp[0] & 0x0c)          
    data[3] = tmp[1]                            
    
    #print(bytes(data))  #Debugging print
    
    ##Send canmessage, buttons and joystick
    message = Message(id=id, data=bytes(data), extended=True)
    can_bus.send(message)                                                     #Comment line to run without can.
    await asyncio.sleep(0.1)    

##Read analog input, oversamling with middle
async def read_joystick_position():
    center_x = 32768        
    center_y = 32768
    dead_zone = 3000
    
    while True:
        x_list = []
        y_list = []
        for i in range(2000):
            x_list.append(xaxi.value)
            #x_list.append(65536 - xaxi.value)   #inverted - if Joystick is attached upside down        
        for i in range(10):
            y_list.append(yaxi.value)
            #y_list.append(65536 - yaxi.value)   #inverted - if Joystick is attached upside down
        x_list.sort()
        y_list.sort()
        x = x_list[1000]
        y = y_list[5]
        if abs(x - center_x) < dead_zone:
            x = center_x
        if abs(y - center_y) < dead_zone:
            y = center_y           
        #print(x,y)     #Debugging print    
        await send_joystick_position(x, y)
        await asyncio.sleep(0.01)
        
##Listening on bus, and set led states.
async def listen_can(listener):
    while True:
        message_count = listener.in_waiting()
        for _i in range(message_count):
            msg = listener.receive()
            #print(msg.id,msg.data)		#Debugging print

            if msg.id == 0x18eff102:	##Communication to joystick handler
                k = msg.data[0]						##"k" is key from other part of receiving software
                c = int((msg.data[1]&0xF0) >> 4)	##"c" is center led from other part of receiving software
                led_status[k-1].value= (c==0)		#OK	
              
        await asyncio.sleep(0.01)

##Starting main, setup filters to subscribe
async def main():
    match = [Match(address=0x00ef0002), Match(address=0x066)]
    with can_bus.listen(match) as listener:
        task1 = asyncio.create_task(listen_can(listener))
        print("Starting can filters......") 
        task2 = asyncio.create_task(read_joystick_position())       
        print("Reading joystick......")
        await task1
        await task2
          
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Program closed")
