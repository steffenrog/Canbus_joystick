import can
import time

arbitration_id = 0x20

def setbutton(buttonarray, x, y):
  button = [0x01,0x00,0x01,0x00,0xff,0x00,0x30,0x1f]
  for b in buttonarray:
    if b == 1:
      button[5]= button[5] | 0x40
    if b == 2:
      button[5]= button[5] | 0x10
    if b == 3:
      button[5]= button[5] | 0x04
    if b == 4:
      button[5]= button[5] | 0x01
    if b == 5:
      button[5]= button[6] | 0x40
    if b == 6:
      button[5]= button[6] | 0x10
    if b == 7:
      button[5]= button[6] | 0x04

  button[1]=x
  button[3]=y

  msg = can.Message(arbitration_id=arbitration_id,data=button, is_extended_id=True)
  bus.send(msg)
  time.sleep(0.1)

bus = can.interface.Bus(channel='can0',bustype='socketcan')
#-----------------------------------------------------------------

setbutton([1],0,0)
setbutton([2],0,0)
setbutton([3],0,0)
setbutton([4],0,0)

setbutton([1],0,0)
time.sleep(1)
setbutton([3],0,0)
time.sleep(1)
setbutton([3],0,0)
time.sleep(1)

setbutton([],100,200)
time.sleep(1)