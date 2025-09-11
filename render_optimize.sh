#!/bin/bash
# Ultra-fast deployment setup for Render

# Install system-level optimizations
apt-get update && apt-get install -y aria2 ffmpeg

# Python optimizations
pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r pyproject.toml

# Set optimal Python flags
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Networking optimizations  
export AIOHTTP_NO_EXTENSIONS=1
export PYTHONASYNCIODEBUG=0

# Memory optimizations
export PYTHONMALLOC=malloc

# Start with optimized settings
python main.py