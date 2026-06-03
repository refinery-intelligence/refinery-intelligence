#!/bin/bash

echo "=============================="
echo "REFINERY SYSTEM HEALTH CHECK"
echo "=============================="

echo ""
echo "----- NGINX STATUS -----"
systemctl status nginx --no-pager

echo ""
echo "----- CLOUDFLARED STATUS -----"
systemctl status cloudflared --no-pager

echo ""
echo "----- REFINERY STATUS -----"
systemctl status refinery --no-pager

echo ""
echo "----- ENABLED SERVICES -----"
systemctl is-enabled nginx
systemctl is-enabled cloudflared
systemctl is-enabled refinery

echo ""
echo "----- CRON TIMERS -----"
crontab -l

echo ""
echo "----- HISTORY FILE -----"
tail -5 ~/Refinery-01/data/defi-flow-intel-history.jsonl

echo ""
echo "----- CRAWLER CHECK -----"
grep -iE "bot|crawl|spider|gpt|anthropic|google" /var/log/nginx/access.log | tail -20

echo ""
echo "----- SSL CERTIFICATE -----"
openssl s_client -connect api.dalien.net:443 -servername api.dalien.net </dev/null 2>/dev/null | openssl x509 -noout -dates

echo ""
echo "=============================="
echo "REFINERY HEALTH CHECK COMPLETE"
echo "=============================="

