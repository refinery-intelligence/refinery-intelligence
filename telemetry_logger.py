import os
import time
import datetime

LOG_FILE = "/home/dalien/Refinery-01/node_telemetry.csv"

def get_stats():
    # Gets CPU Load and Temperature from the M4800 hardware
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    load = os.getloadavg()[0]
    # Standard Linux thermal path
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000
    except:
        temp = 0
    return f"{timestamp},{load},{temp}\n"

# Create the file with headers if it doesn't exist
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w") as f:
        f.write("timestamp,cpu_load,temp_celsius\n")

print("Refinery-01 Telemetry Logger Started...")

while True:
    with open(LOG_FILE, "a") as f:
        f.write(get_stats())
    time.sleep(60) # Log every minute
