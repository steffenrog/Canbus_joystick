import can
import time

bus = can.interface.Bus(bustype='socketcan', channel='can0', bitrate=250000)

while True:
    payload = input("Enter the payload : ")
    data_payload = bytes.fromhex(payload)
    arbitration_id = 0x020
    pl = can.Message(arbitration_id=arbitration_id, data=data_payload, is_extended_id=False)
    bus.send(pl)
    print ('Message sent!')