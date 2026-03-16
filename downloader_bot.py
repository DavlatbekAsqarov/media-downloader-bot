import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
import yt_dlp

# --- SOZLAMALAR ---
API_TOKEN = '8763063838:AAG4xA6wuEP9uL1jAs7LDoRXV2byIarol-s'
# Ikkita kanalingizni @ nomi bilan yozing
CHANNELS = ["@hozirchalikka", "@yaxshilikkada"] 

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- WEB SERVER (Render o'chib qolmasligi uchun) ---
async def handle(request): return web.Response(text="Bot ishlayapti!")
async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, "0.0.0.0", port).start()

# --- MAJBURIY OBUNANI TEKSHIRISH ---
async def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception:
            continue # Agar bot kanalda admin bo'lmasa yoki xato bo'lsa
    return True

# --- BOT HANDLERLARI ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(f"👋 Salom {message.from_user.first_name}!\nLink yuboring, men uni MP3 yoki Video qilib yuklab beraman.")

@dp.message(F.text.contains("http"))
async def link_received(message: types.Message):
    # Obunani tekshirish
    if not await check_subscription(message.from_user.id):
        builder = InlineKeyboardBuilder()
        for ch in CHANNELS:
            builder.row(types.InlineKeyboardButton(text=f"Obuna bo'lish", url=f"https://t.me/{ch[1:]}"))
        builder.row(types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub"))
        
        return await message.answer("❌ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:", 
                                    reply_markup=builder.as_markup())

    # Format tanlash tugmalari
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
async def download_media(call: types.CallbackQuery):
    format_type, url = call.data.split("|")
    await call.message.edit_text("⏳ Yuklash boshlandi, biroz kuting...")

    if not os.path.exists('downloads'): os.makedirs('downloads')

    # MP3 yoki MP4 uchun yt-dlp sozlamalari
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
            if format_type == "mp3": file_path = file_path.rsplit('.', 1)[0] + ".mp3"

            input_file = types.FSInputFile(file_path)
            if format_type == "mp3":
                await call.message.answer_audio(input_file, caption="🎵 @SizningBot_nomi")
            else:
                await call.message.answer_video(input_file, caption="🎬 @SizningBot_nomi")
            
            os.remove(file_path)
            await call.message.delete()
    except Exception as e:
        await call.message.answer(f"Xatolik yuz berdi: {str(e)}")

async def main():
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())