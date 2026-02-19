#!/bin/bash
# Helper script to run the daily challenge post
# This activates the virtual environment and runs the script

cd "$(dirname "$0")"
source venv/bin/activate
python post_daily_challenge.py
