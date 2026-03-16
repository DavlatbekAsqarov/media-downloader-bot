import asyncio, os, logging, uuid
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import FSInputFile
from aiohttp import web
import yt_dlp

# --- KONFIGURATSIYA ---
API_TOKEN = '8763063838:AAG4xA6wuEP9uL1jAs7LDoRXV2byIarol-s'
CHANNELS = ['@hozirchhgfalikka', '@yaxshilikkada'] 
INSTAGRAM_URL = "https://www.instagram.com/samarkand070102?igsh=NzVuMGhmcXF2ZnFh"
DOWNLOAD_DIR = 'downloads'
MAX_SIZE = 100 * 1024 * 1024  # 100 MB (Render Free uchun xavfsiz)

# Papkani yaratish
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Loglarni sozlash
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Vaqtinchalik xotira (Linklar va IDlar uchun)
url_storage = {}

# --- FUNKSIYALAR ---

async def is_subscribed(user_id):
    """Obunani tekshirish"""
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(ch, user_id)
            if m.status in ["left", "kicked"]: return False
        except: return False
    return True

def get_sub_kb():
    """Obuna tugmalari"""
    builder = InlineKeyboardBuilder()
    for i, ch in enumerate(CHANNELS, 1):
        builder.row(types.InlineKeyboardButton(text=f"📢 {i}-kanalga a'zo bo'lish", url=f"https://t.me/{ch.replace('@', '')}"))
    builder.row(types.InlineKeyboardButton(text="📸 Instagram (Majburiy emas)", url=INSTAGRAM_URL))
    builder.row(types.InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="recheck"))
    return builder.as_markup()

# --- HANDLERLAR ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if await is_subscribed(message.from_user.id):
        await message.answer(
            f"🌟 **Assalomu alaykum, {message.from_user.first_name}!**\n\n"
            "Men orqali YouTube, Instagram (Reels) va TikTok videolarini yuklab olishingiz mumkin.\n\n"
            "📥 **Link yuboring:**",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "⚠️ **Bot to'liq ishlashi uchun kanallarga a'zo bo'ling:**",
            reply_markup=get_sub_kb()
        )

@dp.callback_query(F.data == "recheck")
async def recheck_handler(call: types.CallbackQuery):
    if await is_subscribed(call.from_user.id):
        await call.message.delete()
        await call.message.answer("🎉 Rahmat! Obuna tasdiqlandi. Endi link yuboring.")
    else:
        await call.answer("❌ Hali obuna bo'lmagansiz!", show_alert=True)

@dp.message(F.text.startswith("http"))
async def link_processor(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        return await message.answer("❌ Avval kanallarga a'zo bo'ling!", reply_markup=get_sub_kb())

    url = message.text
    u_id = str(uuid.uuid4())[:8] # Qisqa ID yaratish
    url_storage[u_id] = url

    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(text="🎬 Video (720p)", callback_data=f"dl|mp4|{u_id}"),
        types.InlineKeyboardButton(text="🎵 Musiqa (MP3)", callback_data=f"dl|mp3|{u_id}")
    )
    
    await message.reply(
        "📀 **Sifatni tanlang:**\n\n"
        "ℹ️ _Katta hajmli videolar 720p formatda yuklanadi._",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("dl|"))
async def download_handler(call: types.CallbackQuery):
    _, f_type, u_id = call.data.split("|")
    url = url_storage.get(u_id)

    if not url:
        return await call.message.edit_text("❌ Link muddati tugagan. Qayta yuboring.")

    status_msg = await call.message.edit_text("🔍 **Tahlil qilinmoqda...**", parse_mode="Markdown")
    
    file_path = f"{DOWNLOAD_DIR}/{u_id}.%(ext)s"
    
    ydl_opts = {
        'outtmpl': file_path,
        'noplaylist': True,
        'max_filesize': MAX_SIZE,
        'quiet': True
    }

    if f_type == "mp4":
        ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
    else:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        await status_msg.edit_text("⏳ **Yuklanmoqda...**\n_Bu biroz vaqt olishi mumkin._", parse_mode="Markdown")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=True)
            real_path = ydl.prepare_filename(info)
            
            if f_type == "mp3":
                real