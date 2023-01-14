# Author: Steffen Rogne
# Brief:  CAN bus test software - receiving
# 
#==================================================


import can
import struct

bus = can.interface.Bus(bustype='socketcan', channel='can0')

arbitration_id = 0x20

def receive_joystick_position():
    while True:
        message = bus.recv()
        if message.arbitration_id == arbitration_id:
            x, y = struct.unpack("ff", message.data)
            x = x 
            y = y 
            print("Joystick position received: x={:.2f}, y={:.2f}".format(x, y))

receive_joystick_position()
