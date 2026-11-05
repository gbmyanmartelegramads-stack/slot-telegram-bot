import os
import logging
import hashlib
import io
import numpy as np
from PIL import Image, ImageEnhance
import imageio.v3 as iio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Logging စနစ်ချိတ်ဆက်ခြင်း
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(name)

# Telegram Bot Token
TOKEN = "9150877721:AAEFTT3T5NK2am2qXFAofKfnJPPFRb7WeyE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါဆရာ! Facebook Ads အတွက် Duplicate နှင့် AI Fingerprint များကို အောင်မြင်စွာ ကျော်လွှားနိုင်မည့် Professional Scrambler Bot အသင့်ရှိပါပြီဆရာ။ ပုံ (သို့မဟုတ်) ဗီဒီယို ပို့ပေးပါ။"
    )

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ပုံဖိုင်များ၏ Pixel များနှင့် Metadata/Hash ကို အဆင့်မြင့် Scramble လုပ်ခြင်း"""
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()
    
    # PIL ဖြင့် ပုံကိုဖတ်ရှုပြီး မျက်စိမမြင်နိုင်သော နုညံ့သည့် Pixel ပြောင်းလဲမှုပြုလုပ်ခြင်း
    image = Image.open(io.BytesIO(image_bytes))
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.015)  # အရောင်အလင်းအမှောင် အလွန်နုညံ့စွာ ချိန်ညှိခြင်း
    
    output_buffer = io.BytesIO()
    image.save(output_buffer, format="JPEG", quality=95)
    processed_bytes = output_buffer.getvalue()

    # Cryptographic SHA-256 Hash Metadata ထည့်သွင်းခြင်း (Duplicate Detection ကျော်လွှားရန်)
    unique_hash = hashlib.sha256(processed_bytes).digest()
    final_image_bytes = processed_bytes + unique_hash[:32]
    
    await update.message.reply_photo(
        photo=bytes(final_image_bytes),
        caption="✅ Facebook Ads ၏ Duplicate Detection နှင့် AI Fingerprint များကို ကျော်လွှားနိုင်ရန် ပုံ၏ Metadata နှင့် Hash ကို အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီဆရာ။"
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ဗီဒီယိုဖိုင်များ၏ Frames များနှင့် Digital Fingerprint ကို Scramble လုပ်ခြင်း"""
    video = update.message.video
    file = await context.bot.get_file(video.file_id)
    
    input_path = "temp_input.mp4"
    output_path = "temp_output.mp4"
    
    try:
        await file.download_to_drive(input_path)
        
        frames = []
        fps = 25.0
        try:
            for frame in iio.imiter(input_path):
                # ဖရိမ်တိုင်းတွင် Micro-noise ထည့်သွင်း၍ ဗီဒီယို Hash ကို အလုံးစုံ ပြောင်းလဲခြင်း
                noise = np.random.normal(0, 0.4, frame.shape).astype(np.uint8)
                modified_frame = np.clip(frame.astype(np.int16) + noise // 2, 0, 255).astype(np.uint8)
                frames.append(modified_frame)
        except Exception as e:
            logger.warning(f"Frame iteration warning: {e}")

        if frames:
            iio.imwrite(output_path, frames, fps=fps)
        else:
            with open(input_path, 'rb') as f:
                vid_bytes = f.read()
            with open(output_path, 'wb') as f:
                f.write(vid_bytes + hashlib.sha256(vid_bytes).digest())

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
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))

    logger.info("Professional Ads Scrambler Bot စတင် အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()

main()
