import os
import requests
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from .utils import cleanup_temp_files, final_cleanup

async def text_to_txt(bot: Client, message: Message):
    # Clean up all temporary files before starting new conversion
    cleaned_count = cleanup_temp_files()
    if cleaned_count > 0:
        print(f"🧹 Cleaned {cleaned_count} temporary files before starting text to txt conversion")
    
    user_id = str(message.from_user.id)
    # Inform the user to send the text data and its desired file name
    editable = await message.reply_text(f"<blockquote><b>Welcome to the Text to .txt Converter!\nSend the **text** for convert into a `.txt` file.</b></blockquote>")
    input_message = await bot.listen(message.from_user.id)
    if not input_message.text:
        await message.reply_text("**Send valid text data**")
        return

    text_data = input_message.text.strip()
    await input_message.delete()  # Corrected here
    
    await editable.edit("**🔄 Send file name or send /d for filename**")
    inputn = await bot.listen(message.from_user.id)
    raw_textn = inputn.text
    await inputn.delete()  # Corrected here
    await editable.delete()

    if raw_textn == '/d':
        custom_file_name = 'txt_file'
    else:
        # Remove any leading slashes and clean the filename 
        custom_file_name = raw_textn.lstrip('/').replace('/', '_')

    # Create downloads directory in current working directory  
    downloads_dir = os.path.join(".", "downloads")
    os.makedirs(downloads_dir, exist_ok=True)
    txt_file = os.path.join(downloads_dir, f'{custom_file_name}.txt')
    with open(txt_file, 'w') as f:
        f.write(text_data)
        
    await message.reply_document(document=txt_file, caption=f"`{custom_file_name}.txt`\n\n<blockquote>You can now download your content! 📥</blockquote>")
    os.remove(txt_file)


    # Final cleanup after completing conversion and sending results
    final_cleaned = final_cleanup()
    if final_cleaned > 0:
        print(f"🧹 Final cleanup: Removed {final_cleaned} temporary files after text to txt conversion")
