import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web
import yt_dlp

# 1. Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# 2. BOT TOKENingizni shu yerga yozing
API_TOKEN = '8763063838:AAG4xA6wuEP9uL1jAs7LDoRXV2byIarol-s'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- WEB SERVER (Render uchun shart) ---
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

# --- BOT FUNKSIYALARI ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Salom! Video yoki audio yuklash uchun link yuboring.")

@dp.message(F.text.contains("http"))
async def download_media(message: types.Message):
    url = message.text
    status_msg = await message.answer("Media tahlil qilinmoqda...")

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            input_file = types.FSInputFile(file_path)
            
            # Audio yoki Video ekanini aniqlash
            if info.get('ext') == 'mp3' or 'audio' in info.get('format', ''):
                await message.answer_audio(input_file, caption=f"🎵 {info.get('title')}")
            else:
                await message.answer_video(input_file, caption=f"🎬 {info.get('title')}")
            
            os.remove(file_path)
            await status_msg.delete()
    except Exception as e:
        await status_msg.edit_text(f"Xatolik: {str(e)}")

async def main():
    asyncio.create_task(start_web_server())
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())