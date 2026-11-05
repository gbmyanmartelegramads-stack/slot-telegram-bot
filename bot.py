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
logger = logging.getLogger("name")

# Telegram Bot Token ကို ဤနေရာတွင် တိုက်ရိုက်ထည့်သွင်းပါ
TOKEN = "9150877721:AAEFTT3T5NK2am2qXFAofKfnJPPFRb7WeyE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ဘော့တ်စတင်သည့်အခါ ကြိုဆိုသော မက်ဆေ့ချ် ပို့ပေးခြင်း"""
    await update.message.reply_text(
        "မင်္ဂလာပါဆရာ! Facebook Ads အတွက် AI Fingerprint နှင့် Metadata များကို အဆင့်မြင့်ဆုံး ပြောင်းလဲပေးမည့် Professional Bot အသင့်ဖြစ်ပါပြီဆရာ။ ပုံ (သို့မဟုတ်) ဗီဒီယို ပို့ပေးပါ။"
    )

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ပုံဖိုင်များ၏ Pixel များနှင့် Binary/Metadata များကို အပြည့်အဝ Scramble လုပ်ခြင်း"""
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()
    
    # OpenCV ဖြင့် ပုံကိုဖတ်ရှုပြီး Visual Matrix ကို အနည်းငယ် ပြုပြင်ခြင်း (လူ့မျက်စိ မသိသာစေရန်)
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is not None:
        # Pixel Brightness / Contrast ကို အလွန်နုညံ့စွာ ပြောင်းလဲခြင်းဖြင့် Hash ကို လုံးဝအသစ်ဖြစ်စေခြင်း
        img = cv2.convertScaleAbs(img, alpha=1.03, beta=2)
        _, encoded_img = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        processed_bytes = encoded_img.tobytes()
    else:
        processed_bytes = image_bytes

    # Cryptographic SHA-256 Hash Metadata ထည့်သွင်းခြင်း (Duplicate Detection ကျော်လွှားရန်)
    unique_hash = hashlib.sha256(processed_bytes).digest()
    final_image_bytes = processed_bytes + unique_hash[:32]
    
    await update.message.reply_photo(
        photo=bytes(final_image_bytes),
        caption="✅ Facebook Ads ၏ Duplicate Detection နှင့် AI Fingerprint များကို ကျော်လွှားနိုင်ရန် ပုံ၏ Metadata နှင့် Hash ကို အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီဆရာ။"
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ဗီဒီယိုဖိုင်များ၏ ဖရိမ်တိုင်းကို AI နည်းလမ်းဖြင့် ပြုပြင်ပြီး Digital Fingerprint လဲလှယ်ခြင်း"""
    video = update.message.video
    file = await context.bot.get_file(video.file_id)
    
    input_path = "temp_input.mp4"
    output_path = "temp_output.mp4"
    
    try:
        await file.download_to_drive(input_path)
        
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
            # ဗီဒီယိုဖရိမ်တိုင်းတွင် Micro-noise ထည့်သွင်း၍ ဗီဒီယို Hash ကို အလုံးစုံ ပြောင်းလဲခြင်း
            noise = np.random.normal(0, 0.8, frame.shape).astype(np.uint8)
            modified_frame = cv2.add(frame, noise)
            out.write(modified_frame)
            
        cap.release()
        out.release()
        
        # ထပ်ဆောင်း Binary Hash ကို ဗီဒီယိုဖိုင်အနောက်ဘက်တွင် ပေါင်းထည့်ခြင်း
        with open(output_path, 'rb') as f:
            vid_bytes = f.read()
        vid_hash = hashlib.sha256(vid_bytes).digest()
        
        with open(output_path, 'wb') as f:
            f.write(vid_bytes + vid_hash)
        
        with open(output_path, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                caption="✅ ဗီဒီယိုဖိုင်၏ Frames များနှင့် Digital Fingerprint ကို Facebook Ads အတွက် အောင်မြင်စွာ Scramble လုပ်ပြီးပါပြီဆရာ။"
            )
            
    except Exception as e:
        logger.error(f"ဗီဒီယိုပြုပြင်ရာတွင် အမှားအယွင်းရှိသည်: {e}")
        await update.message.reply_text("❌ ဗီဒီယိုကို လုပ်ဆောင်ရာတွင် အခက်အခဲရှိသွားပါသည်။ ထပ်မံကြိုးစားပေးပါ။")
        
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(output_path):
            os.remove(output_path)

def main():
    # Application တည်ဆောက်ခြင်း
    app = ApplicationBuilder().token(TOKEN).build()

    # Handlers များ ထည့်သွင်းခြင်း
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))

    logger.info("Professional Ads Scrambler Bot စတင် အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()

main()
