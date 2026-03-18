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
CHANNELS = ["@yaxshilikkada", "@hozirchalikka"] 
INSTAGRAM_URL = "https://www.instagram.com/samarkand070102"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

user_links = {}
insta_clicks = {}

# --- WEB SERVER (RENDER UCHUN) ---
async def handle(request): return web.Response(text="Bot is running!")
async def start_web_server():
    app = web.Application(); app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, "0.0.0.0", port).start()

# --- PROFILNI SOZLASH (MONTHLY USERS) ---
async def set_bot_profile():
    """Botning profil ma'lumotlarini professional ko'rinishga keltirish"""
    try:
        # Bot ismini yangilash
        await bot.set_my_name(name="Media Saver | 1.1M users")
        # 'About' qismi (Rasm ostidagi kulrang yozuv)
        await bot.set_my_short_description(short_description="1,198,069 monthly users")
        # 'Description' qismi (Startdan oldingi matn)
        await bot.set_my_description(
            description="🎬 Instagram, YouTube, TikTok va Threads videolarini yuklovchi №1 bot.\n\n📊 Hozirda 1 milliondan ortiq foydalanuvchi biz bilan!"
        )
        logging.info("Bot profili yangilandi! ✅")
    except Exception as e:
        logging.error(f"Profil yangilashda xato: {e}")

# --- OBUNA TEKSHIRISH ---
async def check_subscription(user_id):
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]: return False
        except Exception: continue
    return True

# --- HANDLERLAR ---
@dp.message(Command("start"))
async def start(message: types.Message):
    welcome_text = (
        f"👋 Salom {message.from_user.full_name}!\n\n"
        f"👥 Botimizdan hozirda **1,198,069** foydalanuvchi foydalanmoqda.\n\n"
        f"Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:"
    )
    
    builder = InlineKeyboardBuilder()
    for ch in CHANNELS:
        builder.row(types.InlineKeyboardButton(text=f"Telegram: {ch}", url=f"https://t.me/{ch[1:]}"))
    builder.row(types.InlineKeyboardButton(text="Instagram: Obuna bo'lish", url=INSTAGRAM_URL))
    builder.row(types.InlineKeyboardButton(text="✅ Obunani tasdiqlash", callback_data="re_check"))
    
    await message.answer(welcome_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "re_check")
async def re_check(call: types.CallbackQuery):
    user_id = call.from_user.id
    count = insta_clicks.get(user_id, 0)
    
    if not await check_subscription(user_id):
        await call.answer("❌ Telegram kanallarga hali a'zo bo'lmadingiz!", show_alert=True)
        return

    # Instagramga 2 marta yo'naltirish
    if count < 2:
        insta_clicks[user_id] = count + 1
        await call.answer("⚠️ Avval Instagram sahifamizga obuna bo'ling! (Qayta bosing)", show_alert=True)
        return

    await call.message.edit_text("Rahmat! Endi link yuborishingiz mumkin. ✅\n\n👥 Foydalanuvchilar: 1,198,069")

@dp.message(F.text.contains("http"))
async def handle_link(message: types.Message):
    if not await check_subscription(message.from_user.id) or insta_clicks.get(message.from_user.id, 0) < 2:
        return await start(message)

    user_links[message.from_user.id] = message.text
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🎬 Video (MP4)", callback_data="type_mp4"),
        types.InlineKeyboardButton(text="🎵 Musiqa (MP3)", callback_data="type_mp3")
    )
    await message.answer("Qaysi formatda yuklaymiz? 👇", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("type_"))
async def download_process(call: types.CallbackQuery):
    url = user_links.get(call.from_user.id)
    if not url: return await call.answer("Link topilmadi.", show_alert=True)

    f_type = call.data.split("_")[1]
    status_msg = await call.message.edit_text("⏳ Yuklanmoqda...")

    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'format': 'best[filesize<45M]/best' 
    }
    
    if f_type == "mp3":
        ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}]})

    try:
        if not os.path.exists('downloads'): os.makedirs('downloads')
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = ydl.prepare_filename(info)
            if f_type == "mp3": path = path.rsplit('.', 1)[0] + ".mp3"
            
            fayl = types.FSInputFile(path)
            caption_text = f"✅ @MediaSaver24Bot orqali yuklab olindi\n👥 Foydalanuvchilar: 1,198,069"
            
            if f_type == "mp3": await call.message.answer_audio(fayl, caption=caption_text)
            else: await call.message.answer_video(fayl, caption=caption_text)
            
            if os.path.exists(path): os.remove(path)
            await status_msg.delete()
    except Exception:
        await call.message.answer("❌ Xatolik! Fayl juda katta (50MB+) yoki link yopiq.")

async def main():
    asyncio.create_task(start_web_server())
    await set_bot_profile()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
