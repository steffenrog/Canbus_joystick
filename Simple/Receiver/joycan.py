import can
import struct

bus = can.interface.Bus(bustype='socketcan', channel='can0')

joystick_id = 0x20


while True:
    message = bus.recv()
    if message.arbitration_id == joystick_id:
        x, y = struct.unpack("ff", message.data)
        x = x 
        y = y 
        print("Joystick position received: x={:.2f}, y={:.2f}".format(x, y))
        #print(message.data)



