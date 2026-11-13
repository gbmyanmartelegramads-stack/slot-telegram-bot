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

# Logging Setup (Fixed __name__)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")
PORT = int(os.environ.get("PORT", "10000"))

# ဆရာ့ရဲ့ Telegram Admin အချက်အလက်များ
ADMIN_ID = 1759541320  
ADMIN_USERNAME = "osker0296"  

# 💰 ဈေးနှုန်းသတ်မှတ်ချက်များ (Prepaid Model)
COST_PER_IMAGE = 1   # ပုံ ၁ ပုံလျှင် 1 Credit (500 Baht / 60,000 ကျပ်)
COST_PER_VIDEO = 2   # ဗီဒီယို ၁ ခုလျှင် 2 Credits (700 Baht / 100,000 ကျပ်)

# ==========================================
# Database Setup (SQLite for Persistent Credits)
# ==========================================
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
    if row:
        return {"credits": row[0]}
    else:
        return {"credits": 0}

def update_user_data(user_id, credits):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, credits) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET credits = ?
    """, (user_id, credits, credits))
    conn.commit()
    conn.close()

# ==========================================
# Web Server for Uptime Monitoring (24/7 Active)
# ==========================================
async def handle_ping(request):
    return web.Response(text="Absolute Ultimate Scrambler Bot is running 24/7 and secure!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Absolute Ultimate Web server started on port {PORT}")

# ==========================================
# Telegram Commands
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_url = f"https://t.me/{ADMIN_USERNAME}"
    welcome_text = (
        "မင်္ဂလာပါဆရာ! 🚀\n\n"
        "Facebook Ads Absolute Ultimate Quantum Scrambler Bot (Zero-Trace Multi-Layer Protection) အသင့်ဖြစ်ပါပြီဆရာ။\n\n"
        "💰 ဝန်ဆောင်မှု ဈေးနှုန်းများ:\n"
        "-------------------------------------\n"
        "🖼️ ပုံ ၁ ပုံ = 500 Baht (သို့) 60,000 ကျပ် (1 Credit)\n"
        "🎬 ဗီဒီယို ၁ ခု = 700 Baht (သို့) 100,000 ကျပ် (2 Credits)\n"
        "-------------------------------------\n\n"
        "📌 အသုံးပြုရန် Credits ဝယ်ယူလိုပါက အောက်ပါခလုတ်ကိုနှိပ်၍ Admin ထံ တိုက်ရိုက်ဆက်သွယ်နိုင်ပါသည်။"
    )
    keyboard = [[InlineKeyboardButton("💬 Credits ဝယ်ယူရန် Admin ဆီသို့ ဆက်သွယ်မည်", url=admin_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text("👑 ဆရာဟာ Admin ဖြစ်ပါတယ်။ Credits ကန့်သတ်ချက် မရှိပါဘူးဆရာ။")
        return
        
    data = get_user_data(user_id)
    admin_url = f"https://t.me/{ADMIN_USERNAME}"
    keyboard = [[InlineKeyboardButton("💬 Credits ထပ်မံဝယ်ယူရန်", url=admin_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"📊 ဆရာ့ရဲ့ အကောင့်အချက်အလက်များ:\n\n"
        f"💎 လက်ကျန် Credits: {data['credits']} Credits",
        reply_markup=reply_markup
    )

async def add_credit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ ဒီ Command ကို အသုံးပြုခွင့် မရှိပါဘူးဆရာ။")
        return
        
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("❌ ဥပမာ - /add [User_ID] [Credits] လို့ ရိုက်ပါဆရာ။ (ဥပမာ: /add 1759541320 1 )")
            return
        
        target_user_id = int(args[0])
        amount = int(args[1])
        
        target_data = get_user_data(target_user_id)
        new_balance = target_data["credits"] + amount
        update_user_data(target_user_id, new_balance)
        
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"🎉 Admin မှ ဆရာ့အကောင့်သို့ Credits {amount} ထည့်သွင်းပေးလိုက်ပါပြီဆရာ။\n💎 လက်ကျန်စုစုပေါင်း: {new_balance} Credits"
            )
        except:
            pass

        await update.message.reply_text(f"✅ User ID: {target_user_id} ကို Credits {amount} ထည့်သွင်းပေးလိုက်ပါပြီဆရာ။ (လက်ကျန်စုစုပေါင်း: {new_balance} Credits)")
    except Exception as e:
        logger.error(f"Add Credit Error: {e}")
        await update.message.reply_text("❌ အမှားအယွင်း ရှိနေပါသည်ဆရာ။")

# ==========================================
# Absolute Ultimate Image Scrambler Handler
# ==========================================
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    if user_id != ADMIN_ID:
        if user_data["credits"] < COST_PER_IMAGE:
            admin_url = f"https://t.me/{ADMIN_USERNAME}"
            keyboard = [[InlineKeyboardButton("💬 Admin ဆီသို့ ဆက်သွယ်၍ Credits ဝယ်ယူရန်", url=admin_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"❌ လက်ကျန် Credits မလုံလောက်တော့ပါဆရာ။ (လိုအပ်သည်: {COST_PER_IMAGE} Credit | လက်ကျန်: {user_data['credits']} Credits)\n\n"
                "📌 ဈေးနှုန်း: ပုံ ၁ ပုံ = 500 Baht (သို့) 60,000 ကျပ်\n"
                "ဆက်လက်အသုံးပြုရန်အတွက် Admin ထံ ဆက်သွယ်၍ Credits ဝယ်ယူနိုင်ပါသည်။",
                reply_markup=reply_markup
            )
            return

    status_message = await update.message.reply_text("⚡ Absolute Ultimate Matrix Engine ဖြင့် ပုံကို အစွန်းဆုံး Scramble လုပ်နေပါပြီဆရာ...")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = image.size
        
        # --- LAYER 1: Multi-Stage Structural & Perspective Warping ---
        pad_color = (random.randint(220, 255), random.randint(220, 255), random.randint(220, 255))
        image = ImageOps.expand(image, border=random.randint(5, 8), fill=pad_color)
        new_w, new_h = image.size
        
        dx = new_w * 0.035
        dy = new_h * 0.035
        coeffs = [
            1.0 + random.uniform(-0.045, 0.045), random.uniform(-0.035, 0.035), random.uniform(-dx, dx),
            random.uniform(-0.035, 0.035), 1.0 + random.uniform(-0.045, 0.045), random.uniform(-dy, dy),
            random.uniform(-0.00018, 0.00018), random.uniform(-0.00018, 0.00018)
        ]
        image = image.transform((new_w, new_h), Image.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC, fillcolor=pad_color)
        image = image.rotate(random.uniform(-4.0, 4.0), expand=False, fillcolor=pad_color)
        
        # --- LAYER 2: Advanced Semantic Feature & Keypoint Disruption ---
        draw = ImageDraw.Draw(image, "RGBA")
        for _ in range(random.randint(6, 12)):
            rx1 = random.randint(0, new_w - 50)
            ry1 = random.randint(0, new_h - 50)
            rx2 = rx1 + random.randint(30, 60)
            ry2 = ry1 + random.randint(30, 60)
            patch_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(12, 25))
            draw.rectangle([rx1, ry1, rx2, ry2], fill=patch_color)

        img_array = np.array(image, dtype=np.float32)
        for i in range(3):
            gamma = random.uniform(0.88, 1.12)
            img_array[:, :, i] = 255.0 * (np.clip(img_array[:, :, i], 0, 255) / 255.0) ** gamma
            
        noise_gradient = np.random.normal(0, 8.0, img_array.shape)
        img_array = img_array + noise_gradient
        
        num_speckles = random.randint(250, 400)
        for _ in range(num_speckles):
            sy = random.randint(0, img_array.shape[0] - 1)
            sx = random.randint(0, img_array.shape[1] - 1)
            img_array[sy, sx, :] = np.clip(img_array[sy, sx, :] + random.choice([-50, 50]), 0, 255)

        for i in range(3):
            shift_val = random.uniform(-4.0, 4.0)
            img_array[:, :, i] += shift_val
            
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        image = Image.fromarray(img_array)
        
        # Complete Metadata & EXIF Eradication + Cryptographic Salt Tail
        data = list(image.getdata())
        clean = Image.new(image.mode, image.size)
        clean.putdata(data)
        
        output_buffer = io.BytesIO()
        clean.save(output_buffer, format="JPEG", quality=random.randint(75, 85), subsampling=0)
        processed_bytes = output_buffer.getvalue()

        unique_hash = hashlib.sha256(processed_bytes).digest()
        final_image_bytes = processed_bytes + unique_hash[:64]  # Double Salt Tail
        
        if user_id != ADMIN_ID:
            new_credits = user_data["credits"] - COST_PER_IMAGE
            update_user_data(user_id, new_credits)
            caption_text = f"⚡ Ultimate Scramble အောင်မြင်ပါပြီဆရာ။ (-{COST_PER_IMAGE} Credit | လက်ကျန်: {new_credits} Credits)"
        else:
            caption_text = "⚡ Ultimate Scramble ပြီးပါပြီဆရာ (Admin)."

        await update.message.reply_photo(
            photo=bytes(final_image_bytes),
            caption=caption_text
        )
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
        
    except Exception as e:
        logger.error(f"Ultimate Image Scramble Error: {e}")
        await update.message.reply_text("❌ ပုံပြုပြင်ရာတွင် အမှားအယွင်း ရှိသွားပါပြီဆရာ။")

# ==========================================
# Absolute Ultimate Video & Audio Scrambler Handler
# ==========================================
async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    if user_id != ADMIN_ID:
        if user_data["credits"] < COST_PER_VIDEO:
            admin_url = f"https://t.me/{ADMIN_USERNAME}"
            keyboard = [[InlineKeyboardButton("💬 Admin ဆီသို့ ဆက်သွယ်၍ Credits ဝယ်ယူရန်", url=admin_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"❌ ဗီဒီယိုဖိုင် ထုတ်လုပ်ရန်အတွက် Credits မလုံလောက်ပါဆရာ။ (လိုအပ်သည်: {COST_PER_VIDEO} Credits | လက်ကျန်: {user_data['credits']} Credits)\n\n"
                "📌 ဈေးနှုန်း: ဗီဒီယို ၁ ခု = 700 Baht (သို့) 100,000 ကျပ်\n"
                "ဆက်လက်အသုံးပြုရန်အတွက် Admin ထံ ဆက်သွယ်၍ Credits ဝယ်ယူနိုင်ပါသည်။",
                reply_markup=reply_markup
            )
            return

    status_message = await update.message.reply_text("🎬 ဗီဒီယို Absolute Ultimate Scramble လုပ်နေပါပြီဆရာ (ခဏစောင့်ပေးပါ)...")
    video = update.message.video
    file = await context.bot.get_file(video.file_id)
    
    unique_id = hashlib.md5(str(update.effective_user.id).encode()).hexdigest()[:8]
    input_path = f"input_{unique_id}.mp4"
    output_path = f"output_{unique_id}.mp4"
    
    try:
        await file.download_to_drive(input_path)
        
        speed_factor = random.choice([0.97, 0.98, 1.02, 1.03])
        video_pts = f"setpts={1.0/speed_factor}*PTS"
        audio_tempo = f"atempo={speed_factor}"
        
        frames = []
        for frame in iio.imiter(input_path):
            noise = np.random.normal(0, 5.5, frame.shape).astype(np.float32)
            processed_frame = np.clip(frame.astype(np.float32) + noise, 0, 255).astype(np.uint8)
            frames.append(processed_frame)
        
        if frames:
            iio.imwrite(
                output_path, 
                frames, 
                fps=25.0, 
                plugin="pyav", 
                quality=8,
                output_params=[
                    "-vf", video_pts,
                    "-af", audio_tempo
                ]
            )
        
        with open(output_path, 'rb') as f:
            vid_bytes = f.read()
        vid_hash = hashlib.sha256(vid_bytes).digest()
        
        with open(output_path, 'wb') as f:
            f.write(vid_bytes + vid_hash[:64])
            
        if user_id != ADMIN_ID:
            new_credits = user_data["credits"] - COST_PER_VIDEO
            update_user_data(user_id, new_credits)
            caption_text = f"✅ ဗီဒီယို Ultimate Scramble ပြီးပါပြီဆရာ။ (-{COST_PER_VIDEO} Credits | လက်ကျန်: {new_credits} Credits)"
        else:
            caption_text = "✅ ဗီဒီယိုဖိုင် Ultimate Scramble ပြီးပါပြီဆရာ (Admin)."

        with open(output_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=caption_text
            )
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
        
    except Exception as e:
        logger.error(f"Video Scramble Error: {e}")
        await update.message.reply_text("❌ ဗီဒီယိုပြုပြင်ရာတွင် အမှားအယွင်း ရှိသွားပါပြီဆရာ။")
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

# ==========================================
# Main Application Runner
# ==========================================
def main():
    if not TOKEN:
        logger.error("No Telegram Token provided!")
        return

    application = Application.builder().token(TOKEN).build()
    
    application.add_handlers([
        CommandHandler("start", start),
        CommandHandler("balance", balance_command),
        CommandHandler("add", add_credit_command),
        MessageHandler(filters.PHOTO, handle_image),
        MessageHandler(filters.VIDEO, handle_video)
    ])

    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(start_web_server())
    
    logger.info("Bot is up and running 24/7 with Absolute Ultimate Scrambling Engine...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
