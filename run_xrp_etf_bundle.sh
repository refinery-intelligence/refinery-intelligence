#!/bin/bash

cd /home/dalien/Refinery-01

while true
do
    python3 vault/datasets/xrp-etf-temporal-intel-v1/generator.py
    python3 enrich_xrp_etf_private_outputs.py
    python3 enrich_xrp_etf_v13_delta.py
    sleep 300
done
