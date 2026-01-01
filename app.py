import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Replace with your token from BotFather
TOKEN = '8456625198:AAGlNGWBFsmEgc45cZ6Pp70hju9FqpbmBs4'

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! Send me a TikTok or YouTube link, and I will download it for you.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    status = await update.message.reply_text("⏳ Processing link...")

    # yt-dlp configuration
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s', # Saves to a folder named 'downloads'
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        await status.edit_text("✅ Download complete! Uploading to Telegram...")
        
        # Send the video file to the user
        with open(filename, 'rb') as video:
            await update.message.reply_video(video=video, caption=info.get('title'))
        
        # Delete file after sending to save space on the server
        os.remove(filename)
    except Exception as e:
        await status.edit_text(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("Bot is starting...")
    app.run_polling()