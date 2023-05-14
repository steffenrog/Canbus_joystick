import can
import time
import argparse
import curses

# Define IDs as in your VESC simulator
myID  = 0x0041
myID2 = 0x0300 | myID

def send_speed(bus, speed):
    # Your speed value should be an integer. If it's not, you should convert it to an integer value.
    speed = int(speed)

    # Convert the speed to bytes
    speed_bytes = speed.to_bytes(2, 'big', signed=True)

    # Create a dummy position value
    pos_bytes = (0).to_bytes(4, 'big', signed=True)

    # Create the data for the CAN message
    data = bytearray(8)  # Initialize an 8 byte long bytearray
    data[1:5] = pos_bytes
    data[5:7] = speed_bytes

    # Create the CAN message and send it
    msg = can.Message(arbitration_id=myID, data=data, is_extended_id=False)
    bus.send(msg)
    print(f"Sent speed {speed} on {bus.channel_info}")

def send_position(bus, position):
    # Your position value should be an integer. If it's not, you should convert it to an integer value.
    position = int(position)

    # Convert the position to bytes
    pos_bytes = position.to_bytes(4, 'big', signed=True)

    # Create a dummy speed value
    speed_bytes = (0).to_bytes(2, 'big', signed=True)

    # Create the data for the CAN message
    data = bytearray(8)  # Initialize an 8 byte long bytearray
    data[1:5] = pos_bytes
    data[5:7] = speed_bytes

    # Create the CAN message and send it
    msg = can.Message(arbitration_id=myID, data=data, is_extended_id=False)
    bus.send(msg)
    print(f"Sent position {position} on {bus.channel_info}")

def main(stdscr):
    # Connect to the CAN bus
    bus = can.interface.Bus(channel='vcan0', bustype='socketcan')

    speed = 1000
    position = 1000

    while True:
        # Wait for a key press
        c = stdscr.getch()

        # If the key is the up arrow
        if c == curses.KEY_UP:
            speed += 1
            send_speed(bus, speed)

        # If the key is the down arrow
        elif c == curses.KEY_DOWN:
            speed -= 1
            send_speed(bus, speed)

        # If the key is the right arrow
        elif c == curses.KEY_RIGHT:
            position += 1
            send_position(bus, position)

        # If the key is the left arrow
        elif c == curses.KEY_LEFT:
            position -= 1
            send_position(bus, position)

if __name__ == "__main__":
    curses.wrapper(main)
