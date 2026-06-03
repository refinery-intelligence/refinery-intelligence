import subprocess
import time
import os

# Define the paths to your infrastructure components
BASE_DIR = os.path.expanduser("~/Refinery-01")
GATE_SCRIPT = os.path.join(BASE_DIR, "refinery_gate.py")
CRAWL_SCRIPT = os.path.join(BASE_DIR, "bot_crawl.py")

def launch_refinery():
    print("--- Initializing Refinery-01 Infrastructure ---")
    
    # 1. Start the Sanitizer Gate in the background
    print("Starting Sanitizer Gate...")
    gate_process = subprocess.Popen(["python3", GATE_SCRIPT])
    
    try:
        while True:
            # 2. Trigger the Bot Crawl (The Data/Value Flow)
            print("\nTriggering scheduled Pulse...")
            subprocess.run(["python3", CRAWL_SCRIPT])
            
            # 3. Interval between Pulses (e.g., every hour)
            print("Pulse complete. Standing by for next cycle.")
            time.sleep(3600) 
            
    except KeyboardInterrupt:
        print("\nShutting down Refinery-01...")
        gate_process.terminate()

if __name__ == "__main__":
    launch_refinery()
