#!/bin/bash
echo "--- WebForge: Reclaiming System Control ---"

# 1. Kill the old Python "Manager" so it stops restarting
sudo pkill -9 -f "monitor_refinery.py"

# 2. Strip the 'program' permission from the old monitor script
chmod -x ~/Refinery-01/monitor_refinery.py 2>/dev/null

# 3. Force-clear Port 8080
sudo fuser -k 8080/tcp 2>/dev/null

# 4. Launch the new Node Gateway
nohup node ~/Refinery-01/server.js > /dev/null 2>&1 &

echo "--- WebForge: Deployment Complete ---"
echo "Monitor pings with: tail -f ~/Refinery-01/server.log"
