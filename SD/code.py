# Author: Steffen Rogne
# Brief:  Test software, read canbus with filter. Read Analog Joystick, send joystick values over can.
# 
#==================================================
#
#
##RS485 PINS
# MISO  - Pin 21 (GP16)
# CS    - Pin 22 (GP17)
# SCK   - Pin 24 (GP18)
# MOSI  - Pin 25 (GP19)
# GND   - Pin 38
# 3v3 Out - Pin 36
# LED Out - Pin 34(GP 28)
#
##JOYSTICK PINS
#GP26_A0, GP27_A1#
#
##BUTTON PINS
#GP0, GP1, GP2, GP3, GP4, GP5#
#
##LED PINS ## not connected yet
#GP6, GP7, GP8, GP9, GP10, GP11, GP12, GP13, GP14#

import board
import analogio
import busio
from digitalio import DigitalInOut, Direction, Pull
from adafruit_mcp2515.canio import Message
from adafruit_mcp2515 import MCP2515 as CAN
import asyncio
import struct

cs = DigitalInOut(board.GP17)
cs.switch_to_output()
spi = busio.SPI(board.GP18, board.GP19, board.GP16)
can_bus = CAN(spi, cs)

yaxi = analogio.AnalogIn(board.GP26_A0)
xaxi = analogio.AnalogIn(board.GP27_A1)

btn1 = DigitalInOut(board.GP2)
btn1.direction = Direction.INPUT
btn1.pull = Pull.UP

btn2 = DigitalInOut(board.GP1)
btn2.direction = Direction.INPUT
btn2.pull = Pull.UP

btn3 = DigitalInOut(board.GP0)
btn3.direction = Direction.INPUT
btn3.pull = Pull.UP

btn4 = DigitalInOut(board.GP5)
btn4.direction = Direction.INPUT
btn4.pull = Pull.UP

btn5 = DigitalInOut(board.GP3)
btn5.direction = Direction.INPUT
btn5.pull = Pull.UP

btn6 = DigitalInOut(board.GP4)
btn6.direction = Direction.INPUT
btn6.pull = Pull.UP

##LED connections
led_1 = DigitalInOut(board.GP11)
led_1.direction = Direction.OUTPUT
led_1.value=True

led_2 = DigitalInOut(board.GP10)
led_2.direction = Direction.OUTPUT
led_2.value=True

led_3 = DigitalInOut(board.GP9)
led_3.direction = Direction.OUTPUT
led_3.value=True

led_4 = DigitalInOut(board.GP14)
led_4.direction = Direction.OUTPUT
led_4.value=True

##LED 5 and 6 may change depending on coding in receiving software
led_5 = DigitalInOut(board.GP8)
led_5.direction = Direction.OUTPUT
led_5.value=True

led_6 = DigitalInOut(board.GP12)
led_6.direction = Direction.OUTPUT
led_6.value=True

led_7 = DigitalInOut(board.GP13)
led_7.direction = Direction.OUTPUT
led_7.value=True

led_8 = DigitalInOut(board.GP7)
led_8.direction = Direction.OUTPUT
led_8.value=True

led_9 = DigitalInOut(board.GP6)
led_9.direction = Direction.OUTPUT
led_9.value=True

##Setting the array
buttons = [True,True,True,True,True,True]
leds = [True,True,True,True,True,True,True,True,True]
led_status = [led_1,led_2,led_3,led_4,led_5,led_6,led_7,led_8,led_9]

#Joystick resolution, calculations based on this
joy_res = 12

##To use can filters, 2 filters can be used
class Match:
    def __init__(self,address,mask,extended: bool):
        self.address = address
        self.mask = mask
        self.extended = extended

##Send joystick values, adapted to receiving software. 
async def send_joystick_position(x, y):
    id = 0x18fdd6F1 ##ID mimics Grayhill
    
    ##Joystick calculations
    #-2048 to 2048
    x = ((x/2**16)*(2**(joy_res+1)))-(2**joy_res) ##Works pretty good 
    y = ((y/2**16)*(2**(joy_res+1)))-(2**joy_res) ##Works pretty good
    
    #print(x,y)     ##Debugging print
    
    buttons[0] = btn1.value
    buttons[1] = btn2.value
    buttons[2] = btn3.value
    buttons[3] = btn4.value
    buttons[4] = btn5.value
    buttons[5] = btn6.value
        
    ##Joystick and button send array
    data = [0x01, 0x00, 0x01, 0x00, 0xff, 0x00, 0x00, 0x1f] 

    ##Button send setup
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
    data[1] = tmp[1]                            #  8 bit ... 
    tmp = int(abs(y)).to_bytes(2,'big', signed=False)
    data[2] = data[2] | ((tmp[0] << 6) & 0xC0)   
    data[2] = data[2] | (tmp[0] & 0x0c)          
    data[3] = tmp[1]                            
    
    print(bytes(data))  ##Debugging print
    
    #Send canmessage, buttons and joystick
    message = Message(id=id, data=bytes(data), extended=True)
    #can_bus.send(message)
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
            x_list.append(65536 - xaxi.value)   #inverted        
        for i in range(10):
            y_list.append(yaxi.value)
        x_list.sort()
        y_list.sort()
        x = x_list[1000]
        y = y_list[5]
        if abs(x - center_x) < dead_zone:
            x = center_x
        if abs(y - center_y) < dead_zone:
            y = center_y
            
        #print(x,y)     ##Debugging print
      
        await send_joystick_position(x, y)
        await asyncio.sleep(0.01)
        
##Listening on bus for filtered messages.
async def listen_can(listener):
    led_1.value = leds[0]
    led_2.value = leds[1]
    led_3.value = leds[2]
    led_4.value = leds[3]
    led_5.value = leds[4]
    led_6.value = leds[5]
    led_7.value = leds[6]
    led_8.value = leds[7]
    led_9.value = leds[8]
    
    while True:
        message_count = listener.in_waiting()
        for _i in range(message_count):
            msg = listener.receive()
            
            #print("Message from: ", hex(msg.id))   ##Debugging print
            #print(msg.data)
            
            if msg.id == 0x18eff102:
                k = msg.data[0]
                c = int((msg.data[1]&0xF0) >> 4)
                led_status[k-1].value= (c==0)		#OK
              
        await asyncio.sleep(0.01)

##setup filters to subscribe
async def main():
    matches = [
           Match(0x00ef0002,0xFF,True),         ##Filter 1
           Match(0x666,0xFFF,True),             ##Filter 2
           ]
    
    with can_bus.listen(matches) as listener:
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
