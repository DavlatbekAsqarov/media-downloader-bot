import asyncio, os, logging, uuid
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import FSInputFile
from aiohttp import web
import yt_dlp

# --- SOZLAMALAR ---
API_TOKEN = '8763063838:AAG4xA6wuEP9uL1jAs7LDoRXV2byIarol-s'
CHANNELS = ['@hozirchalikka', '@yaxshilikkada'] 
INSTAGRAM_URL = "https://www.instagram.com/samarkand070102?igsh=NzVuMGhmcXF2ZnFh"
DOWNLOAD_DIR = 'downloads'

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Linklarni vaqtincha saqlash (ID orqali xatolikni oldini olamiz)
url_ombori = {}

async def obunani_tekshir(user_id):
    for ch in CHANNELS:
        try:
            azo = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            if azo.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if await obunani_tekshir(message.from_user.id):
        await message.answer(f"🌟 Salom {message.from_user.first_name}!\nVideo linkini yuboring, yuklab beraman.")
    else:
        kb = InlineKeyboardBuilder()
        for ch in CHANNELS:
            kb.row(types.InlineKeyboardButton(text="📢 Obuna bo'lish", url=f"https://t.me/{ch.replace('@', '')}"))
        kb.row(types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check"))
        await message.answer("⚠️ Botdan foydalanish uchun kanallarga a'zo bo'ling:", reply_markup=kb.as_markup())

@dp.callback_query(F.data == "check")
async def check_callback(call: types.CallbackQuery):
    if await obunani_tekshir(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ Rahmat! Endi link yuborishingiz mumkin.")
    else:
        await call.answer("❌ Obuna bo'lmagansiz!", show_alert=True)

@dp.message(F.text.startswith("http"))
async def link_handler(message: types.Message):
    if not await obunani_tekshir(message.from_user.id):
        return await message.answer("⚠️ Avval kanallarga obuna bo'ling!")

    # ID yaratish (64 baytdan oshmasligi uchun)
    u_id = str(uuid.uuid4())[:8]
    url_ombori[u_id] = message.text

    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(text="🎬 Video", callback_data=f"dl|v|{u_id}"),
        types.InlineKeyboardButton(text="🎵 MP3", callback_data=f"dl|a|{u_id}")
    )
    await message.reply("📀 Qaysi formatda yuklaymiz?", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("dl|"))
async def download_handler(call: types.CallbackQuery):
    _, turi, u_id = call.data.split("|")
    link = url_ombori.get(u_id)
    
    if not link:
        return await call.answer("❌ Xatolik! Link topilmadi.")

    msg = await call.message.edit_text("⏳ Yuklanmoqda...")
    
    opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'format': 'bestvideo[height<=720]+bestaudio/best' if turi == "v" else 'bestaudio/best',
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            # Bu yerda IndentationError to'g'irlandi
            info = await asyncio.to_thread(ydl.extract_info, link, download=True)
            path = ydl.prepare_filename(info)
            
            await call.message.answer_video(FSInputFile(path), caption=f"🎬 @media_downloader_bot\n📸 {INSTAGRAM_URL}")
            if os.path.exists(path): os.remove(path)
            await msg.delete()
    except Exception:
        await msg.edit_text("❌ Xatolik! Fayl juda katta yoki link xato.")

# --- WEB SERVER ---
async def handle(request): return web.Response(text="OK")
async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", 10000).start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())