import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web
import yt_dlp

# 1. Loglarni sozlash (Xatolarni ko'rish uchun)
logging.basicConfig(level=logging.INFO)

# 2. BOT TOKENingizni shu yerga yozing
API_TOKEN = '8763063838:AAG4xA6wuEP9uL1jAs7LDoRXV2byIarol-s'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- WEB SERVER (Render o'chirib yubormasligi uchun) ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server {port}-portda ishga tushdi.")

# --- BOT BUYRUQLARI ---

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Salom! Video yoki audio yuklash uchun link yuboring (YouTube, Instagram, TikTok va hk).")

@dp.message(F.text.contains("http"))
async def download_media(message: types.Message):
    url = message.text
    status_msg = await message.answer("Media tahlil qilinmoqda...")

    # Fayllarni saqlash uchun papka
    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    # yt-dlp sozlamalari
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await status_msg.edit_text("Yuklanmoqda...")
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            # Faylni yuborish (Video yoki Audio ekanligini tekshirish)
            input_file = types.FSInputFile(file_path)
            
            if info.get('ext') == 'mp3' or 'audio' in info.get('format', ''):
                await message.answer_audio(input_file, caption=f"🎵 {info.get('title')}")
            else:
                await message.answer_video(input_file, caption=f"🎬 {info.get('title')}")
            
            # Xotirani tozalash (Faylni o'chirish)
            os.remove(file_path)
            await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"Xatolik yuz berdi: {str(e)}")

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    # Web serverni alohida vazifa (task) sifatida qo'shish
    asyncio.create_task(start_web_server())
    
    # Botni ishga tushirish
    logging.info("Bot polling rejimi boshlandi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi!")