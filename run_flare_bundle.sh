#!/bin/bash

cd /home/dalien/Refinery-01

while true
do
    python3 vault/datasets/flare-temporal-intel-v1/generator.py
    sleep 300
done
