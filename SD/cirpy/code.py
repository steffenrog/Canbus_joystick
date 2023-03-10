import board
import analogio
import busio
from digitalio import DigitalInOut, Direction, Pull
import asyncio
import struct
from adafruit_mcp2515.canio import Message, Match
from adafruit_mcp2515 import MCP2515 as CAN
import math
import time

cs = DigitalInOut(board.GP17)
cs.switch_to_output()
spi = busio.SPI(board.GP18, board.GP19, board.GP16)
can_bus = CAN(spi, cs)

yaxi = analogio.AnalogIn(board.GP26_A0)
xaxi = analogio.AnalogIn(board.GP27_A1)
#zaxi = analogio.AnalogIn(board.GP28_A2)

buttons = [DigitalInOut(board.GP5), DigitalInOut(board.GP7), DigitalInOut(board.GP9), DigitalInOut(board.GP11), DigitalInOut(board.GP13), DigitalInOut(board.GP3)] ##Finnal layout
for btn in buttons:
    btn.direction = Direction.INPUT
    btn.pull = Pull.UP

led_status = [DigitalInOut(board.GP6), DigitalInOut(board.GP8), DigitalInOut(board.GP10), DigitalInOut(board.GP12), DigitalInOut(board.GP14), DigitalInOut(board.GP2), DigitalInOut(board.GP4), DigitalInOut(board.GP1), DigitalInOut(board.GP0)] ##Finnal layout
for led in led_status:
    led.direction = Direction.OUTPUT
    led.value = False

def slow_blink(led):
    while True:
        led.value = not led.value
        time.sleep(1)
    
def med_blink(led):
    while True:
        led.value = not led.value
        time.sleep(0.5)
    
def fast_blink(led):
    while True:
        led.value = not led.value
        time.sleep(0.1)
    
##Send joystick values, adapted to receiving software. Default: id = 0x18fdd6F1 -To speak with SeaDrive software.
async def send_joystick_position(x, y, button_value):
    id = 0x18fdd6F1 #ID mimics Grayhill
    joy_res = 12	#Default value 12, options 8, 10, 12.
    
    ##Joystick calculations
    x = ((x/2**16)*(2**(joy_res+1)))-(2**joy_res) #Works pretty good 
    y = ((y/2**16)*(2**(joy_res+1)))-(2**joy_res) #Works pretty good
    
    ##CAN send array
    data = [0x01, 0x00, 0x01, 0x00, 0xff, 0x00, 0x00, 0x1f]
    ##Button send values,
    if button_value[0]:
        data[5] = data[5] | 0x40
    if button_value[1]:
        data[5] = data[5] | 0x10
    if button_value[2]:
        data[5] = data[5] | 0x04
    if button_value[3]:
        data[5] = data[5] | 0x01
    if button_value[4]:
        data[6] = data[6] | 0x04
    if button_value[5]:
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
    #print(x,y)
    ##Send canmessage, buttons and joystick
    message = Message(id=id, data=bytes(data), extended=True)
    can_bus.send(message)                                                     #Comment line to run without can.
    await asyncio.sleep(0.10)    

##Read analog input, oversamling with middle
async def read_joystick_position():
    center_x = 32768        
    center_y = 32768
    dead_zone = 2000
    while True:
        x_list = []
        y_list = []
        for i in range(500):
            x_list.append(xaxi.value)
            #x_list.append(65536 - xaxi.value)   #inverted - if Joystick is attached upside down        
        for i in range(500):
            #y_list.append(yaxi.value)
            y_list.append(65536 - yaxi.value)   #inverted - if Joystick is attached upside down
        x_list.sort()
        y_list.sort()
        x = x_list[250]
        y = y_list[250]
        if abs(x - center_x) < dead_zone:
            x = center_x
        if abs(y - center_y) < dead_zone:
            y = center_y           
        button_value = [not btn.value for btn in buttons]
        #print(x,y, button_values)     #Debugging print
        
        await send_joystick_position(x, y, button_value)
        await asyncio.sleep(0)
        
##Listening on bus, and set led states.
async def listen_can(listener):
     ##The old Grayhill way:#######
#    while True:
#        message_count = listener.in_waiting()
#        for _i in range(message_count):
#            msg = listener.receive()
            
            #print(msg.id,msg.data)		#Debugging print

#            if msg.id == 0x18eff102:	##Communication tGP11o joystick handler
#                k = msg.data[0]						##"k" is key from other part of receiving software
#                c = int((msg.data[1]&0xF0) >> 4)	##"c" is center led from other part of receiving software
#                led_status[k-1].value= (c==0)		#OK	
              
#        await asyncio.sleep(0)

    ##The new way:
    while True:
        message_count = listener.in_waiting()
        for _i in range(message_count):
            msg= listener.receive()
            #print(msg.id,msg.data)

            if msg.id == 0x18eff102:
                #print("received message with id 0x18eff102 and data", msg.data)
                for i in range(9):
                    if i % 2:
                        led_value = msg.data[math.floor(i/2)] & 0x0f
                    else:
                        led_value = (msg.data[math.floor(i/2)] >> 4) & 0x0f
                    #print("led value for led", i, "is", led_value)
                    if led_value == 0x10:
                        led_status[i].value = False
                    elif led_value == 0x00:
                        led_status[i].value = True
                    elif led_value == 0x20:
                        slow_blink(led_status[i])
                    elif led_value == 0x30:
                        med_blink(led_status[i])
                    elif led_value == 0x40:
                        fast_blink(led_status[i])    
                    else:
                        led_status[i].value = not led_value % 2
                    #print("led status for led", i, "is", led_status[i].value)
                        
        await asyncio.sleep(0)

##Starting main, setup filters to subscribe
async def main():
    match = [Match(address=0x00ef0002, mask=0xFF, extended=True), Match(address=0xF3, mask=0xFF, extended=True)]
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