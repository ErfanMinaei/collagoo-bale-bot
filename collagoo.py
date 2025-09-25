import os
import io
import logging
from PIL import Image
import bale

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("BOT_TOKEN environment variable not set. Set it and restart.")
    raise SystemExit("Set BOT_TOKEN environment variable")

bot = bale.Bot(BOT_TOKEN)
user_photos = {}  # chat_id -> list of bytes


def make_collage(images, width=700, margin=12):
    """Vertical collage: images stacked top->bottom with white margin around and between."""
    imgs = []
    for b in images:
        try:
            im = Image.open(io.BytesIO(b)).convert("RGB")
        except Exception as e:
            logging.exception("Invalid image")
            continue
        # resize preserving aspect ratio
        w = width
        im = im.resize((w, int(im.height * w / im.width)))
        imgs.append(im)

    if not imgs:
        raise ValueError("No valid images to build collage")

    total_height = sum(im.height for im in imgs) + margin * (len(imgs) + 1)
    collage = Image.new("RGB", (width + 2 * margin, total_height), (255, 255, 255))

    y = margin
    for im in imgs:
        collage.paste(im, (margin, y))
        y += im.height + margin

    return collage


@bot.event
async def on_message(message: bale.Message):
    try:
        chat_id = message.chat.id
    except Exception:
        return

    # Photos (use message.photos)
    if getattr(message, "photos", None):
        file_id = message.photos[-1].file_id  # highest quality
        try:
            file_data = await bot.get_file(file_id)  # returns bytes
        except Exception:
            await bot.send_message(chat_id, "⚠️ Failed to download the photo.")
            return

        user_photos.setdefault(chat_id, []).append(file_data)
        count = len(user_photos[chat_id])

        if count < 3:
            await bot.send_message(chat_id, f"Photo {count}/3 received ✅")
            return

        # Have 3 photos -> create collage
        try:
            collage = make_collage(user_photos[chat_id], width=700, margin=16)
            img_bytes = io.BytesIO()
            collage.save(img_bytes, format="JPEG", quality=85)
            img_bytes.seek(0)

            await bot.send_photo(chat_id, bale.InputFile(img_bytes.read()), caption="Here is your collage 🎨")
        except Exception:
            logging.exception("Failed to create/send collage")
            await bot.send_message(chat_id, "Sorry — failed to create the collage.")
        finally:
            user_photos[chat_id] = []
        return

    # Text handling
    if getattr(message, "text", None):
        text = message.text.strip()
        if text.lower() == "/reset":
            user_photos[chat_id] = []
            await bot.send_message(chat_id, "Reset done. Send 3 photos again.")
        else:
            await bot.send_message(chat_id, "Send 3 photos (one by one) and I'll return a vertical collage with white borders.")
