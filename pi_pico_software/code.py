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

import board
import analogio
import busio
from digitalio import DigitalInOut
from adafruit_mcp2515.canio import Message
from adafruit_mcp2515 import MCP2515 as CAN
import asyncio
import struct
import math

cs = DigitalInOut(board.GP17)
cs.switch_to_output()
spi = busio.SPI(board.GP18, board.GP19, board.GP16)
xaxi = analogio.AnalogIn(board.GP26_A0)
yaxi = analogio.AnalogIn(board.GP27_A1)
can_bus = CAN(spi, cs)

##To use filters, 2 filters can be used
class Match:
    def __init__(self,address,mask,extended: bool):
        self.address = address
        self.mask = mask
        self.extended = extended

##Packing joystickvalues in 0-1000 range for now
async def send_joystick_position(x, y):
    if not (0 <= x <= 1000) or not (0 <= y <= 1000):
        return
    id = 0x020
    data = struct.pack("ff", x, y)
    message = Message(id=id, data=data, extended=True)
    can_bus.send(message)
    print(f"Joystick position sent: x={x}, y={y}")

##Possible filter to test.
# N = 5
# readings = []
# alpha = 0.7 # adjust this value as needed
# x_filtered = 0
# y_filtered = 0
# 
# async def read_joystick_position():
#     global readings, x_filtered, y_filtered
#     while True:
#         x = xaxi.value
#         y = yaxi.value
#         x_filtered = alpha * x + (1 - alpha) * x_filtered
#         y_filtered = alpha * y + (1 - alpha) * y_filtered
#         x_scaled = x_filtered / 64920 * 1000
#         y_scaled = y_filtered / 65200 * 1000
#         readings.append((x_scaled, y_scaled))
#         readings = readings[-N:]
#         x_avg = sum([x for x, _ in readings]) / N
#         y_avg = sum([y for _, y in readings]) / N
#         print(x_avg, y_avg)
#         await send_joystick_position(x_avg, y_avg)
#         await asyncio.sleep(0.1)

##Stable reading at 0-500-1000. Tmp stable readings.
async def read_joystick_position():
    while True:
        x = xaxi.value / 65200 * 1000
        y = yaxi.value / 64000 * 1000
        
        scale_x = 100/3
        scale_y = 100/3
        
        xamounts = math.floor(x/scale_x)
        yamounts = math.floor(y/scale_y)
        
        xclamped = scale_x*xamounts
        yclamped = scale_y*yamounts
        xclamped-=500
        yclamped-=500
        await send_joystick_position(round(xclamped), round(yclamped))
        await asyncio.sleep(0.01)

#Listening on bus for filtered messages.
async def listen_can(listener):
    while True:
        message_count = listener.in_waiting()
        for _i in range(message_count):
            msg = listener.receive()
            print("Message from: ", hex(msg.id))
            print(msg.data)

            #do something with the data
               
        await asyncio.sleep(0.01)

async def main():
    matches = [
         #  Match(0xF1,0xFF,True),
           Match(0x941,0xFFF,True),
           ]
    with can_bus.listen(matches) as listener:
        task1 = asyncio.create_task(listen_can(listener))
        task2 = asyncio.create_task(read_joystick_position())
        await asyncio.gather(task1, task2)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Program ended")

