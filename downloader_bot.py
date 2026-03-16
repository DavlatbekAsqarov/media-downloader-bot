import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
import yt_dlp

# --- SOZLAMALAR (O'zingiznikini qo'ying) ---
API_TOKEN = '8763063838:AAG4xA6wuEP9uL1jAs7LDoRXV2byIarol-s'
CHANNELS = ["@yaxshilikkada", "@hozirchalikka"] # 2 ta kanal manzili

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

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

# --- OBUNANI TEKSHIRISH ---
async def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            continue
    return True

# --- BOT HANDLERLARI ---
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(f"👋 Salom {message.from_user.first_name}!\n\nVideo yoki MP3 yuklash uchun link yuboring.")

@dp.message(F.text.contains("http"))
async def handle_link(message: types.Message):
    # 1. Obunani tekshirish
    if not await check_subscription(message.from_user.id):
        builder = InlineKeyboardBuilder()
        for ch in CHANNELS:
            builder.row(types.InlineKeyboardButton(text="Obuna bo'lish", url=f"https://t.me/{ch[1:]}"))
        builder.row(types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub"))
        return await message.answer("❌ Botdan foydalanish uchun kanallarga a'zo bo'ling:", reply_markup=builder.as_markup())

    # 2. Tanlash tugmalarini chiqarish
    url = message.text
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🎬 Video (MP4)", callback_data=f"mp4|{url}"),
        types.InlineKeyboardButton(text="🎵 Musiqa (MP3)", callback_data=f"mp3|{url}")
    )
    await message.answer("Qaysi formatda yuklamoqchisiz? 👇", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "check_sub")
async def check_callback(call: types.CallbackQuery):
    if await check_subscription(call.from_user.id):
        await call.message.edit_text("Rahmat! Endi link yuborishingiz mumkin. ✅")
    else:
        await call.answer("Hali hamma kanallarga a'zo bo'lmadingiz! ❌", show_alert=True)

@dp.callback_query(F.data.startswith("mp4|") | F.data.startswith("mp3|"))
async def download_process(call: types.CallbackQuery):
    format_type, url = call.data.split("|")
    await call.message.edit_text("⏳ Yuklanmoqda, kuting...")

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    # yt-dlp sozlamalari
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
    }

    if format_type == "mp3":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        ydl_opts['format'] = 'best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if format_type == "mp3":
                file_path = file_path.rsplit('.', 1)[0] + ".mp3"

            input_file = types.FSInputFile(file_path)
            if format_type == "mp3":
                await call.message.answer_audio(input_file, caption="🎵 @SizningKanal")
            else:
                await call.message.answer_video(input_file, caption="🎬 @SizningKanal")
            
            if os.path.exists(file_path):
                os.remove(file_path)
            await call.message.delete()
            
    except Exception as e:
        await call.message.answer(f"Xatolik: Link noto'g'ri yoki fayl juda katta.")

async def main():
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())