from vars import REPO_URL
import os
import re
import sys
import m3u8
import json
import time
import pytz
import asyncio
import requests
import subprocess
import urllib
import urllib.parse
import yt_dlp
import tgcrypto
import cloudscraper
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64encode, b64decode
from modules.logs import logging
from bs4 import BeautifulSoup
from modules import saini as helper
from modules.html_handler import html_handler
from modules.drm_handler import drm_handler
from modules import globals
from modules.authorisation import add_auth_user, list_auth_users, remove_auth_user
from modules.broadcast import broadcast_handler, broadusers_handler
from modules.text_handler import text_to_txt
from modules.youtube_handler import ytm_handler, y2t_handler, getcookies_handler, cookies_handler
from modules.utils import progress_bar
from vars import api_url, api_token, token_cp, adda_token, photologo, photoyt, photocp, photozip
from vars import API_ID, API_HASH, BOT_TOKEN, OWNER, CREDIT, AUTH_USERS, TOTAL_USERS, cookies_file_path
from aiohttp import ClientSession
from subprocess import getstatusoutput
from pytube import YouTube
from aiohttp import web
import random
from pyromod import listen
from pyrogram.client import Client
from pyrogram import filters
from pyrogram.types import Message, InputMediaPhoto
from pyrogram.errors import FloodWait, PeerIdInvalid, UserIsBlocked, InputUserDeactivated
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
import aiofiles
import zipfile
import shutil
import ffmpeg

# Initialize the bot - Railway compatible (fixes SQLite error)
bot = Client(
    "railway_bot",
    api_id=int(os.environ.get("API_ID") or API_ID),
    api_hash=os.environ.get("API_HASH") or API_HASH,
    bot_token=os.environ.get("BOT_TOKEN") or BOT_TOKEN,
    in_memory=True  # THIS FIXES THE SQLITE ERROR ON RAILWAY
)

# Add Flask web server for Render compatibility with live progress tracking
from flask import Flask, jsonify, render_template_string
from threading import Thread
import threading
import json
from datetime import datetime

web_app = Flask(__name__)

# Global progress tracking for live updates
progress_data = {
    'current_downloads': {},
    'completed_downloads': [],
    'stats': {
        'total_files_processed': 0,
        'active_downloads': 0,
        'last_activity': None
    }
}

@web_app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>SAINI DRM Bot - Live Progress</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: Arial, sans-serif; background: #1a1a1a; color: #fff; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; padding: 20px; background: #2d2d2d; border-radius: 10px; margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .stat-card { background: #2d2d2d; padding: 15px; border-radius: 8px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #00d4aa; }
        .downloads { background: #2d2d2d; padding: 20px; border-radius: 10px; }
        .download-item { background: #1a1a1a; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 4px solid #00d4aa; }
        .progress-bar { background: #333; height: 20px; border-radius: 10px; overflow: hidden; margin: 10px 0; }
        .progress-fill { background: linear-gradient(90deg, #00d4aa, #00b894); height: 100%; transition: width 0.3s ease; }
        .status-active { color: #00d4aa; }
        .status-completed { color: #00b894; }
        .status-error { color: #e17055; }
        .log-entry { font-family: monospace; padding: 5px; margin: 2px 0; background: #111; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚂 SAINI DRM Bot</h1>
            <p>Live Progress Monitoring on Render</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ stats.active_downloads }}</div>
                <div>Active Downloads</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_files_processed }}</div>
                <div>Total Processed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ total_users }}</div>
                <div>Total Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ auth_users }}</div>
                <div>Premium Users</div>
            </div>
        </div>
        
        <div class="downloads">
            <h2>📥 Current Downloads</h2>
            {% if current_downloads %}
                {% for id, download in current_downloads.items() %}
                <div class="download-item">
                    <div><strong>{{ download.filename }}</strong></div>
                    <div>User: {{ download.user_id }} | Started: {{ download.start_time }}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {{ download.progress }}%"></div>
                    </div>
                    <div>{{ download.progress }}% - {{ download.status }}</div>
                </div>
                {% endfor %}
            {% else %}
                <p>No active downloads</p>
            {% endif %}
            
            <h2>✅ Recent Completed Downloads</h2>
            {% for download in completed_downloads[-5:] %}
            <div class="download-item">
                <div><strong>{{ download.filename }}</strong></div>
                <div class="status-completed">✅ Completed in {{ download.duration }}s</div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
    ''', 
    current_downloads=progress_data['current_downloads'],
    completed_downloads=progress_data['completed_downloads'],
    stats=progress_data['stats'],
    total_users=len(TOTAL_USERS),
    auth_users=len(AUTH_USERS)
    )

@web_app.route('/health')
def health():
    return {'status': 'healthy', 'bot_active': True, 'timestamp': time.time()}

@web_app.route('/api/progress')
def api_progress():
    return jsonify(progress_data)

@web_app.route('/status')
def status():
    return {
        'bot_name': 'SAINI DRM Bot',
        'status': 'running',
        'total_users': len(TOTAL_USERS),
        'auth_users': len(AUTH_USERS),
        'uptime': time.time(),
        'active_downloads': progress_data['stats']['active_downloads'],
        'total_processed': progress_data['stats']['total_files_processed']
    }

def update_download_progress(download_id, filename, user_id, progress=0, status="Starting", completed=False):
    """Update download progress for live tracking"""
    current_time = datetime.now().strftime("%H:%M:%S")
    
    if completed:
        if download_id in progress_data['current_downloads']:
            download_info = progress_data['current_downloads'][download_id]
            download_info['duration'] = time.time() - download_info['start_timestamp']
            progress_data['completed_downloads'].append(download_info)
            del progress_data['current_downloads'][download_id]
            progress_data['stats']['active_downloads'] -= 1
            progress_data['stats']['total_files_processed'] += 1
        print(f"🎉 RENDER LIVE: Download completed - {filename} for user {user_id}")
    else:
        if download_id not in progress_data['current_downloads']:
            progress_data['stats']['active_downloads'] += 1
            
        progress_data['current_downloads'][download_id] = {
            'filename': filename,
            'user_id': user_id,
            'progress': progress,
            'status': status,
            'start_time': current_time,
            'start_timestamp': time.time()
        }
        print(f"📥 RENDER LIVE: {filename} - {progress}% - {status} (User: {user_id})")
    
    progress_data['stats']['last_activity'] = current_time

def run_web_server():
    """Run Flask server in separate thread for Render compatibility"""
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Flask server starting on 0.0.0.0:{port}")
    try:
        web_app.run(host="0.0.0.0", port=port, debug=False, threaded=True, use_reloader=False)
    except Exception as e:
        print(f"❌ Flask server failed to start: {e}")
        raise

# Advanced Railway monitoring and optimization functions
import random

async def test_download_speed():
    """Test Railway's connection speed to major video CDNs"""
    test_urls = [
        "https://www.youtube.com/",
        "https://vimeo.com/",
        "https://www.instagram.com/"
    ]
    
    speeds = {}
    for url in test_urls:
        try:
            start = time.time()
            response = requests.get(url, timeout=10)
            end = time.time()
            speeds[url] = end - start
        except:
            speeds[url] = 999  # Mark as very slow
    
    return speeds

async def download_with_retry(cmd, max_retries=3):
    """Download with intelligent retry logic"""
    
    for attempt in range(max_retries):
        try:
            # Add random delay to avoid rate limiting
            if attempt > 0:
                delay = (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                return result
            else:
                print(f"Attempt {attempt + 1} failed: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"Attempt {attempt + 1} timed out")
        except Exception as e:
            print(f"Attempt {attempt + 1} error: {e}")
    
    raise Exception("All download attempts failed")

async def process_video_railway_optimized(video_url, message):
    """Enhanced Railway processing with real-time speed monitoring and live progress tracking"""
    import tempfile
    import time
    import re
    
    start_time = time.time()
    user_id = message.from_user.id
    download_id = f"{user_id}_{int(time.time())}"
    filename = f"video_{int(time.time())}.mp4"
    
    # Initialize live progress tracking
    update_download_progress(download_id, filename, user_id, 0, "🚂 Starting video download...")
    
    status_msg = await message.reply_text("🚂 **Railway Download Starting...**")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, filename)
            
            # Monitor download progress with enhanced parameters
            cmd = [
                'yt-dlp',
                '-f', 'best[height<=720][filesize<50M]',
                '-o', temp_file,
                '--concurrent-fragments', '16',
                '--fragment-retries', '20',              # Increased for reliability
                '--retries', '10',
                '--progress-template', 'download:[%(progress._percent_str)s] %(progress._speed_str)s ETA %(progress._eta_str)s',
                '--newline',  # Progress on new lines for parsing
                video_url
            ]
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            
            last_update = time.time()
            last_progress = ""
            current_percent = 0
            
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    if '[download]' in line and '%' in line:
                        # Parse percentage from yt-dlp output
                        percent_match = re.search(r'(\d+(?:\.\d+)?)%', line)
                        if percent_match:
                            current_percent = float(percent_match.group(1))
                        
                        # Parse speed from yt-dlp output
                        current_progress = line.strip()
                        
                        # Update live progress tracking
                        update_download_progress(download_id, filename, user_id, current_percent, f"Downloading... {current_percent:.1f}%")
                        
                        if time.time() - last_update > 5 and current_progress != last_progress:  # Update every 5 seconds
                            try:
                                await status_msg.edit_text(f"🚂 **Railway Download**\n\n{current_progress}")
                                last_update = time.time()
                                last_progress = current_progress
                            except Exception:
                                pass  # Ignore edit errors
            
            process.wait()
            
            if os.path.exists(temp_file):
                file_size = os.path.getsize(temp_file)
                download_time = time.time() - start_time
                speed_mbps = (file_size / (1024*1024)) / download_time
                
                # Update completion status
                update_download_progress(download_id, filename, user_id, 100, f"✅ Completed ({file_size / (1024*1024):.1f}MB)", completed=True)
                
                await message.reply_video(
                    video=temp_file,
                    caption=f"🚂 **Railway Downloaded**\n\n"
                           f"📊 **Size**: {file_size / (1024*1024):.1f}MB\n"
                           f"⏱️ **Time**: {download_time:.1f}s\n"
                           f"⚡ **Speed**: {speed_mbps:.2f}MB/s",
                    supports_streaming=True
                )
                
                await status_msg.delete()
            else:
                update_download_progress(download_id, filename, user_id, 0, "❌ Download failed", completed=True)
                await status_msg.edit_text("❌ **Download failed - no file generated**")
                
    except Exception as e:
        update_download_progress(download_id, filename, user_id, 0, f"❌ Error: {str(e)}", completed=True)
        await status_msg.edit_text(f"❌ **Download failed**: {str(e)}")

# Legacy function maintained for compatibility
async def optimized_download_with_progress(video_url: str, progress_callback=None):
    """Enhanced yt-dlp with progress tracking - from guidance"""
    import tempfile
    import time
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = os.path.join(temp_dir, f"video_{int(time.time())}.mp4")
        
        cmd = [
            'yt-dlp',
            '-f', 'best[height<=720][filesize<50M]',  # Telegram limit
            '--concurrent-fragments', '16',           # Railway CPU optimized
            '--fragment-retries', '10',               # Essential for reliability
            '--buffer-size', '16K',                   # Better buffering
            '--http-chunk-size', '10M',               # Railway memory optimized
            '--newline',                              # For progress parsing
            '--no-playlist',                          # Prevent accidental batch downloads
            '-o', temp_file,
            video_url
        ]
        
        # Use retry logic for better reliability
        try:
            result = await download_with_retry(cmd)
            if os.path.exists(temp_file):
                return temp_file, os.path.getsize(temp_file)
        except Exception as e:
            print(f"Download failed after retries: {e}")
        
        return None, 0

# Railway-optimized video processing function
async def process_video_railway(video_url, message):
    """Railway-compatible video processing with enhanced optimization parameters"""
    
    status_msg = await message.reply_text(
        "🚂 **Railway Processing**\n\n"
        "⚡ **Enhanced with optimization guidance**\n"
        "🔧 **16 concurrent fragments, 10M chunks**"
    )
    
    try:
        # Use the optimized download function from guidance
        temp_file, file_size = await optimized_download_with_progress(video_url)
        
        if temp_file and os.path.exists(temp_file):
            await status_msg.edit_text(
                f"🚂 **Railway Success with Optimizations**\n\n"
                f"✅ **Size**: {file_size / (1024*1024):.1f}MB\n"
                f"⚡ **16 concurrent fragments used**\n"
                f"💾 **10M chunks, 16K buffer**"
            )
            
            await message.reply_video(
                video=temp_file,
                caption=f"🚂 **Railway Optimized Download**\n"
                       f"📊 **{file_size / (1024*1024):.1f}MB**\n"
                       f"⚡ **Enhanced performance parameters**\n"
                       f"🔧 **From optimization guidance**",
                supports_streaming=True
            )
            
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ **Download failed**")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ **Error**: {str(e)}")

# .....,.....,.......,...,.......,....., .....,.....,.......,...,.......,.....,
@bot.on_message(filters.command("start"))
async def start(bot, m: Message):
    user_id = m.chat.id
    if user_id not in TOTAL_USERS:
        TOTAL_USERS.append(user_id)
    user = await bot.get_me()

    mention = user.mention
    caption = f"🌟 Welcome {m.from_user.mention} ! 🌟"
    start_message = await bot.send_photo(
        chat_id=m.chat.id,
        photo="https://envs.sh/GVI.jpg",
        caption=caption
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        f"🌟 Welcome {m.from_user.first_name}! 🌟\n\n" +
        f"Initializing Uploader bot... 🤖\n\n"
        f"Progress: [⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️] 0%\n\n"
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        f"🌟 Welcome {m.from_user.first_name}! 🌟\n\n" +
        f"Loading features... ⏳\n\n"
        f"Progress: [🟥🟥🟥⬜️⬜️⬜️⬜️⬜️⬜️⬜️] 25%\n\n"
    )
    
    await asyncio.sleep(1)
    await start_message.edit_text(
        f"🌟 Welcome {m.from_user.first_name}! 🌟\n\n" +
        f"This may take a moment, sit back and relax! 😊\n\n"
        f"Progress: [🟧🟧🟧🟧🟧⬜️⬜️⬜️⬜️⬜️] 50%\n\n"
    )

    await asyncio.sleep(1)
    await start_message.edit_text(
        f"🌟 Welcome {m.from_user.first_name}! 🌟\n\n" +
        f"Checking subscription status... 🔍\n\n"
        f"Progress: [🟨🟨🟨🟨🟨🟨🟨🟨⬜️⬜️] 75%\n\n"
        f"Almost ready...\n"
    )

    await asyncio.sleep(1)
    if m.chat.id in AUTH_USERS:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✨ Commands", callback_data="cmd_command")],
            [InlineKeyboardButton("💎 Features", callback_data="feat_command"), InlineKeyboardButton("⚙️ Settings", callback_data="setttings")],
            [InlineKeyboardButton("💳 Plans", callback_data="upgrade_command")],
            [InlineKeyboardButton(text="📞 Contact", url=f"tg://openmessage?user_id={OWNER}"), InlineKeyboardButton(text="🛠️ Repo", url=REPO_URL)],
        ])
        
        await start_message.edit_text(
            f"🌟 Welcome {m.from_user.first_name}! 🌟\n\n" +
            f"Great! You are a premium member!\n"
            f"Use button : **✨ Commands** to get started 🌟\n\n"
            f"If you face any problem contact -  [{CREDIT}⁬](tg://openmessage?user_id={OWNER})\n", disable_web_page_preview=True, reply_markup=keyboard
        )
    else:
        await asyncio.sleep(2)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✨ Commands", callback_data="cmd_command")],
            [InlineKeyboardButton("💎 Features", callback_data="feat_command"), InlineKeyboardButton("⚙️ Settings", callback_data="setttings")],
            [InlineKeyboardButton("💳 Plans", callback_data="upgrade_command")],
            [InlineKeyboardButton(text="📞 Contact", url=f"tg://openmessage?user_id={OWNER}"), InlineKeyboardButton(text="🛠️ Repo", url=REPO_URL)],
        ])
        await start_message.edit_text(
           f" 🎉 Welcome {m.from_user.first_name} to DRM Bot! 🎉\n\n"
           f"**You are currently using the free version.** 🆓\n\n<blockquote expandable>I'm here to make your life easier by downloading videos from your **.txt** file 📄 and uploading them directly to Telegram!</blockquote>\n\n**Want to get started? Press /id**\n\n💬 Contact : [{CREDIT}⁬](tg://openmessage?user_id={OWNER}) to Get The Subscription 🎫 and unlock the full potential of your new bot! 🔓\n", disable_web_page_preview=True, reply_markup=keyboard
    )

# .....,.....,.......,...,.......,....., .....,.....,.......,...,.......,.....,
@bot.on_callback_query(filters.regex("back_to_main_menu"))
async def back_to_main_menu(client, callback_query):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name
    caption = f"✨ **Welcome [{first_name}](tg://user?id={user_id}) in My uploader bot**"
    keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✨ Commands", callback_data="cmd_command")],
            [InlineKeyboardButton("💎 Features", callback_data="feat_command"), InlineKeyboardButton("⚙️ Settings", callback_data="setttings")],
            [InlineKeyboardButton("💳 Plans", callback_data="upgrade_command")],
            [InlineKeyboardButton(text="📞 Contact", url=f"tg://openmessage?user_id={OWNER}"), InlineKeyboardButton(text="🛠️ Repo", url=REPO_URL)],
        ])
    
    await callback_query.message.edit_media(
      InputMediaPhoto(
        media="https://envs.sh/GVI.jpg",
        caption=caption
      ),
      reply_markup=keyboard
    )
    await callback_query.answer()

# .....,.....,.......,...,.......,....., .....,.....,.......,...,.......,.....,
@bot.on_callback_query(filters.regex("cmd_command"))
async def cmd_commands(client, callback_query):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name
    caption = f"✨ **Welcome [{first_name}](tg://user?id={user_id})\nChoose Button to select Commands**"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚻 User", callback_data="user_command"), InlineKeyboardButton("🚹 Owner", callback_data="owner_command")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="back_to_main_menu")]
    ])
    await callback_query.message.edit_media(
    InputMediaPhoto(
      media="https://tinypic.host/images/2025/07/14/file_00000000fc2461fbbdd6bc500cecbff8_conversation_id6874702c-9760-800e-b0bf-8e0bcf8a3833message_id964012ce-7ef5-4ad4-88e0-1c41ed240c03-1-1.jpg",
      caption=caption
    ),
    reply_markup=keyboard
    )

# .....,.....,.......,...,.......,....., .....,.....,.......,...,.......,.....,
@bot.on_callback_query(filters.regex("user_command"))
async def user_help_button(client, callback_query):
  user_id = callback_query.from_user.id
  first_name = callback_query.from_user.first_name
  keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back to Commands", callback_data="cmd_command")]])
  caption = (
        f"💥 𝐁𝐎𝐓𝐒 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒\n"
        f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n" 
        f"📌 𝗠𝗮𝗶𝗻 𝗙𝗲𝗮𝘁𝘂𝗿𝗲𝘀:\n\n"  
        f"➥ /start – Bot Status Check\n"
        f"➥ /y2t – YouTube → .txt Converter\n"  
        f"➥ /ytm – YouTube → .mp3 downloader\n"  
        f"➥ /t2t – Text → .txt Generator\n"
        f"➥ /t2h – .txt → .html Converter\n" 
        f"➥ /stop – Cancel Running Task\n"
        f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰ \n" 
        f"⚙️ 𝗧𝗼𝗼𝗹𝘀 & 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀: \n\n" 
        f"➥ /cookies – Update YT Cookies\n" 
        f"➥ /id – Get Chat/User ID\n"  
        f"➥ /info – User Details\n"  
        f"➥ /logs – View Bot Activity\n"
        f"▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"
        f"💡 𝗡𝗼𝘁𝗲:\n\n"  
        f"• Send any link for auto-extraction\n"
        f"• Send direct .txt file for auto-extraction\n"
        f"• Supports batch processing\n\n"  
        f"╭────────⊰◆⊱────────╮\n"   
        f" ➠ 𝐌𝐚𝐝𝐞 𝐁𝐲 : {CREDIT} 💻\n"
        f"╰────────⊰◆⊱────────╯\n"
  )
    
  await callback_query.message.edit_media(
    InputMediaPhoto(
      media="https://tinypic.host/images/2025/07/14/file_00000000fc2461fbbdd6bc500cecbff8_conversation_id6874702c-9760-800e-b0bf-8e0bcf8a3833message_id964012ce-7ef5-4ad4-88e0-1c41ed240c03-1-1.jpg",
      caption=caption
    ),
    reply_markup=keyboard
    )

# .....,.....,.......,...,.......,....., .....,.....,.......,...,.......,.....,
@bot.on_message(filters.command(["id"]))
async def id_command(client, message: Message):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text="Send to Owner", url=f"tg://openmessage?user_id={OWNER}")]])
    chat_id = message.chat.id
    text = f"<blockquote expandable><b>The ID of this chat id is:</b></blockquote>\n`{chat_id}`"
    
    if str(chat_id).startswith("-100"):
        await message.reply_text(text)
    else:
        await message.reply_text(text, reply_markup=keyboard)

# .....,.....,.......,...,.......,....., .....,.....,.......,...,.......,.....,
@bot.on_message(filters.private & filters.command(["info"]))
async def info(bot: Client, update: Message):
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(text="📞 Contact", url=f"tg://openmessage?user_id={OWNER}")]])
    text = (
        f"╭────────────────╮\n"
        f"│✨ **Your Telegram Info**✨ \n"
        f"├────────────────\n"
        f"├🔹**Name :** `{update.from_user.first_name} {update.from_user.last_name if update.from_user.last_name else 'None'}`\n"
        f"├🔹**User ID :** @{update.from_user.username}\n"
        f"├🔹**TG ID :** `{update.from_user.id}`\n"
        f"├🔹**Profile :** {update.from_user.mention}\n"
        f"╰────────────────╯"
    )
    
    await update.reply_text(        
        text=text,
        disable_web_page_preview=True,
        reply_markup=keyboard
    )

# .....,.....,.......,...,.......,....., .....,.....,.......,...,.......,.....,
@bot.on_message(filters.command(["logs"]))
async def send_logs(client: Client, m: Message):
    try:
        with open("logs.txt", "rb") as file:
            sent = await m.reply_text("**📤 Sending you ....**")
            await m.reply_document(document=file)
            await sent.delete()
    except Exception as e:
        await m.reply_text(f"**Error sending logs:**\n<blockquote>{e}</blockquote>")

# .....,.....,.......,...,.......,....., .....,.....,.......,...,.......,.....,
@bot.on_message(filters.command(["reset"]))
async def restart_handler(_, m):
    if m.chat.id != OWNER:
        return
    else:
        await m.reply_text("𝐁𝐨𝐭 𝐢𝐬 𝐑𝐞𝐬𝐞𝐭𝐢𝐧𝐠...", True)
        os.execl(sys.executable, sys.executable, *sys.argv)

# .....,.....,.......,...,.......,....., .....,.....,.......,...,.......,.....,
@bot.on_message(filters.command("stop") & filters.private)
async def cancel_handler(client: Client, m: Message):
    if m.chat.id not in AUTH_USERS:
        print(f"User ID not in AUTH_USERS", m.chat.id)
        await bot.send_message(
            m.chat.id, 
            f"<blockquote>__**Oopss! You are not a Premium member**__\n"
            f"__**PLEASE /upgrade YOUR PLAN**__\n"
            f"__**Send me your user id for authorization**__\n"
            f"__**Your User id** __- `{m.chat.id}`</blockquote>\n\n"
        )
    else:
        if globals.processing_request:
            globals.cancel_requested = True
            await m.delete()
            cancel_message = await m.reply_text("**🚦 Process cancel request received. Stopping after current process...**")
            await asyncio.sleep(30)
            await cancel_message.delete()
        else:
            await m.reply_text("**⚡ No active process to cancel.**")

# Include ALL your other command handlers...
@bot.on_message(filters.command("addauth") & filters.private)
async def call_add_auth_user(client: Client, message: Message):
    await add_auth_user(client, message)

@bot.on_message(filters.command("users") & filters.private)
async def call_list_auth_users(client: Client, message: Message):
    await list_auth_users(client, message)
    
@bot.on_message(filters.command("rmauth") & filters.private)
async def call_remove_auth_user(client: Client, message: Message):
    await remove_auth_user(client, message)
    
@bot.on_message(filters.command("broadcast") & filters.private)
async def call_broadcast_handler(client: Client, message: Message):
    await broadcast_handler(client, message)
    
@bot.on_message(filters.command("broadusers") & filters.private)
async def call_broadusers_handler(client: Client, message: Message):
    await broadusers_handler(client, message)
    
@bot.on_message(filters.command("cookies") & filters.private)
async def call_cookies_handler(client: Client, m: Message):
    await cookies_handler(client, m)

@bot.on_message(filters.command(["t2t"]))
async def call_text_to_txt(bot: Client, m: Message):
    await text_to_txt(bot, m)

@bot.on_message(filters.command(["y2t"]))
async def call_y2t_handler(bot: Client, m: Message):
    await y2t_handler(bot, m)

@bot.on_message(filters.command(["ytm"]))
async def call_ytm_handler(bot: Client, m: Message):
    await ytm_handler(bot, m)

@bot.on_message(filters.command("getcookies") & filters.private)
async def call_getcookies_handler(client: Client, m: Message):
    await getcookies_handler(client, m)

@bot.on_message(filters.command(["t2h"]))
async def call_html_handler(bot: Client, message: Message):
    await html_handler(bot, message)
    
@bot.on_message(filters.private & (filters.document | filters.text))
async def call_drm_handler(bot: Client, m: Message):
    await drm_handler(bot, m)

def notify_owner():
    """Send restart notification with cooldown to prevent spam"""
    import os
    import time
    
    cooldown_file = "/tmp/last_notification.txt"
    current_time = time.time()
    cooldown_minutes = 15  # Don't notify more than once every 15 minutes
    
    try:
        # Check if cooldown file exists and read last notification time
        if os.path.exists(cooldown_file):
            with open(cooldown_file, 'r') as f:
                last_notification = float(f.read().strip())
                
            # Check if cooldown period has passed
            if current_time - last_notification < (cooldown_minutes * 60):
                print(f"🔕 Skipping notification - cooldown active ({cooldown_minutes} minutes)")
                return
    except (FileNotFoundError, ValueError, Exception):
        # If file doesn't exist or is corrupt, proceed with notification
        pass
    
    # Send notification
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": OWNER,
        "text": "🚂 Render Bot Started Successfully ✅\n⏰ Live progress: Your-Render-URL"
    }
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            # Save current time to cooldown file
            with open(cooldown_file, 'w') as f:
                f.write(str(current_time))
            print("✅ Owner notification sent successfully")
        else:
            print(f"⚠️ Notification failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Failed to send notification: {e}")

def reset_and_set_commands():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands"
    # Reset
    requests.post(url, json={"commands": []})
    # Set new
    commands = [
        {"command": "start", "description": "✅ Check Alive the Bot"},
        {"command": "stop", "description": "🚫 Stop the ongoing process"},
        {"command": "features", "description": "💎 Access Bot Features Panel"},
        {"command": "settings", "description": "⚙️ Access Bot Settings Panel"},
        {"command": "id", "description": "🆔 Get Your ID"},
        {"command": "info", "description": "ℹ️ Check Your Information"},
        {"command": "cookies", "description": "📁 Upload YT Cookies"},
        {"command": "y2t", "description": "🔪 YouTube → .txt Converter"},
        {"command": "ytm", "description": "🎶 YouTube → .mp3 downloader"},
        {"command": "t2t", "description": "📟 Text → .txt Generator"},
        {"command": "t2h", "description": "🌐 .txt → .html Converter"},
        {"command": "logs", "description": "👁️ View Bot Activity"},
        {"command": "broadcast", "description": "📢 Broadcast to All Users"},
        {"command": "broadusers", "description": "👨‍❤️‍👨 All Broadcasting Users"},
        {"command": "addauth", "description": "▶️ Add Authorisation"},
        {"command": "rmauth", "description": "⏸️ Remove Authorisation"},
        {"command": "users", "description": "👨‍👨‍👧‍👦 All Premium Users"},
        {"command": "reset", "description": "✅ Reset the Bot"}
    ]
    requests.post(url, json={"commands": commands})

def startup_network_test_sync():
    """Test network performance during startup (synchronous version)"""
    print("🌐 Testing Railway network performance...")
    try:
        test_urls = [
            "https://www.youtube.com/",
            "https://vimeo.com/",
            "https://www.instagram.com/"
        ]
        
        speeds = {}
        for url in test_urls:
            try:
                start = time.time()
                response = requests.get(url, timeout=10)
                end = time.time()
                speeds[url] = end - start
            except:
                speeds[url] = 999  # Mark as very slow
        
        print("🚂 Network Test Results:")
        for url, response_time in speeds.items():
            status = "✅ Fast" if response_time < 2 else "⚠️ Slow" if response_time < 5 else "❌ Very Slow"
            print(f"  {url}: {response_time:.2f}s - {status}")
    except Exception as e:
        print(f"⚠️ Network test failed: {e}")

if __name__ == "__main__":
    print("🚂 SAINI DRM Bot Starting with Render Port Support...")
    
    # Start web server FIRST for immediate port detection
    port = int(os.environ.get('PORT', 10000))
    print(f"🌐 Starting Flask server on port {port} (Render requirement)...")
    web_thread = Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Give Flask server time to bind to port
    import time
    time.sleep(2)
    
    # Test if server is responding
    try:
        import requests
        response = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Flask server is responding - Render should detect port")
        else:
            print(f"⚠️ Flask server responding with status {response.status_code}")
    except Exception as e:
        print(f"⚠️ Flask server health check failed: {e}")
    
    # Run other startup tasks (non-blocking for port detection)
    try:
        startup_network_test_sync()
        reset_and_set_commands()
        # Temporarily disabled to prevent notification spam during FloodWait
        # notify_owner()
        print("🔕 Notification disabled to prevent FloodWait spam")
    except Exception as e:
        print(f"⚠️ Startup task failed: {e}")
    
    print("🤖 Starting Telegram bot...")
    
    try:
        import signal
        import asyncio
        
        def timeout_handler(signum, frame):
            print("⏰ Bot startup timeout - likely FloodWait blocking")
            raise TimeoutError("Bot connection timeout")
        
        # Set timeout for bot connection attempt
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(10)  # 10 second timeout
        
        print("🔗 Attempting bot connection...")
        bot.run()
        
    except TimeoutError:
        print("⏳ Bot connection timed out - FloodWait blocking detected")
        print("🌐 Flask server continues running for Render deployment")
        print("🔄 Bot will retry automatically when Render restarts")
        
    except Exception as e:
        print(f"❌ Bot startup failed: {e}")
        
        # Check if it's FloodWait
        if "FloodWait" in str(type(e)) or "FLOOD_WAIT" in str(e):
            wait_time = getattr(e, 'value', getattr(e, 'x', 1968))
            print(f"⏳ FloodWait detected: {wait_time} seconds ({wait_time//60:.1f} minutes)")
            print("🌐 Flask server will continue running for Render")
            print("🔄 Render will automatically restart the bot when ready")
        else:
            print(f"❌ Other error: {e}")
            print("🌐 Flask server continues for Render port detection")
    
    finally:
        signal.alarm(0)  # Clear the alarm
        
    # Keep Flask running for Render - this prevents "No open ports" error
    print("🌐 Maintaining Flask server for Render deployment...")
    try:
        while True:
            print(f"🌐 Flask server active - Bot will retry on next restart")
            time.sleep(300)  # Status update every 5 minutes
    except KeyboardInterrupt:
        print("👋 Shutting down gracefully...")
