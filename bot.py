import os
import logging
import hashlib
import io
import asyncio
from aiohttp import web
import numpy as np
from PIL import Image
import imageio.v3 as iio
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

# ==========================================
# Credit System & Pricing Configuration
# ==========================================
user_credits = {}
free_used_users = set()

# ဆရာ့ရဲ့ Telegram Admin အချက်အလက်များ
ADMIN_ID = 1759541320  
ADMIN_USERNAME = "osker0296"  

COST_PER_IMAGE = 4   
COST_PER_VIDEO = 12  

async def handle_ping(request):
        return web.Response(text="Bot is running and active!")

async def start_web_server():
        app = web.Application()
        app.router.add_get("/", handle_ping)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()
        logger.info(f"Production Web server started on port {PORT}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "မင်္ဂလာပါဆရာ! 🚀\n\n"
        "Facebook Ads Media Scrambler Bot အသင့်ဖြစ်ပါပြီဆရာ။\n"
        "📌 ပုံ ၁ ပုံကို အခမဲ့ (Free) စမ်းသပ်ထုတ်လုပ်နိုင်ပါသည်။\n"
        "ဆက်လက်အသုံးပြုလိုပါက Credits ဝယ်ယူရမည် ဖြစ်ပါသည်။ ပုံ ၁ ပုံလျှင် ၄ Credits (၂၀,၀၀၀ ကျပ်) နှင့် ဗီဒီယို ၁ ခုလျှင် ၁၂ Credits (၄၀,၀၀၀ ကျပ်) ကျသင့်ပါမည်ဆရာ。"
    )
    await update.message.reply_text(welcome_text)

# ==========================================
# Admin Command: ခွဲတမ်းတိုးပေးရန်
# ==========================================
async def add_credit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ ဒီ Command ကို အသုံးပြုခွင့် မရှိပါဘူးဆရာ။")
        return
        
    try:
        args = context.args
        if len(args) < 2:
            await update.message.reply_text("❌ ဥပမာ - /add [User_ID] [Credits] လို့ ရိုက်ပါဆရာ။ (ဥပမာ: /add 1759541320 12)")
            return
        
        target_user_id = int(args[0])
        amount = int(args[1])
        
        current = user_credits.get(target_user_id, 0)
        user_credits[target_user_id] = current + amount
        
        await update.message.reply_text(f"✅ User ID: {target_user_id} ကို Credits {amount} ထည့်သွင်းပေးလိုက်ပါပြီဆရာ။")
    except Exception as e:
        logger.error(f"Add Credit Error: {e}")
        await update.message.reply_text("❌ အမှားအယွင်း ရှိနေပါသည်ဆရာ။")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        current_balance = user_credits.get(user_id, 0)
        if user_id in free_used_users and current_balance < COST_PER_IMAGE:
            admin_url = f"https://t.me/{ADMIN_USERNAME}"
            keyboard = [[InlineKeyboardButton("💬 Admin ဆီသို့ ဆက်သွယ်ရန် (Credits ဝယ်ရန်)", url=admin_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "❌ ဆရာ့ရဲ့ အခမဲ့ခွဲတမ်း ကုန်ဆုံးသွားပြီ ဖြစ်ပြီး လက်ကျန် Credits မလုံလောက်တော့ပါဆရာ။\n"
                "ပုံ ၁ ပုံလျှင် ၄ Credits (၂၀,၀၀၀ ကျပ်) ဖြင့် ဆက်လက်ဝယ်ယူသုံးစွဲနိုင်ပါသည်။",
                reply_markup=reply_markup
            )
            return

    status_message = await update.message.reply_text("🔄 ပုံဖိုင်ကို Scramble လုပ်နေပါပြီဆရာ...")
    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_array = np.array(image, dtype=np.int16)
        
        noise = np.random.normal(0, 1.5, img_array.shape).astype(np.int16)
        noisy_img_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
        
        noisy_image = Image.fromarray(noisy_img_array)
        output_buffer = io.BytesIO()
        noisy_image.save(output_buffer, format="JPEG", quality=98, subsampling=0)
        processed_bytes = output_buffer.getvalue()

        unique_hash = hashlib.sha256(processed_bytes).digest()
        final_image_bytes = processed_bytes + unique_hash[:32]
        
        if user_id != ADMIN_ID:
            if user_id not in free_used_users:
                free_used_users.add(user_id)
                caption_text = "✅ အခမဲ့ ပုံ Scramble ပြီးပါပြီဆရာ။ (နောင်အကြိမ်များတွင် Credits ဝယ်ယူရမည်ဖြစ်ပါသည်)"
            else:
                user_credits[user_id] = current_balance - COST_PER_IMAGE
                remaining = user_credits[user_id]
                caption_text = f"✅ ပုံ Scramble ပြီးပါပြီဆရာ။ (-{COST_PER_IMAGE} Credits | လက်ကျန်: {remaining} Credits)"
        else:
            caption_text = "✅ ပုံဖိုင်ကို Scramble ပြီးပါပြီဆရာ (Admin)."

        await update.message.reply_photo(
            photo=bytes(final_image_bytes),
            caption=caption_text
        )
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
    except Exception as e:
        logger.error(f"Image Error: {e}")
        await update.message.reply_text("❌ ပုံပြုပြင်ရာတွင် အမှားအယွင်း ရှိသွားပါပြီဆရာ။")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        current_balance = user_credits.get(user_id, 0)
        if current_balance < COST_PER_VIDEO:
            admin_url = f"https://t.me/{ADMIN_USERNAME}"
            keyboard = [[InlineKeyboardButton("💬 Admin ဆီသို့ ဆက်သွယ်ရန် (ဗီဒီယိုအတွက် Credits ဝယ်ရန်)", url=admin_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"❌ ဗီဒီယိုဖိုင် ထုတ်လုပ်ရန်အတွက် Credits မလုံလောက်ပါဆရာ။\n"
                f"ဗီဒီယို ၁ ခုလျှင် {COST_PER_VIDEO} Credits (၄၀,၀၀၀ ကျပ်) လိုအပ်ပါသည်။ Admin ထံသို့ ဆက်သွယ်ဝယ်ယူနိုင်ပါသည်။",
                reply_markup=reply_markup
            )
            return

    status_message = await update.message.reply_text("🎬 ဗီဒီယိုဖိုင်ကို Scramble လုပ်နေပါပြီဆရာ (ခဏစောင့်ပေးပါ)...")
    video = update.message.video
    file = await context.bot.get_file(video.file_id)
    
    unique_id = hashlib.md5(str(update.effective_user.id).encode()).hexdigest()[:8]
    input_path = f"input_{unique_id}.mp4"
    output_path = f"output_{unique_id}.mp4"
    
    try:
        await file.download_to_drive(input_path)
        
        frames = []
        for frame in iio.imiter(input_path):
            noise = np.random.normal(0, 0.5, frame.shape).astype(np.uint8)
            processed_frame = np.clip(frame.astype(np.int16) + noise // 2, 0, 255).astype(np.uint8)
            frames.append(processed_frame)
        
        if frames:
            iio.imwrite(output_path, frames, fps=25.0, plugin="pyav", quality=8)
        
        with open(output_path, 'rb') as f:
            vid_bytes = f.read()
        vid_hash = hashlib.sha256(vid_bytes).digest()
        
        with open(output_path, 'wb') as f:
            f.write(vid_bytes + vid_hash)
            
        if user_id != ADMIN_ID:
            user_credits[user_id] = current_balance - COST_PER_VIDEO
            remaining = user_credits[user_id]
            caption_text = f"✅ ဗီဒီယို Scramble ပြီးပါပြီဆရာ။ (-{COST_PER_VIDEO} Credits | လက်ကျန်: {remaining} Credits)"
        else:
            caption_text = "✅ ဗီဒီယိုဖိုင်ကို Scramble ပြီးပါပြီဆရာ (Admin)."

        with open(output_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption=caption_text
            )
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
    except Exception as e:
        logger.error(f"Video Error: {e}")
        await update.message.reply_text("❌ ဗီဒီယိုပြုပြင်ရာတွင် အမှားအယွင်း ရှိသွားပါပြီဆရာ။")
    finally:
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

def main():
    if not TOKEN:
        logger.error("No Telegram Token provided!")
        return

    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_credit_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))

    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(start_web_server())
    
    logger.info("Bot is up and running 24/7...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
