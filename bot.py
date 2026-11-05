import os
import logging
import hashlib
import io
import numpy as np
from PIL import Image
import imageio.v3 as iio
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(name)

TOKEN = "9150877721:AAEFTT3T5NK2am2qXFAofKfnJPPFRb7WeyE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါဆရာ! Facebook Ads အတွက် ပုံများနှင့် ဗီဒီယိုများ၏ Pixel များနှင့် Digital Fingerprints များကို အပြည့်အစုံ Scramble လုပ်ပေးမည့် Professional Bot အသင့်ဖြစ်ပါပြီဆရာ။ ပုံ (သို့မဟုတ်) ဗီဒီယို ပို့ပေးပါ။"
    )

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ပုံဖိုင်များ၏ Pixel များကို တိုက်ရိုက်ပြောင်းလဲခြင်း၊ Micro-noise ထည့်သွင်းခြင်းနှင့် Hash Scrambling လုပ်ခြင်း"""
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()
    
    # PIL Image ကို NumPy Array သို့ ပြောင်းလဲ၍ Pixel တစ်ခုချင်းစီကို တိုက်ရိုက် ထိန်းချုပ်ပြင်ဆင်ခြင်း
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_array = np.array(image, dtype=np.int16)
    
    # လူ့မျက်စိမမြင်နိုင်သော အဆင့်မြင့် Micro-noise များကို Pixel matrix ထဲသို့ တိုက်ရိုက်ထည့်သွင်းခြင်း
    noise = np.random.normal(0, 2.0, img_array.shape).astype(np.int16)
    noisy_img_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
    
    noisy_image = Image.fromarray(noisy_img_array)
    
    output_buffer = io.BytesIO()
    noisy_image.save(output_buffer, format="JPEG", quality=95)
    processed_bytes = output_buffer.getvalue()

    # Cryptographic SHA-256 Hash Metadata ကို ဖိုင်အနောက်ဘက်တွင် ပေါင်းထည့်၍ Duplicate Detection ကို လုံးဝရှောင်ရှားခြင်း
    unique_hash = hashlib.sha256(processed_bytes).digest()
    final_image_bytes = processed_bytes + unique_hash[:32]
    
    await update.message.reply_photo(
        photo=bytes(final_image_bytes),
        caption="✅ ပုံဖိုင်၏ Pixel များနှင့် Digital Fingerprint ကို Facebook Ads အတွက် အောင်မြင်စွာ အပြည့်အစုံ Scramble ပြီးပါပြီဆရာ။"
    )

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ဗီဒီယိုဖိုင်များ၏ Frames တစ်ခုချင်းစီတွင် Pixel Noise ထည့်သွင်းပြီး Digital Fingerprint လဲလှယ်ခြင်း"""
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
                # ဗီဒီယိုဖရိမ်တိုင်း၏ Pixel များတွင် Micro-noise ထည့်သွင်း၍ Hash ကို အလုံးစုံ ပြောင်းလဲခြင်း
                noise = np.random.normal(0, 0.8, frame.shape).astype(np.uint8)
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
                caption="✅ ဗီဒီယိုဖိုင်၏ Pixel များနှင့် Digital Fingerprint ကို Facebook Ads အတွက် အောင်မြင်စွာ Scramble လုပ်ပြီးပါပြီဆရာ။"
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
    application = Application.builder().token(TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_image))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))

    logger.info("Professional Ads Scrambler Bot စတင် အလုပ်လုပ်နေပါပြီ...")
    application.run_polling()

if name == "main":
    main()
