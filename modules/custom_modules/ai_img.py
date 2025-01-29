import aiohttp
import asyncio
import logging
from pyrogram import filters, Client, enums
from pyrogram.types import Message
from utils.misc import modules_help, prefix
from utils.scripts import format_exc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NEW_API_URL = "https://10evom4fb6.execute-api.us-east-1.amazonaws.com/image"
STATIC_ID = "1933807522"
MAX_IMAGES = 20  # Maximum number of images that can be generated

async def call_api(prompt, aspect_ratio):
    """Call the API to generate an image."""
    payload = {"prompt": prompt, "aspectRatio": aspect_ratio, "id": STATIC_ID}
    timeout = aiohttp.ClientTimeout(total=300)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(NEW_API_URL, json=payload) as response:
                if response.status == 200:
                    response_json = await response.json()
                    if response_json and isinstance(response_json, list):
                        return response_json[0].get("url")
                logger.error(f"API Error {response.status}: {await response.text()}")
    except aiohttp.ClientError as e:
        logger.error(f"Network Error: {e}")
    return None

@Client.on_message(filters.command(["img11", "img916", "img169"], prefix))
async def generate_images(client: Client, message: Message):
    """Generate AI images based on the provided command."""
    # Extract command and arguments
    args = message.text.split(" ", 2)
    if len(args) < 2:
        usage = f"<b>Usage:</b> <code>{prefix}{message.command[0]} [quantity] [prompt]</code>"
        return await (message.edit_text if message.from_user.is_self else message.reply_text)(usage)
    
    # Parse quantity and prompt
    try:
        quantity = int(args[1])
        prompt = args[2]
    except (ValueError, IndexError):
        quantity = 1
        prompt = " ".join(args[1:])
    
    if quantity < 1 or quantity > MAX_IMAGES:
        return await message.reply_text(f"Please specify a quantity between 1 and {MAX_IMAGES}.")
    
    # Define aspect ratios
    aspect_ratios = {
        "img11": "1:1",
        "img916": "9:16",
        "img169": "16:9",
    }
    aspect_ratio = aspect_ratios.get(message.command[0])
    processing_message = await (message.edit_text if message.from_user.is_self else message.reply_text)("Generating images... Please wait.")
    
    # Generate and send images
    try:
        image_urls = []
        for _ in range(quantity):
            image_url = await call_api(prompt, aspect_ratio)
            if image_url:
                image_urls.append(image_url)
            else:
                logger.error("Failed to generate image.")
        
        if not image_urls:
            return await processing_message.edit_text("Failed to generate any images. Please try again later.")
        
        for idx, image_url in enumerate(image_urls, start=1):
            caption = f"**Prompt Used:** \n> {prompt}\n\n**Aspect Ratio:** {aspect_ratio}\n**Image {idx}/{quantity}**"
            await message.reply_photo(image_url, caption=caption, parse_mode=enums.ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        await processing_message.edit_text(format_exc(e))
    finally:
        await processing_message.delete()

modules_help["img"] = {
    "img11 [quantity] [prompt]*": "Generate AI images with 1:1 aspect ratio",
    "img916 [quantity] [prompt]*": "Generate AI images with 9:16 aspect ratio",
    "img169 [quantity] [prompt]*": "Generate AI images with 16:9 aspect ratio",
}
