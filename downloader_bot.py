import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from aiohttp import web
import yt_dlp

# --- KONFIGURATSIYA ---
API_TOKEN = '8763063838:AAG4xA6wuEP9uL1jAs7LDoRXV2byIarol-s'
# Kanallaringiz ID sini yoki usernamesini yozing (masalan: '@kanal_yoki_id')
CHANNELS = ['@hozirchalikka', '@yaxshilikkada'] 
INSTAGRAM_URL = "https://www.instagram.com/samarkand070102?igsh=NzVuMGhmcXF2ZnFh"

DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- OBUNANI TEKSHIRISH FUNKSIYASI ---
async def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            # Agar bot kanal admini bo'lmasa yoki kanal topilmasa
            logging.error(f"Xatolik: {channel} tekshirib bo'lmadi")
            return False
    return True

def get_sub_keyboard():
    builder = InlineKeyboardBuilder()
    for i, channel in enumerate(CHANNELS, 1):
        builder.row(types.InlineKeyboardButton(text=f"📢 {i}-kanalga obuna bo'lish", url=f"https://t.me/{channel.replace('@', '')}"))
    
    builder.row(types.InlineKeyboardButton(text="📸 Instagramga obuna bo'lish", url=INSTAGRAM_URL))
    builder.row(types.InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub"))
    return builder.as_markup()

# --- WEB SERVER ---
async def handle(request): return web.Response(text="Bot is running!")
async def start_web_server():
    app = web.Application(); app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, "0.0.0.0", port).start()

# --- HANDLERLAR ---
@dp.message(Command("start"))
async def start(message: types.Message):
    if await check_subscription(message.from_user.id):
        await message.answer(f"👋 Salom {message.from_user.first_name}!\nLink yuboring, Video yoki MP3 yuklab beraman.")
    else:
        await message.answer("❌ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:", reply_markup=get_sub_keyboard())

@dp.callback_query(F.data == "check_sub")
async def check_button(call: types.CallbackQuery):
    if await check_subscription(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ Rahmat! Endi botdan foydalanishingiz mumkin. Link yuboring.")
    else:
        await call.answer("❌ Hali hamma kanallarga obuna bo'lmadingiz!", show_alert=True)

@dp.message(F.text.startswith("http"))
async def handle_link(message: types.Message):
    # Har safar link yuborganda tekshirish (ixtiyoriy)
    if not await check_subscription(message.from_user.id):
        return await message.answer("❌ Avval obuna bo'ling:", reply_markup=get_sub_keyboard())

    url = message.text
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🎬 Video (MP4)", callback_data=f"mp4|{url}"), # Url'ni callback ichiga yashirdik
        types.InlineKeyboardButton(text="🎵 Musiqa (MP3)", callback_data=f"mp3|{url}")
    )
    await message.answer("Qaysi formatda yuklaymiz? 👇", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("mp4|") | F.data.startswith("mp3|"))
async def download_process(call: types.CallbackQuery):
    if not await check_subscription(call.from_user.id):
        return await call.answer("❌ Obuna bo'lmagansiz!", show_alert=True)

    format_type, url = call.data.split("|")
    status_msg = await call.message.edit_text("⏳ Yuklanmoqda, kuting...")

    ydl_opts = {'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s', 'noplaylist': True, 'quiet': True}
    if format_type == "mp3":
        ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]})
    else:
        ydl_opts['format'] = 'best[ext=mp4]/best'

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            path = ydl.prepare_filename(info)
            if format_type == "mp3": path = os.path.splitext(path)[0] + ".mp3"
            
            if os.path.exists(path):
                file_to_send = types.FSInputFile(path)
                if format_type == "mp3": await call.message.answer_audio(file_to_send)
                else: await call.message.answer_video(file_to_send)
                os.remove(path)
            
            await status_msg.delete()
    except Exception as e:
        logging.error(e)
        await call.message.answer("❌ Xatolik yuz berdi!")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())