import os
import logging
import hashlib
import io
import asyncio
import random
import sqlite3
from aiohttp import web
import numpy as np
from PIL import Image, ImageDraw
import imageio.v3 as iio

import torch
import torch.nn as nn
from torchvision import models, transforms

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, MessageHandler, CommandHandler, filters

# Logging Setup
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
COST_PER_IMAGE = 1   # ပုံ ၁ ပုံလျှင် 1 Credit
COST_PER_VIDEO = 2   # ဗီဒီယို ၁ ခုလျှင် 2 Credits

# ==========================================
# PyTorch Deep Learning Model Setup (PGD Adversarial Engine)
# ==========================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info(f"Loading PyTorch Model on device: {device}...")

# Load pre-trained ResNet50 as target network for adversarial perturbation
adversarial_model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT).to(device)
adversarial_model.eval()

preprocess_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

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
    return web.Response(text="PyTorch Adversarial Scrambler Bot is running 24/7!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Enterprise Web server started on port {PORT}")

# ==========================================
# Telegram Commands
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_url = f"https://t.me/{ADMIN_USERNAME}"
    welcome_text = (
        "🙏မင်္ဂလာပါဆရာ! 🚀\n\n"
        "✨PSN image cleaner win Bot အသင့်ဖြစ်ပါပြီဆရာ။\n\n"
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
        await update.message.reply_text("❌ ဒီ Command ကို အသုံးပြုခွင့် မရှိပါဘူးဆရာ။ရှင်။")
        return
        
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("❌ ဥပမာ - /add [User_ID] [Credits]")
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
        except Exception:
            pass

        await update.message.reply_text(f"✅ User ID: {target_user_id} သို့ Credits {amount} ထည့်သွင်းပြီးပါပြီ။ (စုစုပေါင်း: {new_balance})")
    except Exception as e:
        logger.error(f"Add Credit Error: {e}")
        await update.message.reply_text("❌ အမှားအယွင်း ရှိနေပါသည်ဆရာ။")

# ==========================================
# Enterprise PGD Adversarial Image Handler
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
                f"❌ လက်ကျန် Credits မလုံလောက်တော့ပါ။ (လိုအပ်သည်: {COST_PER_IMAGE} Credit | လက်ကျန်: {user_data['credits']} Credits)",
                reply_markup=reply_markup
            )
            return

    status_message = await update.message.reply_text("🧠 PyTorch PGD Adversarial AI Engine ဖြင့် ပုံကို အဆင့်မြင့်ဆုံး Scramble လုပ်နေပါပြီဆရာ...")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        
        # Load image via PIL
        original_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = original_image.size
        
        # --- PyTorch PGD Adversarial Perturbation Execution ---
        img_resized = original_image.resize((224, 224), Image.Resampling.LANCZOS)
        input_tensor = preprocess_transform(img_resized).unsqueeze(0).to(device)
        input_tensor.requires_grad = True
        
        criterion = nn.CrossEntropyLoss()
        with torch.no_grad():
            output = adversarial_model(input_tensor)
            original_class = output.argmax(dim=1)

        epsilon = 0.08
        alpha = 0.01
        num_iter = 10
        perturbed_tensor = input_tensor.clone().detach()
        
        for _ in range(num_iter):
            perturbed_tensor.requires_grad = True
            outputs = adversarial_model(perturbed_tensor)
            loss = criterion(outputs, original_class)
            
            adversarial_model.zero_grad()
            loss.backward()
            
            with torch.no_grad():
                gradient = perturbed_tensor.grad.data
                perturbed_tensor = perturbed_tensor + alpha * gradient.sign()
                eta = torch.clamp(perturbed_tensor - input_tensor, min=-epsilon, max=epsilon)
                perturbed_tensor = torch.clamp(input_tensor + eta, min=0, max=1).detach()

        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1).to(device)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1).to(device)
        denorm_tensor = perturbed_tensor.squeeze(0) * std + mean
        denorm_tensor = torch.clamp(denorm_tensor, 0, 1)
        
        to_pil = transforms.ToPILImage()
        adversarial_pil = to_pil(denorm_tensor.cpu())
        final_image = adversarial_pil.resize((w, h), Image.Resampling.LANCZOS)
        
        # Additional Patch Masking & EXIF Eradication
        draw = ImageDraw.Draw(final_image, "RGBA")
        for _ in range(random.randint(6, 12)):
            rx1 = random.randint(0, max(1, w - 20))
            ry1 = random.randint(0, max(1, h - 20))
            rx2 = rx1 + random.randint(10, min(25, w - rx1))
            ry2 = ry1 + random.randint(10, min(25, h - ry1))
            patch_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(5, 12))
            draw.rectangle([rx1, ry1, rx2, ry2], fill=patch_color)

        output_buffer = io.BytesIO()
        final_image.save(output_buffer, format="JPEG", quality=random.randint(85, 92), subsampling=0)
        processed_bytes = output_buffer.getvalue()

        # Cryptographic Salt Tail
        unique_hash = hashlib.sha256(processed_bytes).digest()
        final_image_bytes = processed_bytes + unique_hash[:64]
        
        if user_id != ADMIN_ID:
            new_credits = user_data["credits"] - COST_PER_IMAGE
            update_user_data(user_id, new_credits)
            caption_text = f"🛡️ PyTorch PGD Adversarial Scramble အောင်မြင်ပါပြီဆရာ။ (-{COST_PER_IMAGE} Credit | လက်ကျန်: {new_credits} Credits)"
        else:
            caption_text = "🛡️ PyTorch PGD Adversarial Scramble ပြီးပါပြီဆရာ (Admin)."

        await update.message.reply_photo(
            photo=bytes(final_image_bytes),
            caption=caption_text
        )
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
        
    except Exception as e:
        logger.error(f"PyTorch Image Scramble Error: {e}")
        await update.message.reply_text("❌ ပုံပြုပြင်ရာတွင် အမှားအယွင်း ရှိသွားပါပြီဆရာ။")

# ==========================================
# Video Scrambler Handler
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
                f"❌ ဗီဒီယိုဖိုင်အတွက် Credits မလုံလောက်ပါဆရာ။ (လိုအပ်သည်: {COST_PER_VIDEO} Credits | လက်ကျန်: {user_data['credits']} Credits)",
                reply_markup=reply_markup
            )
            return

    status_message = await update.message.reply_text("🎬 ဗီဒီယို Neural Frame Scramble လုပ်နေပါပြီဆရာ (ခဏစောင့်ပေးပါ)...")
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
            noise = np.random.normal(0, 5.0, frame.shape).astype(np.float32)
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
            caption_text = f"✅ ဗီဒီယို Scramble ပြီးပါပြီဆရာ။ (-{COST_PER_VIDEO} Credits | လက်ကျန်: {new_credits} Credits)"
        else:
            caption_text = "✅ ဗီဒီယိုဖိုင် Scramble ပြီးပါပြီဆရာ (Admin)."

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
    
    logger.info("Bot is up and running with PyTorch PGD Adversarial Engine...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
