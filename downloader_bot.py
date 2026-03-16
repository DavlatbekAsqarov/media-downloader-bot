import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web
import yt_dlp

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# --- BOT SOZLAMALARI ---
API_TOKEN = '8763063838:AAG4xA6wuEP9uL1jAs7LDoRXV2byIarol-s'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- WEB SERVER (RENDER UCHUN) ---
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
    print(f"Web server {port}-portda ishga tushdi.")

# --- BOT FUNKSIYALARI ---

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Salom! Video yoki audio yuklash uchun link yuboring.")

@dp.message(F.text.contains("http"))
async def download_media(message: types.Message):
    url = message.text
    msg = await message.answer("Media qayta ishlanmoqda, kuting...")

    # yt-dlp sozlamalari (Ham video, ham audio uchun)
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            # Faylni yuborish
            input_file = types.FSInputFile(file_path)
            if info.get('ext') == 'mp3' or 'audio' in info.get('format', ''):
                await message.answer_audio(input_file, caption=info.get('title'))
            else:
                await message.answer_video(input_file, caption=info.get('title'))
            
            # Faylni serverdan o'chirish (joy band qilmasligi uchun)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"Xatolik yuz berdi: {str(e)}")

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    # 1. Web serverni orqa fonda yurgizish
    asyncio.create_task(start_web_server())
    
    # 2. Botni yurgizish
    print("Bot Renderda ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    asyncio.run(main())