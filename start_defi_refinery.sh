#!/bin/bash

cd /home/dalien/Refinery-01

source env/bin/activate

while true
do
    echo "================================="
    echo "Running DeFi Refinery Generator"
    date

    python3 defi_liquidation_generator.py

    echo "Cycle complete."
    echo "Sleeping 300 seconds..."

    sleep 300
done

