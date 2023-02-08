import board
import analogio
import time

start_time = time.monotonic()

yaxi = analogio.AnalogIn(board.GP26_A0)
xaxi = analogio.AnalogIn(board.GP27_A1)


# readings = 0
# 
# while True:
#         x = xaxi.value
#         y = yaxi.value
#         elapsed_time = time.monotonic() - start_time
#         elapsed_time_format = "{:.2f}".format(elapsed_time)
#         readings += 1
#         readingsWanted = 1000
#         if(readings == readingsWanted):
#             print("{} sek - x: {}, y: {}, Readings done: {}".format(elapsed_time_format, x, y,readings))


center_x = 32768        
center_y = 32768
dead_zone = 650

while True:
    x_list = []
    y_list = []
    for i in range(200):
        x_list.append(xaxi.value)
        #x_list.append(65536 - xaxi.value)   #inverted - if Joystick is attached upside down        
    for i in range(200):
        y_list.append(yaxi.value)
        #y_list.append(65536 - yaxi.value)   #inverted - if Joystick is attached upside down
    x_list.sort()
    y_list.sort()
    x = x_list[100]
    y = y_list[100]
    if abs(x - center_x) < dead_zone:
        x = center_x
    if abs(y - center_y) < dead_zone:
        y = center_y
    print(x,y)     #Debugging print
    time.sleep(0.01)
