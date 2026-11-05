import os
import logging
import hashlib
import io
import asyncio
from aiohttp import web
import numpy as np
from PIL import Image
import imageio.v3 as iio
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, CommandHandler, filters

logging.basicConfig(
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
level=logging.INFO
)
logger = logging.getLogger(name)

TOKEN = os.getenv("TOKEN")
PORT = int(os.environ.get("PORT", "10000"))

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
"ပုံ သို့မဟုတ် ဗီဒီယို ပို့ပေးပါ, Pixel Micro-noise နှင့် SHA-256 Scrambling ပြုလုပ်ပေးပါမည်။"
)
await update.message.reply_text(welcome_text)

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

await update.message.reply_photo(
photo=bytes(final_image_bytes),
caption="✅ ပုံဖိုင်ကို Scramble ပြီးပါပြီဆရာ။"
)
await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
except Exception as e:
logger.error(f"Image Error: {e}")
await update.message.reply_text("❌ ပုံပြုပြင်ရာတွင် အမှားအယွင်း ရှိသွားပါပြီဆရာ။")

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

with open(output_path, 'rb') as video_file:
await update.message.reply_video(
video=video_file,
caption="✅ ဗီဒီယိုဖိုင်ကို Scramble ပြီးပါပြီဆရာ။"
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
application.add_handler(MessageHandler(filters.PHOTO, handle_image))
application.add_handler(MessageHandler(filters.VIDEO, handle_video))

loop = asyncio.get_event_loop()
loop.run_until_complete(start_web_server())

logger.info("Bot is up and running 24/7...")
application.run_polling(allowed_updates=Update.ALL_TYPES)

if name == "main":
main()
