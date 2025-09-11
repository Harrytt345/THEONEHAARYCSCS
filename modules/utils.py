import random
import time
import math
import os
import glob
import shutil
from vars import CREDIT
from pyrogram.errors import FloodWait
from datetime import datetime, timedelta

class Timer:
    def __init__(self, time_between=5):
        self.start_time = time.time()
        self.time_between = time_between

    def can_send(self):
        if time.time() > (self.start_time + self.time_between):
            self.start_time = time.time()
            return True
        return False

# lets do calculations
def hrb(value, digits=2, delim="", postfix=""):
    """Return a human-readable file size.
    """
    if value is None:
        return None
    chosen_unit = "B"
    for unit in ("KB", "MB", "GB", "TB"):
        if value > 1000:
            value /= 1024
            chosen_unit = unit
        else:
            break
    return f"{value:.{digits}f}" + delim + chosen_unit + postfix

def hrt(seconds, precision=0):
    """Return a human-readable time delta as a string.
    """
    pieces = []
    value = timedelta(seconds=seconds)

    if value.days:
        pieces.append(f"{value.days}day")

    seconds = value.seconds

    if seconds >= 3600:
        hours = int(seconds / 3600)
        pieces.append(f"{hours}hr")
        seconds -= hours * 3600

    if seconds >= 60:
        minutes = int(seconds / 60)
        pieces.append(f"{minutes}min")
        seconds -= minutes * 60

    if seconds > 0 or not pieces:
        pieces.append(f"{seconds}sec")

    if not precision:
        return "".join(pieces)

    return "".join(pieces[:precision])

timer = Timer()

async def progress_bar(current, total, reply, start):
    if timer.can_send():
        now = time.time()
        diff = now - start
        if diff < 1:
            return
        else:
            perc = f"{current * 100 / total:.1f}%"
            elapsed_time = round(diff)
            speed = current / elapsed_time
            remaining_bytes = total - current
            if speed > 0:
                eta_seconds = remaining_bytes / speed
                eta = hrt(eta_seconds, precision=1)
            else:
                eta = "-"
            sp = str(hrb(speed)) + "/s"
            tot = hrb(total)
            cur = hrb(current)
            bar_length = 10
            completed_length = int(current * bar_length / total)
            remaining_length = bar_length - completed_length

            symbol_pairs = [
                ("🟩", "⬜")
            ]
            chosen_pair = random.choice(symbol_pairs)
            completed_symbol, remaining_symbol = chosen_pair

            progress_bar = completed_symbol * completed_length + remaining_symbol * remaining_length

            try:
                await reply.edit(f'<blockquote>`╭──⌯═════𝐁𝐨𝐭 𝐒𝐭𝐚𝐭𝐢𝐜𝐬══════⌯──╮\n├⚡ {progress_bar}\n├⚙️ Progress ➤ | {perc} |\n├🚀 Speed ➤ | {sp} |\n├📟 Processed ➤ | {cur} |\n├🧲 Size ➤ | {tot} |\n├🕑 ETA ➤ | {eta} |\n╰─═══✨🦋{CREDIT}🦋✨═══─╯`</blockquote>')
            except FloodWait as e:
                time.sleep(e.x)

def cleanup_temp_files(cleanup_type="initial"):
    """
    Ultra-robust cleanup function to remove all temporary files and assets.
    
    Args:
        cleanup_type (str): "initial" for pre-download cleanup, "final" for post-download cleanup
    
    Returns:
        int: Number of files cleaned
    """
    # Import globals to check processing state
    try:
        from . import globals
        # Prevent cleanup during active processing unless it's final cleanup
        if cleanup_type == "initial" and globals.processing_request:
            print("⏸️ Skipping cleanup - post-processing still in progress")
            return 0
    except ImportError:
        # If globals not available, proceed with cleanup
        pass
    # Comprehensive file patterns for all possible temporary files
    cleanup_patterns = [
        # Video formats
        "*.mp4", "*.mkv", "*.avi", "*.mov", "*.wmv", "*.flv", "*.webm", "*.m4v", "*.3gp", "*.ogv",
        
        # Audio formats  
        "*.mp3", "*.wav", "*.flac", "*.aac", "*.ogg", "*.m4a", "*.wma", "*.opus", "*.aiff",
        
        # Document formats
        "*.pdf", "*.doc", "*.docx", "*.txt", "*.rtf", "*.odt", "*.epub", "*.mobi",
        
        # Image formats
        "*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.tiff", "*.svg", "*.ico", "*.webp",
        
        # Archive formats
        "*.zip", "*.rar", "*.7z", "*.tar", "*.gz", "*.bz2", "*.xz", "*.tar.gz", "*.tar.bz2",
        
        # Web formats
        "*.html", "*.htm", "*.css", "*.js", "*.json", "*.xml", "*.rss",
        
        # Temporary file patterns
        "*.tmp", "*.temp", "*.temporary", "*.cache", "*.log", "*.bak", "*.backup",
        "*.part", "*.partial", "*.download", "*.downloading", "*.crdownload",
        "*.temp.*", "*.tmp.*", "*temp*", "*tmp*", "*cache*", "*backup*",
        "*.temp.mp4", "*.temp.mkv", "*.temp.avi", "*.temp.webm",
        
        # Thumbnails and previews
        "thumb.*", "thumbnail.*", "preview.*", "*.thumb", "*.thumbnail", "*.preview",
        
        # Session and database temp files
        "*.session-journal", "*.db-journal", "*.sqlite-journal", "*.lock",
        
        # Media processing temp files
        "*.ytdl", "*.f4v", "*.f4a", "*.m3u8", "*.ts", "*.vtt", "*.srt", "*.ass", "*.X",
        
        # System temp files
        "*.pyc", "*.pyo", "*.pyd", "__pycache__/*", ".DS_Store", "Thumbs.db"
    ]
    
    # Directories to clean completely
    cleanup_dirs = [
        "downloads",
        "temp", 
        "tmp",
        "cache",
        "__pycache__",
        ".temp",
        "attached_assets"  # Clean attached assets as requested
    ]
    
    cleaned_files = []
    
    # Clean files in current directory using patterns
    for pattern in cleanup_patterns:
        if "/" not in pattern and "*" in pattern:  # Pattern-based cleanup
            for file_path in glob.glob(pattern):
                try:
                    if os.path.isfile(file_path):
                        # Preserve active bot session files
                        if "bot.session" in file_path and "journal" not in file_path:
                            continue
                        # Preserve youtube cookies and core config files
                        if file_path in ["youtube_cookies.txt", "vars.py", "main.py", "app.py"]:
                            continue
                            
                        os.remove(file_path)
                        cleaned_files.append(file_path)
                except Exception:
                    continue
        elif "/" not in pattern and "*" not in pattern:  # Specific file cleanup
            try:
                if os.path.isfile(pattern):
                    os.remove(pattern)
                    cleaned_files.append(pattern)
            except Exception:
                continue
    
    # Clean directories completely
    for dir_name in cleanup_dirs:
        if os.path.exists(dir_name):
            try:
                # Remove all files in directory
                for root, dirs, files in os.walk(dir_name):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                            cleaned_files.append(file_path)
                        except Exception:
                            continue
                    
                    # Remove empty subdirectories
                    for dir_path in dirs:
                        full_dir_path = os.path.join(root, dir_path)
                        try:
                            if not os.listdir(full_dir_path):  # If directory is empty
                                os.rmdir(full_dir_path)
                        except Exception:
                            continue
                            
            except Exception:
                pass
    
    # Clean any orphaned session files (except main bot session)
    session_patterns = ["*.session*", "device_*", "*.db-*"]
    for pattern in session_patterns:
        for file_path in glob.glob(pattern):
            try:
                if (os.path.isfile(file_path) and 
                    "bot.session" not in file_path and 
                    "journal" in file_path):
                    os.remove(file_path)
                    cleaned_files.append(file_path)
            except Exception:
                continue
    
    # Recursive cleanup for hidden temp files
    try:
        for root, dirs, files in os.walk("."):
            for file in files:
                if (file.startswith('.tmp') or 
                    file.startswith('.temp') or 
                    file.endswith('.tmp') or
                    file.endswith('.temp') or
                    'temp' in file.lower() and file != 'youtube_cookies.txt'):
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        cleaned_files.append(file_path)
                    except Exception:
                        continue
    except Exception:
        pass
    
    return len(cleaned_files)

def final_cleanup():
    """
    Final cleanup after download completion - more aggressive cleanup
    """
    return cleanup_temp_files(cleanup_type="final")
