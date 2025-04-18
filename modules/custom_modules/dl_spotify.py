import json
import requests
import time
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix
from utils.scripts import progress


@Client.on_message(filters.command(["sdl", "spotify"], prefix))
async def spotify_download(client: Client, message: Message):
    chat_id = message.chat.id
    is_self = message.from_user and message.from_user.is_self

    # Extract query from the command or replied message
    query = (
        message.text.split(maxsplit=1)[1]
        if len(message.command) > 1
        else message.reply_to_message.text.strip()
        if message.reply_to_message
        else None
    )

    if not query:
        response = f"<b>Usage:</b> <code>{prefix}sdl [song name]</code>"
        await (message.edit(response) if is_self else message.reply(response))
        return

    # Initial searching message
    status_message = await (
        message.edit_text(f"<code>Searching for {query} on Spotify...</code>")
        if is_self
        else message.reply(f"<code>Searching for {query} on Spotify...</code>")
    )

    # Search for the song
    try:
        search_result = requests.get(
            f"https://delirius-apiofc.vercel.app/search/spotify?q={query}&limit=1"
        ).json()
        if not (search_result.get("status") and search_result.get("data")):
            raise ValueError("No results found")
    except Exception as e:
        await status_message.edit_text(f"<code>Failed to search: {str(e)}</code>")
        return

    song_details = search_result["data"][0]
    song_name, song_artist, song_thumb, song_url = (
        song_details["title"],
        song_details["artist"],
        song_details["image"],
        song_details["url"],
    )

    await status_message.edit_text(
        f"<code>Found: {song_name} by {song_artist}</code>\n<code>Fetching download link...</code>"
    )

    # Fetch download link
    try:
        download_result = requests.get(
            f"https://delirius-apiofc.vercel.app/download/spotifydlv3?url={song_url}"
        ).json()
        if not download_result.get("status"):
            raise ValueError("Failed to fetch download link")
    except Exception as e:
        await status_message.edit_text(f"<code>Failed to fetch link: {str(e)}</code>")
        return

    song_download_link = download_result["data"].get("url")
    song_name, song_artist, song_thumb = (
        download_result["data"]["title"],
        download_result["data"]["author"],
        download_result["data"]["image"],
    )

    if not song_download_link or not song_download_link.startswith("http"):
        await status_message.edit_text("<code>Song isn't available for download.</code>")
        return

    await status_message.edit_text(f"<code>Downloading {song_name}...</code>")

    # Download the song and thumbnail
    try:
        # Download thumbnail
        if song_thumb:
            with open(f"{song_name}.jpg", "wb") as thumb_file:
                thumb_file.write(requests.get(song_thumb, stream=True).content)

        # Download song
        song_response = requests.get(song_download_link, stream=True)
        if "audio" not in song_response.headers.get("Content-Type", ""):
            raise ValueError("Invalid audio file")
        
        with open(f"{song_name}.mp3", "wb") as song_file:
            song_file.write(song_response.content)
    except Exception as e:
        await status_message.edit_text(f"<code>Failed to download: {str(e)}</code>")
        return

    await status_message.edit_text(f"<code>Uploading {song_name}...</code>")

    # Upload the song
    try:
        c_time = time.time()
        await client.send_audio(
            chat_id,
            f"{song_name}.mp3",
            caption=f"<b>Song Name:</b> {song_name}\n<b>Artist:</b> {song_artist}",
            progress=progress,
            progress_args=(status_message, c_time, f"<code>Uploading {song_name}...</code>"),
            thumb=f"{song_name}.jpg" if os.path.exists(f"{song_name}.jpg") else None,
        )
    except Exception as e:
        await status_message.edit_text(f"<code>Failed to upload: {str(e)}</code>")
        return
    finally:
        # Cleanup downloaded files
        for file in [f"{song_name}.jpg", f"{song_name}.mp3"]:
            if os.path.exists(file):
                os.remove(file)

    await status_message.delete()

modules_help["spotify"] = {
    "sdl [song name]": "search, download, and upload songs from Spotify"
}
