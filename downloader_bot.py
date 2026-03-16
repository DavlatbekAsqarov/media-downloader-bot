import asyncio, os, logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web
import yt_dlp

# --- KONFIGURATSIYA ---
API_TOKEN = '8763063838:AAG4xA6wuEP9uL1jAs7LDoRXV2byIarol-s'
CHANNELS = ['@hozirchhgfalikka', '@yaxshilikkada'] 
DOWNLOAD_DIR = 'downloads'
if not os.path.exists(DOWNLOAD_DIR): os.makedirs(DOWNLOAD_DIR)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Uzun linklarni vaqtincha saqlash (BUTTON_DATA_INVALID xatosini yopadi)
url_temp = {}

async def check_sub(user_id):
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(ch, user_id)
            if m.status in ["left", "kicked"]: return False
        except: return False
    return True

@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer("Salom! Link yuboring, 720p HD formatda yuklab beraman.")

@dp.message(F.text.startswith("http"))
async def handle_url(m: types.Message):
    if not await check_sub(m.from_user.id):
        return await m.answer("Avval kanallarga obuna bo'ling!")
    
    url = m.text
    u_id = str(hash(url)) # Linkni qisqa ID ga aylantiramiz
    url_temp[u_id] = url
    
    kb = InlineKeyboardBuilder()
    kb.row(
        types.InlineKeyboardButton(text="🎬 Video (720p)", callback_data=f"v|{u_id}"),
        types.InlineKeyboardButton(text="🎵 MP3", callback_data=f"a|{u_id}")
    )
    await m.answer("Formatni tanlang:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith(("v|", "a|")))
async def dl(call: types.CallbackQuery):
    mode, u_id = call.data.split("|")
    url = url_temp.get(u_id)
    if not url: return await call.answer("Xatolik! Linkni qayta yuboring.")
    
    msg = await call.message.edit_text("⏳ Yuklanmoqda...")
    opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'max_filesize': 100 * 1024 * 1024, # 100MB Render uchun limit
        'format': 'bestvideo[height<=720]+bestaudio/best' if mode == "v" else 'bestaudio/best'
    }
    
    path = None
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            # Bu yerda probel (indentation) to'g'ri bo'lishi shart!
            info = await asyncio.to_thread(ydl.extract_info, url, download=True)
            path = ydl.prepare_filename(info)
            
            # Faylni yuborish
            f = types.FSInputFile(path)
            if mode == "v": await call.message.answer_video(f)
            else: await call.message.answer_audio(f)
            
            os.remove(path)
            await msg.delete()
    except Exception as e:
        logging.error(e)
        await msg.edit_text("❌ Xato! Fayl juda katta yoki FFmpeg o'rnatilmagan.")
        if path and os.path.exists(path): os.remove(path)

# Render uchun web server
async def handle(r): return web.Response(text="Bot OK")
async def main():
    app = web.Application(); app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    asyncio.create_task(web.TCPSite(runner, "0.0.0.0", 10000).start())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__": asyncio.run(main())