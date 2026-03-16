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
MAX_SIZE = 100 * 1024 * 1024  # 100 MB cheklov

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Linklarni vaqtincha saqlash (Uzun linklar xato bermasligi uchun)
url_storage = {}

# --- FUNKSIYALAR ---

async def is_subscribed(user_id):
    """Foydalanuvchi kanallarga a'zo ekanini tekshirish"""
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(ch, user_id)
            if m.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True

def get_sub_kb():
    """Obuna bo'lish tugmalari"""
    builder = InlineKeyboardBuilder()
    for i, ch in enumerate(CHANNELS, 1):
        builder.row(types.InlineKeyboardButton(text=f"📢 {i}-kanalga a'zo bo'lish", url=f"https://t.me/{ch.replace('@', '')}"))
    builder.row(types.InlineKeyboardButton(text="📸 Instagram (Majburiy)", url=INSTAGRAM_URL))
    builder.row(types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="recheck"))
    return builder.as_markup()

# --- HANDLERLAR ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if await is_subscribed(message.from_user.id):
        await message.answer(
            f"🌟 **Assalomu alaykum, {message.from_user.first_name}!**\n\n"
            "YouTube, Instagram yoki TikTok linkini yuboring, men yuklab beraman.\n\n"
            "📥 **Linkni yuboring:**",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "⚠️ **Botdan foydalanish uchun quyidagi kanallarga a'zo bo'lishingiz shart:**",
            reply_markup=get_sub_kb()
        )

@dp.callback_query(F.data == "recheck")
async def recheck_handler(call: types.CallbackQuery):
    if await is_subscribed(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ Rahmat! Obuna tasdiqlandi. Endi link yuborishingiz mumkin.")
    else:
        await call.answer("❌ Hali hamma kanallarga a'zo bo'lmagansiz!", show_alert=True)

@dp.message(F.text.startswith("http"))
async def link_processor(message: types.Message):
    if not await is_subscribed(message.from_user.id):
        return await message.answer("❌ Avval kanallarga a'zo bo'ling!", reply_markup=get_sub_kb())

    url = message.text
    u_id = str(uuid.uuid4())[:8] # Uzun linkni qisqa IDga aylantirish
    url_storage[u_id] = url

    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(text="🎬 Video (720p)", callback_data=f"dl|v|{u_id}"),
        types.InlineKeyboardButton(text="🎵 Musiqa (MP3)", callback_data=f"dl|a|{u_id}")
    )
    
    await message.reply(
        "📀 **Formatni tanlang:**\n\n"
        "ℹ️ _Hajmi 100 MB gacha bo'lgan videolarni yuklay olaman._",
        reply_markup=kb.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("dl|"))
async def download_handler(call: types.CallbackQuery):
    _, mode, u_id = call.data.split("|")
    url = url_storage.get(u_id)

    if not url:
        return await call.message.edit_text("❌ Xatolik! Link topilmadi, qayta yuboring.")

    status_msg = await call.message.edit_text("🔍 **Tahlil qilinmoqda...**", parse_mode="Markdown")
    
    # Yuklash sozlamalari
    opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'max_filesize': MAX_SIZE,
        'format': 'bestvideo[height<=720]+bestaudio/best' if mode == "v" else 'bestaudio/best'
    }

    path = None
    try:
        await status_msg.edit_text("⏳ **Yuklanmoqda...**\n_Server ishlamoqda, kuting..._", parse_mode="Markdown")
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            # Ma'lumotni yuklash
            info = await asyncio.to_thread(ydl.extract_info, url, download=True)
            path = ydl.prepare_filename(