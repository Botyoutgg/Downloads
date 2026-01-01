import os
import threading
import yt_dlp
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- 1. HEALTH CHECK FOR KOYEB ---
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"Bot is Healthy")

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthHandler).serve_forever()

# --- 2. BOT LOGIC ---
TOKEN = os.environ.get('TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Paste a link to select quality and download!")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    context.user_data['url'] = url  # Save for button handler
    
    # Selection Menu
    keyboard = [
        [InlineKeyboardButton("🎵 MP3 Audio", callback_data='mp3')],
        [InlineKeyboardButton("📺 480p", callback_data='480'), InlineKeyboardButton("📺 720p", callback_data='720')],
        [InlineKeyboardButton("📺 1080p", callback_data='1080'), InlineKeyboardButton("🌟 4K / Best", callback_data='best')]
    ]
    await update.message.reply_text("Choose your format and quality:", 
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    choice = query.data
    url = context.user_data.get('url')
    await query.edit_message_text(f"⏳ Processing {choice}... Please wait.")

    # Format Logic
    if choice == 'mp3':
        f_str = 'bestaudio/best'
    elif choice == 'best':
        f_str = 'bestvideo+bestaudio/best'
    else:
        f_str = f'bestvideo[height<={choice}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'

    ydl_opts = {
        'format': f_str,
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'merge_output_format': 'mp4' if choice != 'mp3' else None,
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}] if choice == 'mp3' else [],
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            if choice == 'mp3': path = path.rsplit('.', 1)[0] + '.mp3'

        with open(path, 'rb') as f:
            if choice == 'mp3':
                await query.message.reply_audio(audio=f, caption=info['title'])
            else:
                await query.message.reply_video(video=f, caption=info['title'])
        os.remove(path)
    except Exception as e:
        await query.message.reply_text(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    threading.Thread(target=run_health_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_url))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
