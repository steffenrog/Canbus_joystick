# Author: Steffen Rogne
# Brief:  Test software, read canbus with filter. Read Analog Joystick, send joystick values over can.
# 
#==================================================

import board
import analogio
import busio
from digitalio import DigitalInOut
from adafruit_mcp2515.canio import Message
from adafruit_mcp2515 import MCP2515 as CAN
import asyncio
import struct

cs = DigitalInOut(board.GP17)
cs.switch_to_output()
spi = busio.SPI(board.GP18, board.GP19, board.GP16)
xaxi = analogio.AnalogIn(board.GP26_A0)
yaxi = analogio.AnalogIn(board.GP27_A1)

can_bus = CAN(spi, cs)

class Match:
    def __init__(self,address,mask,extended: bool):
        self.address = address
        self.mask = mask
        self.extended = extended
       # print(f"address: {self.address}, mask: {self.mask}, extended: {self.extended}")



def get_analog_values():
    x = xaxi.value
    y = yaxi.value
    return (x, y)

async def send_joystick_position(x, y):
    if not (0 <= x <= 1000) or not (0 <= y <= 1000):
        return
    id = 0x020
    data = struct.pack("ff", x, y)
    message = Message(id=id, data=data, extended=True)
    can_bus.send(message)
    print(f"Joystick position sent: x={x}, y={y}")

async def read_joystick_position():
    while True:
        (x, y) = get_analog_values()
        x = x / 65535 * 1000
        y = y / 65535 * 1000
        print(x,y)
        await send_joystick_position(x, y)
        await asyncio.sleep(0.1)

async def listen_can(listener):
    while True:
        message_count = listener.in_waiting()
        for _i in range(message_count):
            msg = listener.receive()
            print("Message from: ", hex(msg.id))
            print(msg.data)
            #do something with the data
        
        await asyncio.sleep(0.1)

async def main():
    matches = [
           Match(0xF1,0xFF,True),
           Match(0x941,0xFFF,True),
           ]
    with can_bus.listen(matches) as listener:
        task1 = asyncio.create_task(listen_can(listener))
        task2 = asyncio.create_task(read_joystick_position())
        await asyncio.gather(task1, task2)
        while(True):
            message_count = listener.in_waiting()
            for _i in range(message_count):
                msg = listener.receive()
                print("Message from: ", hex(msg.id))
                print(msg.data)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Program ended")
