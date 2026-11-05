import os
import logging
import hashlib
import cv2
import numpy as np
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Logging စနစ်ကို ချိတ်ဆက်ခြင်း
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(_ _name_ _)

# Telegram Bot Token ကို ဤနေရာတွင် တိုက်ရိုက်ထည့်သွင်းပါ
TOKEN = "9150877721:AAEFTT3T5NK2am2qXFAofKfnJPPFRb7WeyE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ဘော့တ်စတင်သည့်အခါ ကြိုဆိုသော မက်ဆေ့ချ် ပို့ပေးခြင်း"""
    await update.message.reply_text(
        "မင်္ဂလာပါဆရာ! ကျေးဇူးပြု၍ ပုံ (သို့မဟုတ်) ဗီဒီယို ပို့ပေးပါ။ AI ဖြင့် Hash နှင့် Metadata များကို အဆင့်မြင့်နည်းလမ်းဖြင့် ပြောင်းလဲပေးပါမည်။"
    )

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ပုံဖိုင်များကို လက်ခံရယူပြီး Hash ပြောင်းလဲခြင်း"""
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()
    
    # ပုံ၏ ဒစ်ဂျစ်တယ် လက်ရာအမှတ်အသားကို ပြောင်းလဲခြင်း
    sha256_hash = hashlib.sha256(image_bytes).hexdigest()
    modified_image_bytes = image_bytes + sha256_hash[:16].encode('utf-8')
    
    await update.message.reply_photo(
        photo=bytes(modified_image_bytes),
        caption="✅ ပုံဖိုင်အတွက် AI Hash နှင့် Metadata များကို အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီဆရာ။"
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ဗီဒီယိုဖိုင်များကို လက်ခံရယူပြီး အဆင့်မြင့်နည်းလမ်းဖြင့် ပြုပြင်ခြင်း"""
    video = update.message.video
    file = await context.bot.get_file(video.file_id)
    
    input_path = "temp_input.mp4"
    output_path = "temp_output.mp4"
    
    try:
        # ဗီဒီယိုဖိုင်ကို ယာယီဒေါင်းလုဒ်လုပ်ခြင်း
        await file.download_to_drive(input_path)
        
        # OpenCV ဖြင့် ဗီဒီယိုကို ဖတ်ရှုခြင်း
        cap = cv2.VideoCapture(input_path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            # ဗီဒီယိုဖရိန်တစ်ခုချင်းစီကို AI Detection မမိစေရန် အနည်းငယ် ပြုပြင်ခြင်း (Noise Injection)
            noise = np.random.normal(0, 1, frame.shape).astype(np.uint8)
            modified_frame = cv2.add(frame, noise // 30)
            out.write(modified_frame)
            
        cap.release()
        out.release()
        
        # ပြုပြင်ပြီးသား ဗီဒီယိုကို ပြန်လည်ပေးပို့ခြင်း
        with open(output_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption="✅ ဗီဒီယိုဖိုင်အတွက် အဆင့်မြင့် AI Hash နှင့် Frames များကို အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီဆရာ။"
            )
            
    except Exception as e:
        logger.error(f"ဗီဒီယိုပြုပြင်ရာတွင် အမှားအယွင်းရှိသည်: {e}")
        await update.message.reply_text("❌ ဗီဒီယိုကို လုပ်ဆောင်ရာတွင် အခက်အခဲရှိသွားပါသည်။ ထပ်မံကြိုးစားပေးပါ။")
        
    finally:
        # ယာယီဖိုင်များကို ဖျက်ဆီးခြင်း
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

def main():
    if not TOKEN or TOKEN == "ဆရာ့ရဲ့_Bot_Token_အသစ်ကို_ဒီမှာထည့်ပါ":
        logger.error("ကျေးဇူးပြု၍ Bot Token ထည့်သွင်းပေးပါ။")
        return

    # Application တည်ဆောက်ခြင်း
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers များ ထည့်သွင်းခြင်း
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))

    logger.info("Bot (Images & Videos) စတင် အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()
[11/5/2026 4:30 PM] osker: if name == 'main':
    main()
