import os
import tempfile
import subprocess
import time
import asyncio
from pyrogram import Client
from pyrogram.types import Message

async def process_video_railway_fixed(video_url, message):
    """Railway-compatible video processor with proper error handling"""
    
    status_msg = await message.reply_text(
        "🚂 **Railway Processing**\n\n"
        "⏳ **Starting download...**"
    )
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, f"video_{int(time.time())}.mp4")
            
            # Railway-optimized download
            cmd = [
                'yt-dlp',
                '-f', 'best[height<=720]',
                '-o', temp_file,
                '--concurrent-fragments', '8',
                '--fragment-retries', '10',
                '--retries', '5',
                '--merge-output-format', 'mp4',
                video_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # CRITICAL: Check if file actually exists before sending
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                file_size = os.path.getsize(temp_file)
                
                await status_msg.edit_text(
                    f"🚂 **Railway Success**\n\n"
                    f"✅ **Downloaded**: {file_size / (1024*1024):.1f}MB\n"
                    f"📤 **Uploading to Telegram...**"
                )
                
                # CORRECT: Only send video if file exists and is valid
                await message.reply_video(
                    video=temp_file,
                    caption=f"🚂 **Railway Processed**\n"
                           f"📊 **Size**: {file_size / (1024*1024):.1f}MB\n"
                           f"✅ **Higher disk quotas used**",
                    supports_streaming=True
                )
                
                await status_msg.delete()
                print(f"✅ Video processed successfully: {file_size / (1024*1024):.1f}MB")
                
            else:
                # CRITICAL: Send error as TEXT, not as video
                error_details = result.stderr if result.stderr else "Unknown download error"
                await status_msg.edit_text(
                    f"❌ **Download Failed**\n\n"
                    f"**URL**: `{video_url}`\n"
                    f"**Error**: {error_details[:200]}...\n\n"
                    f"🚂 **Running on Railway with higher quotas**\n"
                    f"💡 **Try again or check URL validity**"
                )
                print(f"❌ Download failed: {error_details}")
                
    except subprocess.TimeoutExpired:
        await status_msg.edit_text(
            f"❌ **Download Timeout**\n\n"
            f"**URL**: `{video_url}`\n"
            f"**Reason**: Download took longer than 5 minutes\n\n"
            f"💡 **Try a shorter video or different URL**"
        )
    except Exception as e:
        await status_msg.edit_text(
            f"❌ **Processing Error**\n\n"
            f"**URL**: `{video_url}`\n"
            f"**Error**: {str(e)[:200]}...\n\n"
            f"🚂 **Railway Environment Error**"
        )
        print(f"❌ Processing error: {e}")

async def handle_video_urls_optimized(client, message):
    """Updated handler with proper error handling"""
    
    from vars import AUTH_USERS
    
    if message.chat.id not in AUTH_USERS:
        await message.reply_text("❌ **Unauthorized Access**")
        return
    
    url = message.text.strip()
    
    # Validate URL before processing
    if not url.startswith(('http://', 'https://')):
        await message.reply_text("❌ **Invalid URL Format**\nPlease send a valid HTTP/HTTPS URL")
        return
    
    # Check if URL contains supported domains/formats
    supported_patterns = [
        'youtube.com', 'youtu.be', 'vimeo.com', 'instagram.com',
        'facebook.com', 'twitter.com', '.m3u8', '.mp4', '.mkv'
    ]
    
    if not any(pattern in url.lower() for pattern in supported_patterns):
        await message.reply_text(
            "❌ **Unsupported URL**\n\n"
            "✅ **Supported**: YouTube, Vimeo, Instagram, Facebook, Twitter, HLS streams, Direct MP4\n"
            "💡 **Try**: Sending a supported video URL"
        )
        return
    
    # Process with fixed handler
    await process_video_railway_fixed(url, message)