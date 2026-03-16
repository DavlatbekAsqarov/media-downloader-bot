import asyncio, os, logging, uuid
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import FSInputFile
from aiohttp import web
import yt_dlp

# --- ASOSIY SOZLAMALAR ---
API_TOKEN = '8763063838:AAG4xA6wuEP9uL1jAs7LDoRXV2byIarol-s'
CHANNELS = ['@hozirchhgfalikka', '@yaxshilikkada'] 
INSTAGRAM_URL = "https://www.instagram.com/samarkand070102?igsh=NzVuMGhmcXF2ZnFh"
DOWNLOAD_DIR = 'downloads'

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
url_ombori = {}

# --- OBUNANI TEKSHIRISH (Egalarni ham o'tkazadi) ---
async def obunani_tekshir(user_id):
    for ch in CHANNELS:
        try:
            azo = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            # Agar foydalanuvchi chiqib ketgan yoki haydalgan bo'lsa False
            if azo.status in ["left", "kicked"]:
                return False
        except Exception:
            # Agar bot admin bo'lmasa yoki kanal topilmasa ham False
            return False
    return True

# --- HANDLERLAR ---
@dp.message(Command("start"))
async def start_buyrugi(message: types.Message):
    if await obunani_tekshir(message.from_user.id):
        await message.answer(
            f"👋 Salom {message.from_user.full_name}!\n\n"
            "Menga video linkini yuboring, yuklab beraman."
        )
    else:
        knopkalar = InlineKeyboardBuilder()
        for ch in CHANNELS:
            knopkalar.row(types.InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{ch.replace('@', '')}"))
        knopkalar.row(types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check"))
        await message.answer("⚠️ Botdan foydalanish uchun kanallarga a'zo bo'ling:", reply_markup=knopkalar.as_markup())

@dp.callback_query(F.data == "check")
async def tekshirish_tugmasi(call: types.CallbackQuery):
    if await obunani_tekshir(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ Rahmat! Obuna tasdiqlandi. Endi link yuborishingiz mumkin.")
    else:
        await call.answer("❌ Siz hali kanallarga a'zo bo'lmagansiz!", show_alert=True)

@dp.message(F.text.startswith("http"))
async def link_kelganda(message: types.Message):
    if not await obunani_tekshir(message.from_user.id):
        return await message.answer("⚠️ Avval kanallarga obuna bo'ling!")

    # BUTTON_DATA_INVALID xatosini oldini olish uchun ID ishlatamiz
    id_raqam = str(uuid.uuid4())[:8]
    url_ombori[id_raqam] = message.text

    knopka = InlineKeyboardBuilder()
    knopka.row(
        types.InlineKeyboardButton(text="🎬 Video yuklash", callback_data=f"yuk|v|{id_raqam}"),
        types.InlineKeyboardButton(text="🎵 MP3 yuklash", callback_data=f"yuk|a|{id_raqam}")
    )
    await message.reply("📀 Qaysi formatda yuklaymiz?", reply_markup=knopka.as_markup())

@dp.callback_query(F.data.startswith("yuk|"))
async def yuklash(call: types.CallbackQuery):
    _, turi, id_raqam = call.data.split("|")
    link = url_ombori.get(id_raqam)
    
    if not link:
        return await call.answer("❌ Xatolik! Link topilmadi.")

    xabar = await call.message.edit_text("⏳ Yuklanmoqda...")
    
    opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'format': 'bestvideo[height<=720]+bestaudio/best' if turi == "v" else 'bestaudio/best',
    }

    manzil = None
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            # Indentation (surilish) xatosi bu yerda to'g'irlandi
            malumot =