import can
import struct

bus = can.interface.Bus(bustype='socketcan', channel='can0')

my_id = 0x0000f300
joystick_id = 0x20

def receive_joystick_position():
    while True:
        message = bus.recv()
        if message.arbitration_id == joystick_id:
            x, y = struct.unpack("ff", message.data)
            x = x 
            y = y 
            print("Joystick position received: x={:.2f}, y={:.2f}".format(x, y))
            #print(message.data)
receive_joystick_position()


