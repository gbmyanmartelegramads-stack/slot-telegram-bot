import os
import logging
import hashlib
import io
import asyncio
import random
import sqlite3
from aiohttp import web
import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageDraw
import imageio.v3 as iio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, CommandHandler, filters

# Logging Setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")
PORT = int(os.environ.get("PORT", "10000"))

ADMIN_ID = 1759541320  
ADMIN_USERNAME = "osker0296"  

COST_PER_IMAGE = 1   
COST_PER_VIDEO = 2   

def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            credits INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_user_data(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT credits FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return {"credits": row[0]} if row else {"credits": 0}

def update_user_data(user_id, credits):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, credits) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET credits = ?
    """, (user_id, credits, credits))
    conn.commit()
    conn.close()

async def handle_ping(request):
    return web.Response(text="Ultimate Pro Scrambler Bot is running 24/7!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_url = f"https://t.me/{ADMIN_USERNAME}"
    welcome_text = "🚀 **Ultimate Pro AI-Bypass Scrambler Bot** အသင့်ဖြစ်ပါပြီဆရာ။"
    keyboard = [[InlineKeyboardButton("💬 Credits ဝယ်ယူရန် Admin ဆီသို့", url=admin_url)]]
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text("👑 ဆရာဟာ Admin ဖြစ်ပါတယ်။")
        return
    data = get_user_data(user_id)
    await update.message.reply_text(f"💎 လက်ကျန် Credits: `{data['credits']}` Credits", parse_mode="Markdown")

async def add_credit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: 
        return
    try:
        args = context.args
        target_user_id, amount = int(args[0]), int(args[1])
        new_balance = get_user_data(target_user_id)["credits"] + amount
        update_user_data(target_user_id, new_balance)
        await update.message.reply_text(f"✅ Success! New Balance: {new_balance}")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Error in arguments. Usage: `/add <user_id> <amount>`", parse_mode="Markdown")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    if user_id != ADMIN_ID and user_data["credits"] < COST_PER_IMAGE:
        await update.message.reply_text("❌ Credits မလုံလောက်ပါဆရာ။")
        return

    status_msg = await update.message.reply_text("⚡ Processing Advanced AI-Bypass Image Scramble...")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        
        # 1. Open Image & Strip Metadata (EXIF Data)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = image.size
        
        # 2. Subtle Crop (AI Hash Matching ကို လှည့်စားရန် 1% to 2% ခန့် ဘောင်ဖြတ်ခြင်း)
        crop_w = int(w * random.uniform(0.005, 0.015))
        crop_h = int(h * random.uniform(0.005, 0.015))
        image = image.crop((crop_w, crop_h, w - crop_w, h - crop_h))
        w, h = image.size
        
        # 3. NumPy Array Transformation (Gamma, Noise & Color Shift)
        img_array = np.array(image, dtype=np.float32)
        
        # Color Shifting (RGB Channels ကို တန်ဖိုးအနည်းငယ်စီ အပြောင်းအလဲလုပ်ခြင်း)
        for i in range(3):
            gamma = random.uniform(0.85, 1.15)
            img_array[:, :, i] = 255.0 * (np.clip(img_array[:, :, i], 0, 255) / 255.0) ** gamma
            
        # Gaussian Noise ထည့်ခြင်း
        noise = np.random.normal(0, 12.0, img_array.shape)
        img_array = np.clip(img_array + noise, 0, 255)
        
        image_processed = Image.fromarray(img_array.astype(np.uint8))
        draw = ImageDraw.Draw(image_processed, "RGBA")
        
        # Random Opacity rectangles များထည့်၍ pHash ကို ဖျက်ဆီးခြင်း
        for _ in range(random.randint(12, 20)):
            rx1, ry1 = random.randint(0, max(0, w - 30)), random.randint(0, max(0, h - 30))
            rx2, ry2 = rx1 + random.randint(15, 35), ry1 + random.randint(15, 35)
            draw.rectangle([rx1, ry1, rx2, ry2], fill=(random.randint(0,255), random.randint(0,255), random.randint(0,255), random.randint(2,6)))

        output_buffer = io.BytesIO()
        # Quality ကို Random ဖြတ်၍ သိမ်းဆည်းခြင်း (EXIF လုံးဝမပါစေရန်)
        image_processed.save(output_buffer, format="JPEG", quality=random.randint(75, 85), subsampling=0)
        processed_bytes = output_buffer.getvalue()

        if user_id != ADMIN_ID:
            update_user_data(user_id, user_data["credits"] - COST_PER_IMAGE)

        await update.message.reply_photo(photo=processed_bytes, caption="⚡ Advanced AI-Bypass Scramble Complete!")
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Error processing image.")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    if user_id != ADMIN_ID and user_data["credits"] < COST_PER_VIDEO:
        await update.message.reply_text("❌ Credits မလုံလောက်ပါဆရာ။")
        return

    status_msg = await update.message.reply_text("🎬 Processing Advanced Video & Audio Bypass...")
    video = update.message.video
    file = await context.bot.get_file(video.file_id)
    
    uid = hashlib.md5(str(user_id).encode()).hexdigest()[:8]
    in_path, out_path = f"in_{uid}.mp4", f"out_{uid}.mp4"
    
    try:
        await file.download_to_drive(in_path)
        # Video Speed ကို အနည်းငယ်အတိုးအလျှော့လုပ်ခြင်း (AI Hash များကို ရှုပ်ထွေးစေရန်)
        speed = random.choice([0.94, 0.96, 0.98, 1.02, 1.04, 1.06])
        
        frames = []
        for frame in iio.imiter(in_path):
            noise = np.random.normal(0, 4.0, frame.shape).astype(np.float32)
            frames.append(np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8))
        
        if frames:
            iio.imwrite(out_path, frames, fps=25.0, plugin="pyav", quality=6, output_params=[
                "-vf", f"setpts={1.0/speed}*PTS,crop=iw-2:ih-2", # ဘောင်ပါ အနည်းငယ် ဖြတ်ထုတ်ခြင်း
                "-af", f"atempo={speed},acompressor=threshold=-12dB:ratio=4:attack=100:release=400"
            ])
            
        if user_id != ADMIN_ID:
            update_user_data(user_id, user_data["credits"] - COST_PER_VIDEO)

        with open(out_path, 'rb') as vf:
            await update.message.reply_video(video=vf, caption="✅ Advanced Video Bypass Complete!")
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Error processing video.")
    finally:
        for p in [in_path, out_path]:
            if os.path.exists(p): 
                os.remove(p)

async def main_async():
    if not TOKEN: 
        logger.error("TOKEN environment variable not set!")
        return
        
    app = Application.builder().token(TOKEN).build()
    app.add_handlers([
        CommandHandler("start", start),
        CommandHandler("balance", balance_command),
        CommandHandler("add", add_credit_command),
        MessageHandler(filters.PHOTO, handle_image),
        MessageHandler(filters.VIDEO, handle_video)
    ])
    
    # Web Server စတင်ခြင်း (Render / Koyeb ကဲ့သို့ Hosting တွေအတွက်)
    web_app = web.Application()
    web_app.router.add_get("/", handle_ping)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Web server started on port {PORT}")

    # Telegram Bot ကို စတင်ခြင်း
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Telegram Bot started polling...")

    try:
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        await runner.cleanup()

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
