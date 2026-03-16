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
MAX_SIZE = 100 * 1024 * 1024  # 100 MB

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
url_ombori = {}

# --- OBUNANI TEKSHIRISH ---
async def obunani_tekshir(user_id):
    for ch in CHANNELS:
        try:
            azo = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            # Siz 'creator' yoki 'administrator' bo'lsangiz ham ruxsat beradi
            if azo.status in ["left", "kicked"]:
                return False
        except Exception:
            return False
    return True

# --- BUYRUQLAR ---
@dp.message(Command("start"))
async def start_buyrugi(message: types.Message):
    if await obunani_tekshir(message.from_user.id):
        await message.answer(
            f"👋 Assalomu alaykum, {message.from_user.full_name}!\n\n"
            "Menga YouTube, Instagram yoki TikTok linkini yuboring, men uni sizga yuklab beraman."
        )
    else:
        knopkalar = InlineKeyboardBuilder()
        for ch in CHANNELS:
            knopkalar.row(types.InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=f"https://t.me/{ch.replace('@', '')}"))
        knopkalar.row(types.InlineKeyboardButton(text="✅ Tekshirish", callback_mode="check"))
        await message.answer("⚠️ Botdan foydalanish uchun kanallarga a'zo bo'lishingiz shart:", reply_markup=knopkalar.as_markup())

@dp.callback_query(F.data == "check")
async def tekshirish_tugmasi(call: types.CallbackQuery):
    if await obunani_tekshir(call.from_user.id):
        await call.message.delete()
        await call.message.answer("🎉 Rahmat! Obuna tasdiqlandi. Endi link yuborishingiz mumkin.")
    else:
        await call.answer("❌ Siz hali hamma kanallarga a'zo bo'lmagansiz!", show_alert=True)

@dp.message(F.text.startswith("http"))
async def link_qabul_qilish(message: types.Message):
    if not await obunani_tekshir(message.from_user.id):
        return await message.answer("⚠️ Avval kanallarga obuna bo'ling!")

    link = message.text
    id_raqam = str(uuid.uuid4())[:8]
    url_ombori[id_raqam] = link # BUTTON_DATA_INVALID xatosini oldini oladi

    knopka = InlineKeyboardBuilder()
    knopka.row(
        types.InlineKeyboardButton(text="🎬 Video", callback_data=f"yuk|v|{id_raqam}"),
        types.InlineKeyboardButton(text="🎵 MP3", callback_data=f"yuk|a|{id_raqam}")
    )
    await message.reply("📀 Qaysi formatda yuklaymiz?", reply_markup=knopka.as_markup())

@dp.callback_query(F.data.startswith("yuk|"))
async def yuklash_jarayoni(call: types.CallbackQuery):
    _, turi, id_raqam = call.data.split("|")
    link = url_ombori.get(id_raqam)
    
    holat_xabari = await call.message.edit_text("⏳ Yuklanmoqda, iltimos kuting...")
    
    sozlamalar = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'format': 'bestvideo[height<=720]+bestaudio/best' if turi == "v" else 'bestaudio/best',
        'max_filesize': MAX_SIZE
    }

    manzil = None
    try:
        with yt_dlp.YoutubeDL(sozlamalar) as ydl:
            # IndentationError xatosi bu yerda to'g'irlandi
            malumot = await asyncio.to_thread(ydl.extract_info, link, download=True)
            manzil = ydl.prepare_filename(malumot)
            
            fayl = FSInputFile(manzil)
            if turi == "v":
                await call.message.answer_video(fayl, caption=f"🎬 @media_downloader_bot\n📸 {INSTAGRAM_URL}")
            else:
                await call.message.answer_audio(fayl, caption=f"🎵 @media_downloader_bot\n📸 {INSTAGRAM_URL}")
            
            if os.path.exists(manzil): os.remove(manzil)
            await holat_xabari.delete()
    except Exception as e:
        logging.error(e)
        await holat_xabari.edit_text("❌ Xatolik yuz berdi! Fayl juda katta yoki link noto'g'ri.")
        if manzil and os.path.exists(manzil): os.remove(manzil)

# --- RENDER SERVERINI YURGIZISH ---
async def web_javob(request): return web.Response(text="Bot ishlashga tayyor!")
async def main():
    app = web.Application()
    app.router.add_get("/", web_javob)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", 10000).start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())