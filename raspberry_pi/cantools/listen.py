import can


bus = can.interface.Bus(bustype='socketcan', channel='can0', baudrate="500000")

prev_message = None

while True:
    message = bus.recv(1)
    if message != prev_message:
        print(message)
        prev_message = message
