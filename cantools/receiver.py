import can

bus = can.interface.Bus(bustype='socketcan',channel='can0',bitrate=250000)
prev_message = None

while True:

  message = bus.recv(1)

  if message != prev_message:
    print(message)
#    print('    ')
#    for x in range(len(message)):
#       print(message[x])

  prev_message = message
