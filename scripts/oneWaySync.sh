#!/bin/sh
# Run habiticaTodo, avoid proxy.
unset http_proxy
unset https_proxy

pwd
cd source
python3.9 one_way_sync.py
