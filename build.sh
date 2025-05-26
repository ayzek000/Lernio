#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Initialize Supabase database
python init_supabase.py

echo "Build completed successfully!"
