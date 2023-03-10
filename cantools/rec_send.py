import can
import time
import threading

bus = can.interface.Bus(bustype='socketcan', channel='can1', bitrate=250000)

while True:
  msg = bus.recv()
  if msg.arbitration_id == 0x20 and msg.data == b'\x01\x00\x01\x00\xFF\x40\x30\x1F':
    arbitration_id= 0x030
    data_payload = bytes.fromhex('0000000000000001')
    pl = can.Message(arbitration_id=arbitration_id,data=data_payload, is_extended_id=False)
    bus.send(pl)

