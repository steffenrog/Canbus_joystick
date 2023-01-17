# Author: Steffen Rogne
# Brief:  Test software, read canbus with filter. Read Analog Joystick, send joystick values over can.
# 
#==================================================
#
#
##RS485 PINS
# MISO - Pin 21 (GP16)
# CS - Pin 22 (GP17)
# SCK - Pin 24 (GP18)
# MOSI - Pin 25 (GP19)
# LED Out - Pin 34(GP 28)
# 3v3 Out - Pin 36
# GND - Pin 38

##JOYSTICK PINS
#GP26_A0, GP27_A1#

##BUTTON PINS
#GP0, GP1, GP2,GP3, GP4, GP5#

##LED PINS ## not connected yet
#GP6, GP7, GP8, GP9, GP10, GP11, GP12, GP13, GP14#

import board
import analogio
import busio
from digitalio import DigitalInOut, Direction, Pull
import digitalio
from adafruit_mcp2515.canio import Message
from adafruit_mcp2515 import MCP2515 as CAN
import asyncio
import struct
import math
import time

cs = DigitalInOut(board.GP17)
cs.switch_to_output()
spi = busio.SPI(board.GP18, board.GP19, board.GP16)
can_bus = CAN(spi, cs)

yaxi = analogio.AnalogIn(board.GP26_A0)
xaxi = analogio.AnalogIn(board.GP27_A1)

btn1 = DigitalInOut(board.GP0)
btn1.direction = Direction.INPUT
btn1.pull = Pull.UP

btn2 = DigitalInOut(board.GP1)
btn2.direction = Direction.INPUT
btn2.pull = Pull.UP

btn3 = DigitalInOut(board.GP2)
btn3.direction = Direction.INPUT
btn3.pull = Pull.UP

btn4 = DigitalInOut(board.GP3)
btn4.direction = Direction.INPUT
btn4.pull = Pull.UP

buttons = [True,True,True,True]
##Not connected yet: btn5,btn6
# btn5 = DigitalInOut(board.GP4)
# btn5.direction = Direction.INPUT
# btn5.pull = Pull.UP

# btn6 = DigitalInOut(board.GP5)
# btn6.direction = Direction.INPUT
# btn6.pull = Pull.UP

joy_res = 12

##To use can filters, 2 filters can be used
class Match:
    def __init__(self,address,mask,extended: bool):
        self.address = address
        self.mask = mask
        self.extended = extended

##Send joystick values, adapted to receiving software.
async def send_joystick_position(x, y):
    id = 0x18fdd6F1 ##Modify ID
    
    ##Joystick calculations
    #-2048 to 2048
    x = ((x/2**16)*(2**(joy_res+1)))-(2**joy_res) ##Works pretty good 
    y = ((y/2**16)*(2**(joy_res+1)))-(2**joy_res) ##Works pretty good
  
    data = [0x01, 0x00, 0x01, 0x00, 0xff, 0x00, 0x00, 0x1f] ##Setting up array
    
    #print(buttons)

    ##Button setup
    if not buttons[0]:
        data[5] = data[5] | 0x40
    if not buttons[1]:
        data[5] = data[5] | 0x10
    if not buttons[2]:
        data[5] = data[5] | 0x04
    if not buttons[3]:
        data[5] = data[5] | 0x01
        #if self.config == True:
        #    data[6] = data[6] | 0x40
        #    self.config = False
        #    print("Config sent...")
        
    ##Button 5 and 6 not added yet......   Prepared for config use 
    #if not btn5.value:
    #    data[6] = data[6] | 0x04
    #if b == 6:
    #    button[6] = button[6] | 0x40
    #    self.config = True
    #    print("Config...")
    
    #print(btn1.value, btn2.value, btn3.value, btn4.value) ##Debug print
    
    ##Joystick data send setup
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
    data[1] = tmp[1]                            #  8 bit...

    tmp = int(abs(y)).to_bytes(2,'big', signed=False)
    data[2] = data[2] | ((tmp[0] << 6) & 0xC0)
    data[2] = data[2] | (tmp[0] & 0x0c)
    data[3] = tmp[1]
    
    #print(bytes(data))  ##Debugging print
    #print(x,y)
    
    #Send canmessage, buttons and joystick
    message = Message(id=id, data=bytes(data), extended=True)
    can_bus.send(message)
    await asyncio.sleep(0.1)    ##

async def read_joystick_position():
    center_x = 33700
    center_y = 33300
    dead_zone = 1000
    while True:
        x_list = []
        y_list = []
        for i in range(800):
            x_list.append(xaxi.value)           
        for i in range(10):
            y_list.append(yaxi.value)
        x_list.sort()
        y_list.sort()
        x = x_list[400]
        y = y_list[5]
        if abs(x - center_x) < dead_zone:
            x = center_x
        #if abs(y - center_y) < dead_zone:
        #    y = center_y
        print(x,y)
        await send_joystick_position(x, y)

##Read button states
async def read_buttons():
    while True:
        buttons[0] = btn1.value
        buttons[1] = btn2.value
        buttons[2] = btn3.value
        buttons[3] = btn4.value
        await asyncio.sleep(0)
        
##Listening on bus for filtered messages.
async def listen_can(listener):
    while True:
        message_count = listener.in_waiting()
        for _i in range(message_count):
            msg = listener.receive()
            print("Message from: ", hex(msg.id))
            print(msg.data)

            #do something with the data
               
        await asyncio.sleep(0)

##Running main program, setup filters to subscribe
async def main():
    matches = [
           Match(0x777,0xFF,True),      ##Filter 1
           Match(0x666,0xFFF,True),     ##Filter 2
           ]
    with can_bus.listen(matches) as listener:
        task1 = asyncio.create_task(listen_can(listener))
        print("Starting can filters......")
        task2 = asyncio.create_task(read_joystick_position())
        print("Reading joystick......")
        task3 = asyncio.create_task(read_buttons())
        await asyncio.gather(task1, task2, task3)
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Program closed")