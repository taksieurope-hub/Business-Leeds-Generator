#!/bin/bash
cd /app/backend
source /root/.venv/bin/activate
python lead_seeder_v2.py --count 50000 >> /tmp/seeder.log 2>&1
