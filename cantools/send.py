import can

bus = can.Bus(interface='socketcan', channel='can0', receive_own_messages=True)


id_bits = 0x20
frame_type = 1  
remote = 0 
spare = 0 
data_length = 4 
data = [0, 0, 0x88, 0x13]  

msg = can.Message(arbitration_id=id_bits,
                  data=data,
                  is_extended_id=True,
                  is_remote_frame=remote,
                  dlc=data_length)
bus.send(msg)
print(msg)