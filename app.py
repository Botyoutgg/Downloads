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
    await update.message.reply_text("👋 Send me a link to start downloading!")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    context.user_data['current_url'] = url  # Save URL for later
    
    # Selection Menu
    keyboard = [
        [InlineKeyboardButton("🎵 MP3 Audio", callback_data='mp3')],
        [InlineKeyboardButton("📺 480p", callback_data='480'), InlineKeyboardButton("📺 1080p", callback_data='1080')],
        [InlineKeyboardButton("🌟 4K / Best", callback_data='best')]
    ]
    await update.message.reply_text("Choose format & quality:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    choice = query.data
    url = context.user_data.get('current_url')
    await query.edit_message_text(f"⏳ Downloading {choice} quality... please wait.")

    # Quality Mapping
    format_selection = 'bestaudio/best' if choice == 'mp3' else \
                       f'bestvideo[height<={choice}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]' if choice != 'best' else \
                       'bestvideo+bestaudio/best'

    ydl_opts = {
        'format': format_selection,
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}] if choice == 'mp3' else [],
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if choice == 'mp3': file_path = file_path.rsplit('.', 1)[0] + '.mp3'

        with open(file_path, 'rb') as f:
            if choice == 'mp3':
                await query.message.reply_audio(audio=f, caption=info['title'])
            else:
                await query.message.reply_video(video=f, caption=info['title'])
        os.remove(file_path)
    except Exception as e:
        await query.message.reply_text(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    threading.Thread(target=run_health_server, daemon=True).start()
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_url))
    app.add_handler(CallbackQueryHandler(button_click)) #
    app.run_polling()
