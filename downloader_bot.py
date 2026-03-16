import asyncio, os, uuid
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from yt_dlp import YoutubeDL

# --- SOZLAMALAR ---
TOKEN = "8763063838:AAG4xA6wuEP9uL1jAs7LDoRXV2byIarol-s"
CHANNELS = ["@hozirchalikka", "@yaxshilikkada"] 
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Obunani tekshirish
async def check_sub(user_id):
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            if m.status in ["left", "kicked"]: return False
        except: continue
    return True

@dp.message(Command("start"))
async def start(m: types.Message):
    await m.answer("🚀 **Bot tayyor!** Shunchaki link yuboring (YT, Insta, FB, X, TikTok).")

# LINK KELGANDA DARROV YUKLASH
@dp.message(F.text.contains("http"))
async def handle_link(m: types.Message):
    if not await check_sub(m.from_user.id):
        return await m.answer("⚠️ Bot ishlashi uchun @hozirchalikka va @yaxshilikkada kanallariga a'zo bo'ling!")

    wait_msg = await m.answer("⏳ Media tahlil qilinmoqda, kuting...")
    link = m.text.strip()
    fid = str(uuid.uuid4())
    
    opts = {
        'outtmpl': f"{fid}.%(ext)s",
        'format': 'best',
        'nocheckcertificate': True,
        'add_header': ['User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)'],
        'quiet': True
    }

    try:
        with YoutubeDL(opts) as ydl:
            await wait_msg.edit_text("🚀 Yuklash boshlandi...")
            info = ydl.extract_info(link, download=True)
            fname = ydl.prepare_filename(info)

        if os.path.exists(fname):
            video = types.FSInputFile(fname)
            await m.answer_video(video, caption="✅ **Tayyor!**\n\n🤖 @MediaSaverBot")
            await wait_msg.delete()
            os.remove(fname)
        else:
            await wait_msg.edit_text("❌ Fayl yuklanmadi.")
    except Exception as e:
        print(f"TERMINALDA XATO: {e}")
        await wait_msg.edit_text("⚠️ Xatolik yuz berdi. Link noto'g'ri yoki video yopiq.")

async def main():
    print("Bot ishga tushdi... 🔥")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())