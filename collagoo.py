import io
from PIL import Image
import bale

BOT_TOKEN = "paste_your_token_here"   # put your bot token here

bot = bale.Bot(BOT_TOKEN)

# store user photos temporarily
user_photos = {}


def make_collage(images, width=500, margin=10):
    """
    Create a vertical collage with white lines (margin) between and around photos.
    :param images: list of image bytes
    :param width: width of each photo
    :param margin: white space between and around photos
    """
    # open all images
    imgs = [Image.open(io.BytesIO(img)) for img in images]

    # resize all to the same width
    imgs = [im.resize((width, int(im.height * width / im.width))) for im in imgs]

    # total height including margins
    total_height = sum(im.height for im in imgs) + margin * (len(imgs) + 1)

    # create collage with white background
    collage = Image.new("RGB", (width + 2 * margin, total_height), (255, 255, 255))

    y_offset = margin
    for im in imgs:
        collage.paste(im, (margin, y_offset))
        y_offset += im.height + margin  # add margin below each photo

    return collage



@bot.event
async def on_message(message: bale.Message):
    chat_id = message.chat.id

    if message.photos:
        # get highest resolution photo
        file_id = message.photos[-1].file_id
        file_data = await bot.get_file(file_id)

        if chat_id not in user_photos:
            user_photos[chat_id] = []

        user_photos[chat_id].append(file_data)

        if len(user_photos[chat_id]) < 3:
            await bot.send_text(chat_id, f"Photo {len(user_photos[chat_id])}/3 received ✅")
        else:
            # create vertical collage
            collage = make_collage(user_photos[chat_id])

            img_bytes = io.BytesIO()
            collage.save(img_bytes, format="JPEG")
            img_bytes.seek(0)

            await bot.send_photo(
                chat_id,
                bale.InputFile(img_bytes.read()),  # send as bytes
                caption="Here is your vertical collage 🎨"
            )

            # reset user storage
            user_photos[chat_id] = []

    elif message.text and message.text.lower() == "/reset":
        user_photos[chat_id] = []
        await bot.send_text(chat_id, "Reset done. Send 3 photos again.")
    elif message.text:
        await bot.send_text(chat_id, "Please send me 3 photos, one by one.")


if __name__ == "__main__":
    bot.run()
