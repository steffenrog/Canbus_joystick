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
yaxi = analogio.AnalogIn(board.GP26_A0)
xaxi = analogio.AnalogIn(board.GP27_A1)
can_bus = CAN(spi, cs)
N = 10
readings = []
alpha = 0.6 # adjust this value as needed
x_filtered = 0
y_filtered = 0
##To use filters, 2 filters can be used
class Match:
    def __init__(self,address,mask,extended: bool):
        self.address = address
        self.mask = mask
        self.extended = extended

#Packing joystickvalues in 0-1000 range for now
async def send_joystick_position(x, y):
    if not (0 <= x <= 1000) or not (0 <= y <= 1000):
        return
    id = 0x18fdd602
    data = struct.pack("ff", x, y)
    message = Message(id=id, data=data, extended=True)
    can_bus.send(message)
    print(f"Joystick position sent: x={x}, y={y}")


async def send_joystick_position(x, y):
   # if not (-250 <= x <= 250) or not (-250 <= y <= 250):
    #    return
    id = 0x18fdd6F1
    # Create a new byte array with the same size and structure as the button array
    data = bytearray([0x01, 0x00, 0x01, 0x00, 0xff, 0x00, 0x00, 0x1f])
    # Set the x and y values in the correct positions
    if x < 0:
        data[0] = 0x10
    if y < 0:
        data[2] = 0x10
    data[1] = abs(x)
    data[3] = abs(y)
    # Send the message
    message = Message(id=id, data=data, extended=True)
   # can_bus.send(message)
    #print(f"Joystick position sent: x={x}, y={y}")
    #print(data[3])
    
   # print(message.data)
    
    



async def read_joystick_position():
     global readings, x_filtered, y_filtered
     while True:
         x = xaxi.value
         y = yaxi.value
         x_filtered = alpha * x + (1 - alpha) * x_filtered
         y_filtered = alpha * y + (1 - alpha) * y_filtered
         x_scaled = x_filtered / 65.48
         y_scaled = y_filtered / 65.52
         readings.append((x_scaled, y_scaled))
         readings = readings[-N:]
         x_avg = sum([x for x, _ in readings]) / N
         y_avg = sum([y for _, y in readings]) / N
         #print(y_avg)
         print(x_avg, y_avg)
         await send_joystick_position(x_avg, y_avg)
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
               
        await asyncio.sleep(0)

async def main():
    matches = [
           Match(0xF1,0xFF,True),
           Match(0x666,0xFFF,True),
           ]
    with can_bus.listen(matches) as listener:
        task1 = asyncio.create_task(listen_can(listener))
        task2 = asyncio.create_task(read_joystick_position())
        await asyncio.gather(task1, task2)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Program ended")
