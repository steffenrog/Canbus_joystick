import board
import analogio
import time

start_time = time.monotonic()

yaxi = analogio.AnalogIn(board.GP26_A0)
xaxi = analogio.AnalogIn(board.GP27_A1)


readings = 0

while True:
        x = xaxi.value
        y = yaxi.value
        elapsed_time = time.monotonic() - start_time
        elapsed_time_format = "{:.2f}".format(elapsed_time)
        readings += 1
        readingsWanted = 1000
        if(readings == readingsWanted):
            print("{} sek - x: {}, y: {}, Readings done: {}".format(elapsed_time_format, x, y,readings))


# while True:
#     x = xaxi.value
#     y = yaxi.value
#     print (x,y)