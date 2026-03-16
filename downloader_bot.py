import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
import yt_dlp

# --- KONFIGURATSIYA ---
API_TOKEN = '8763063838:AAG4xA6wuEP9uL1jAs7LDoRXV2byIarol-s'
CHANNELS = ['@hozirchhgfalikka', '@yaxshilikkada'] 
INSTAGRAM_URL = "https://www.instagram.com/samarkand070102?igsh=NzVuMGhmcXF2ZnFh"
DOWNLOAD_DIR = 'downloads'
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 Megabayt (Render uchun xavfsiz chegara)

# Yuklamalar uchun papka yaratish
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Loglarni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- MAJBURIY OBUNA TEKSHIRISH ---
async def check_subscription(user_id):
    """Foydalanuvchi barcha kanallarga a'zo ekanini tekshiradi."""
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ["left", "kicked"]:
                return False
        except Exception as e:
            logger.error(f"Kanalni tekshirishda xato ({channel}): {e}")
            # Agar bot kanal admini bo'lmasa, tekshirishni o'tkazib yuboradi
            continue
    return True

def get_sub_keyboard():
    """Obuna bo'lish tugmalarini generatsiya qiladi."""
    builder = InlineKeyboardBuilder()
    for i, channel in enumerate(CHANNELS, 1):
        builder.row(types.InlineKeyboardButton(
            text=f"📢 {i}-kanalga obuna bo'lish", 
            url=f"https://t.me/{channel.replace('@', '')}")
        )
    builder.row(types.InlineKeyboardButton(text="📸 Instagramga o'tish", url=INSTAGRAM_URL))
    builder.row(types.InlineKeyboardButton(text="✅ Obunani tasdiqlash", callback_data="check_sub"))
    return builder.as_markup()

# --- RENDER UCHUN WEB SERVER ---
async def handle(request):
    return web.Response(text="Bot muvaffaqiyatli ishlamoqda!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Web-server portda ishga tushdi: {port}")

# --- BOT HANDLERLARI ---

@dp.message(Command("start"))
async def start_command(message: types.Message):
    if await check_subscription(message.from_user.id):
        await message.answer(
            f"👋 Salom {message.from_user.first_name}!\n\n"
            "YouTube, Instagram yoki TikTok'dan link yuboring.\n"
            "Men sizga **720p HD** sifatda yuklab beraman! 🚀",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "⚠️ **Diqqat!**\n\nBotdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz shart:",
            reply_markup=get_sub_keyboard(),
            parse_mode="Markdown"
        )

@dp.callback_query(F.data == "check_sub")
async def callback_check_sub(call: types.CallbackQuery):
    if await check_subscription(call.from_user.id):
        await call.message.delete()
        await call.message.answer("✅ Rahmat! Obuna tasdiqlandi. Endi link yuborishingiz mumkin.")
    else:
        await call.answer("❌ Hali hamma kanallarga obuna bo'lmagansiz!", show_alert=True)

@dp.message(F.text.startswith("http"))
async def link_handler(message: types.Message):
    # Har safar link yuborganda obunani tekshirish
    if not await check_subscription(message.from_user.id):
        return await message.answer("❌ Avval kanallarga obuna bo'ling!", reply_markup=get_sub_keyboard())

    url = message.text
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="🎬 Video (720p HD)", callback_data=f"mp4|{url}"),
        types.InlineKeyboardButton(text="🎵 Musiqa (MP3)", callback_data=f"mp3|{url}")
    )
    
    await message.answer(
        "📝 **Qaysi formatda yuklaymiz?**\n\n"
        "⚠️ _Hajmi 100 MB dan katta bo'lgan videolar server cheklovi sababli yuklanmasligi mumkin._",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("mp4|") | F.data.startswith("mp3|"))
async def process_download(call: types.CallbackQuery):
    format_type, url = call.data.split("|")
    status_msg = await call.message.edit_text("🔍 Video tahlil qilinmoqda, kuting...")

    # yt-dlp sozlamalari (Optimallashtirilgan)
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'max_filesize': MAX_FILE_SIZE, 
    }

    if format_type == "mp3":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        # 720p sifatni tanlash
        ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'

    temp_path = None
    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. Yuk