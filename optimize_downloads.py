#!/usr/bin/env python3
"""
Download optimization wrapper for aria2c integration
This script optimizes yt-dlp commands to use aria2c automatically
"""

import subprocess
import sys
import re

def optimize_ytdlp_command(original_cmd):
    """Add aria2c optimization to yt-dlp commands"""
    
    # Check if it's a yt-dlp command and doesn't already have aria2c
    if 'yt-dlp' in original_cmd and '--external-downloader aria2c' not in original_cmd:
        
        # Define aria2c optimization parameters
        aria2c_params = [
            '--external-downloader', 'aria2c',
            '--external-downloader-args', 'aria2c:--max-connection-per-server=16 --min-split-size=1M --split=16 --max-download-limit=0 --connect-timeout=10 --timeout=10 --max-tries=3 --retry-wait=2',
            '--concurrent-fragments', '16',
            '--fragment-retries', '25',
            '--http-chunk-size', '10M',
            '--buffer-size', '16K'
        ]
        
        # Insert optimization parameters after 'yt-dlp'
        cmd_parts = original_cmd.split()
        for i, part in enumerate(cmd_parts):
            if 'yt-dlp' in part:
                # Insert aria2c params after yt-dlp
                optimized_cmd = cmd_parts[:i+1] + aria2c_params + cmd_parts[i+1:]
                return ' '.join(optimized_cmd)
    
    return original_cmd

def main():
    if len(sys.argv) < 2:
        print("Usage: python optimize_downloads.py 'yt-dlp command'")
        sys.exit(1)
    
    original_command = ' '.join(sys.argv[1:])
    optimized_command = optimize_ytdlp_command(original_command)
    
    print(f"🚀 Optimized command: {optimized_command}")
    
    # Execute the optimized command
    result = subprocess.run(optimized_command, shell=True)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()