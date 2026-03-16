import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
import yt_dlp

API_TOKEN = '8763063838:AAG4xA6wuEP9uL1jAs7LDoRXV2byIarol-s'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Linklarni vaqtinchalik saqlash uchun savatcha
user_links = {}

async def handle(request): return web.Response(text="Bot is running!")
async def start_web_server():
    app = web.Application(); app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, "0.0.0.0", port).start()

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(f"👋 Salom {message.from_user.first_name}!\nLink yuboring, Video yoki MP3 qilib beraman.")

@dp.message(F.text.contains("http"))
async def handle_link(message: types.Message):
    url = message.text
    # Linkni foydalanuvchi IDsi bilan saqlab qo'yamiz (tugma buzilmasligi uchun)
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
    status_msg = await call.message.edit_text("⏳ Yuklanmoqda...")

    if not os.path.exists('downloads'): os.makedirs('downloads')

    ydl_opts = {'outtmpl': 'downloads/%(title)s.%(ext)s', 'noplaylist': True}
    if format_type == "mp3":
        ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]})
    else:
        ydl_opts['format'] = 'best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            if format_type == "mp3": path = path.rsplit('.', 1)[0] + ".mp3"
            
            fayl = types.FSInputFile(path)
            if format_type == "mp3": await call.message.answer_audio(fayl)
            else: await call.message.answer_video(fayl)
            
            if os.path.exists(path): os.remove(path)
            await status_msg.delete()
            del user_links[call.from_user.id] # Tozalash
    except Exception as e:
        logging.error(e)
        await call.message.answer("❌ Xatolik! Link yoki serverda muammo.")

async def main():
    asyncio.create_task(start_web_server())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())