import asyncio, os, logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
import yt_dlp

# --- KONFIGURATSIYA ---
API_TOKEN = '8763063838:AAG4xA6wuEP9uL1jAs7LDoRXV2byIarol-s'
CHANNELS = ['@hozirchhgfalikka', '@yaxshilikkada'] 
INSTAGRAM_URL = "https://www.instagram.com/samarkand070102"
DOWNLOAD_DIR = 'downloads'

if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Linklarni vaqtincha saqlash uchun lug'at (tugma xatosini oldini olish uchun)
url_storage = {}

async def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]: return False
        except: return False
    return True

@dp.message(F.text.startswith("http"))
async def handle_link(message: types.Message):
    if not await check_subscription(message.from_user.id):
        return await message.answer("❌ Avval obuna bo'ling!")

    url = message.text
    # Tugma xatosini oldini olish uchun linkni ID bilan bog'laymiz
    url_id = str(hash(url)) 
    url_storage[url_id] = url 

    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🎬 Video (720p)", callback_data=f"mp4|{url_id}"),
        types.InlineKeyboardButton(text="🎵 Musiqa (MP3)", callback_data=f"mp3|{url_id}")
    )
    await message.answer("Formatni tanlang (Max 100MB):", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("mp4|") | F.data.startswith("mp3|"))
async def download_process(call: types.CallbackQuery):
    format_type, url_id = call.data.split("|")
    url = url_storage.get(url_id)
    
    if not url:
        return await call.answer("❌ Link muddati o'tgan, qayta yuboring.", show_alert=True)

    status_msg = await call.message.edit_text("⏳ Yuklanmoqda...")
    
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'max_filesize': 100 * 1024 * 1024,
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best' if format_type == "mp4" else 'bestaudio/best'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=True)
            path = ydl.prepare_filename(info)
            if format_type == "mp3":
                # MP3 konvertatsiya qilish (FFmpeg kerak!)
                new_path = os.path.splitext(path)[0] + ".mp3"
                os.rename(path, new_path)
                path = new_path

            await call.message.answer_document(types.FSInputFile(path))
            os.remove(path)
            await status_msg.delete()
    except Exception as e:
        logging.error(e)
        await status_msg.edit_text("❌ Xatolik! Serverda FFmpeg yo'q yoki fayl juda katta.")

# Render uchun web server qismi (O'zgarishsiz qoladi)
async def handle(request): return web.Response(text="Online")
async def main():
    asyncio.create_task(web._run_app(web.Application().add_get("/", handle), port=10000))
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__": asyncio.run(main())