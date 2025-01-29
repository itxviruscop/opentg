import os
import time
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix
from utils.scripts import progress

YOUTUBE_SEARCH_API = "https://api.agatz.xyz/api/ytsearch?message="
YOUTUBE_DOWNLOAD_API = "https://api.agatz.xyz/api/ytmp3?url="

@Client.on_message(filters.command(["ymusic", "ytmusic", "ym"], prefix) & filters.me)
async def youtube_music(client: Client, message: Message):
    chat_id = message.chat.id
    
    # Extract query
    query = (
        message.text.split(maxsplit=1)[1].strip()
        if len(message.command) > 1 else
        (message.reply_to_message.text.strip() if message.reply_to_message else None)
    )
    if not query:
        await message.edit(f"<b>Usage:</b> <code>{prefix}ymusic [song name]</code>")
        return

    ms = await message.edit_text(f"<code>Searching for {query} on YouTube Music...</code>")
    
    try:
        search_response = requests.get(f"{YOUTUBE_SEARCH_API}{query}")
        search_response.raise_for_status()
        search_result = search_response.json()
    except Exception as e:
        await ms.edit_text(f"<code>Error while searching: {str(e)}</code>")
        return

    if search_result.get("status") != 200 or not search_result.get("data"):
        await ms.edit_text(f"<code>No results found for {query}</code>")
        return

    song = search_result["data"][0]
    song_name, song_url, song_author, song_thumb = (
        song["title"], song["url"], song["author"]["name"], song["image"]
    )
    await ms.edit_text(f"<b>Found:</b> <code>{song_name}</code>\n<b>Author:</b> <code>{song_author}</code>\n<code>Fetching download link...</code>")

    try:
        download_response = requests.get(f"{YOUTUBE_DOWNLOAD_API}{song_url}")
        download_response.raise_for_status()
        download_result = download_response.json()
    except Exception as e:
        await ms.edit_text(f"<code>Error while fetching download link: {str(e)}</code>")
        return

    if download_result.get("status") != 200 or not download_result.get("data"):
        await ms.edit_text(f"<code>Failed to fetch download link for {song_name}</code>")
        return

    download_link = max(
        download_result["data"], 
        key=lambda x: int(x["quality"].replace("kbps", ""))
    )["downloadUrl"]

    await ms.edit_text(f"<code>Downloading {song_name}...</code>")
    try:
        with open(f"{song_name}.mp3", "wb") as song_file:
            for chunk in requests.get(download_link, stream=True).iter_content(1024):
                song_file.write(chunk)
    except Exception as e:
        await ms.edit_text(f"<code>Error while downloading song: {str(e)}</code>")
        return

    thumb_file = None
    try:
        thumb_file = f"{song_name}.jpg"
        with open(thumb_file, "wb") as thumb_f:
            thumb_f.write(requests.get(song_thumb).content)
    except:
        pass  # Ignore thumbnail errors

    await ms.edit_text(f"<code>Uploading {song_name}...</code>")
    c_time = time.time()
    try:
        await client.send_audio(
            chat_id,
            audio=f"{song_name}.mp3",
            caption=f"<b>Song Name:</b> {song_name}\n<b>Author:</b> {song_author}",
            thumb=thumb_file,
            progress=progress,
            progress_args=(ms, c_time, f"<code>Uploading {song_name}...</code>"),
        )
    except Exception as e:
        await ms.edit_text(f"<code>Error while uploading song: {str(e)}</code>")
    finally:
        os.remove(f"{song_name}.mp3")
        if thumb_file and os.path.exists(thumb_file):
            os.remove(thumb_file)

    await ms.delete()

modules_help["ytmusic"] = {
    "ymusic [song name]": "Search and download songs from YouTube Music"
  }
