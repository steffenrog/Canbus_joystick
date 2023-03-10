import can
bus = can.interface.Bus(bustype='socketcan', channel='vcan0')

import time
start_time = time.monotonic()
stop_time = start_time + 60
total_bits = 0
while time.monotonic() < stop_time:
    message = bus.recv()
    if message is not None:
        total_bits += message.dlc * 8

print(f"Total bits seen: {total_bits}")
