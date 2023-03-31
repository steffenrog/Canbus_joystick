import can
import time
import os

def log_can_messages(channel, bitrate, log_file, filters=None):
    can_bus = can.interface.Bus(channel=channel, bustype='socketcan', bitrate=bitrate, can_filters=filters)
    prev_timestamp = None

    with open(log_file, 'w') as file:
        while True:
            msg = can_bus.recv()  # Receive a CAN message
            current_timestamp = time.time_ns()  # Get the current time in nanoseconds

            if prev_timestamp is not None:
                time_diff_ns = current_timestamp - prev_timestamp
                file.write(f"Time difference: {time_diff_ns} ns\n")

            log_message = f"Timestamp: {msg.timestamp} ID: {msg.arbitration_id:08X} Data: {msg.data}\n"
            file.write(log_message)

            prev_timestamp = current_timestamp

if __name__ == "__main__":
    CHANNEL = 'can0'  # Set the CAN channel, e.g., 'can0' or 'can1'
    BITRATE = 500000  # Set the CAN bus bitrate, e.g., 500000 for 500 kbps
    LOG_FILE = 'canbus_log.txt'  # Set the name of the log file

    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, 'w').close()

    # Add a filter with a specific extended arbitration ID
    # For example, this filter will only log messages with extended arbitration ID 0x1234567
    FILTERS = [{"can_id": 0x1234567, "can_mask": 0x1FFFFFFF}]
    
    log_can_messages(CHANNEL, BITRATE, LOG_FILE, filters=FILTERS)
