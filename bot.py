import telebot
from PIL import Image
import numpy as np
import hashlib
import io
import os

TOKEN = '9185104477:AAE4v8Vbc0slkAE7AD9lZDscaPWAR-9R9QI'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "မင်္ဂလာပါဆရာ! စလော့ပုံတစ်ပုံ ပိုပေးပါ။ AI ဖြင့် Hash ပြောင်းပေးပြီးသားပုံကို ပြန်ပိုပေးပါမည်။")

@bot.message_handler(content_types=['photo'])
def handle_image(message):
    try:
        fileID = message.photo[-1].file_id
        file_info = bot.get_file(fileID)
        downloaded_file = bot.download_file(file_info.file_path)
        
        orig_hash = hashlib.md5(downloaded_file).hexdigest()
        
        image_stream = io.BytesIO(downloaded_file)
        img = Image.open(image_stream)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        img_array = np.array(img, dtype=np.float32)
        noise = np.random.normal(loc=0.0, scale=1.5, size=img_array.shape)
        noisy_img_array = np.clip(img_array + noise, 0, 255).astype(np.uint8)
        
        processed_img = Image.fromarray(noisy_img_array)
        r, g, b = processed_img.split()
        r = r.point(lambda i: i * 1.002)
        b = b.point(lambda i: i * 0.998)
        final_img = Image.merge("RGB", (r, g, b))
        
        buf = io.BytesIO()
        final_img.save(buf, format="JPEG", quality=91, optimize=True, subsampling=0)
        byte_im = buf.getvalue()
        
        mod_hash = hashlib.md5(byte_im).hexdigest()
        
        caption_text = f"✅ အောင်မြင်ပါပြီ ဆရာ!\n\n🔹 မူရင်း Hash: {orig_hash[:12]}...\n🔸 အသစ် Hash: {mod_hash[:12]}..."
        bot.send_photo(message.chat.id, byte_im, caption=caption_text)
        
    except Exception as e:
        bot.reply_to(message, f"အမှားအယွင်း ရှိနေပါသည်: {e}")

print("🤖 Telegram Bot စတင် အလုပ်လုပ်နေပါပြီ...")
bot.infinity_polling()