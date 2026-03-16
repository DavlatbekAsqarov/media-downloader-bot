import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
import yt_dlp

# --- KONFIGURATSIYA ---
API_TOKEN = '8763063838:AAG4xA6wuEP9uL1jAs7LDoRXV2byIarol-s'
DOWNLOAD_DIR = 'downloads'

# Papka mavjudligini tekshirish
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Foydalanuvchi linklarini saqlash
user_links = {}

# --- WEB SERVER (Render uchun) ---
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
    logging.info(f"Web server started on port {port}")

# --- BOT HANDLERLARI ---
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(f"👋 Salom {message.from_user.first_name}!\nLink yuboring, Video (MP4) yoki Musiqa (MP3) yuklab beraman.")

@dp.message(F.text.startswith("http"))
async def handle_link(message: types.Message):
    url = message.text
    user_links[message.from_user.id] = url
    
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🎬 Video (MP4)", callback_data="get_mp4"),
        types.InlineKeyboardButton(text="🎵 Musiqa (MP3)", callback_data="get_mp3")
    )
    await message.answer("Qaysi formatda yuklaymiz? 👇", reply_markup=builder.as_markup())

@dp.callback_query(F.data.in_(["get_mp4", "get_mp3"]))
async def download_process(call: types.CallbackQuery):
    url = user_links.get(call.from_user.id)
    if not url:
        return await call.answer("❌ Link topilmadi, qaytadan yuboring.", show_alert=True)

    format_type = "mp3" if call.data == "get_mp3" else "mp4"
    status_msg = await call.message.edit_text("⏳ Yuklanmoqda, kuting...")

    # yt-dlp sozlamalari
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
    }

    if format_type == "mp3":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts['format'] = 'best[ext=mp4]/best'

    try:
        # Bloklanib qolmaslik uchun alohida thread'da ishga tushiramiz
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            path = ydl.prepare_filename(info)
            
            # MP3 bo'lsa nomini to'g'rilash
            if format_type == "mp3":
                path = os.path.splitext(path)[0] + ".mp3"
            
            if os.path.exists(path):
                file_to_send = types.FSInputFile(path)
                if format_type == "mp3":
                    await call.message.answer_audio(file_to_send, caption="@media_downloader_bot orqali yuklandi")
                else:
                    await call.message.answer_video(file_to_send, caption="@media_downloader_bot orqali yuklandi")
                
                # Faylni o'chirish
                os.remove(path)
            
            await status_msg.delete()
            user_links.pop(call.from_user.id, None)

    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await call.message.answer("❌ Xatolik! Link noto'g'ri yoki fayl juda katta.")
    finally:
        # Har qanday holatda foydalanuvchi ma'lumotini tozalash
        user_links.pop(call.from_user.id, None)

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    # Eski webhooklarni va pollinglarni tozalash (ConflictError oldini oladi)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Web serverni fonda ishga tushirish
    asyncio.create_task(start_web_server())
    
    # Botni ishga tushirish
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")