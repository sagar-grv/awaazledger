#!/bin/bash
set -e

cd "$(dirname "$0")/../backend"
if [ ! -d "venv" ]; then
    echo "Creating Python virtualenv..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt
python ../scripts/seed_db.py
uvicorn app.main:app --reload --port 8000
