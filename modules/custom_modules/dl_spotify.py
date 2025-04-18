import os
import time
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix
from utils.scripts import progress


@Client.on_message(filters.command(["sdl", "spotify"], prefix))
async def spotify_download(client: Client, message: Message):
    # Extract the query from the command or replied message
    query = (
        message.text.split(maxsplit=1)[1]
        if len(message.command) > 1
        else message.reply_to_message.text.strip()
        if message.reply_to_message
        else None
    )

    if not query:
        await message.reply(f"<b>Usage:</b> <code>{prefix}sdl [song name]</code>")
        return

    # Notify the user about the search
    status_message = await message.reply(f"<code>Searching for {query} on Spotify...</code>")

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

    # Extract song details
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

    # Validate and extract download details
    song_download_link = download_result["data"].get("url")
    song_name = download_result["data"]["title"]
    song_artist = download_result["data"]["author"]
    song_thumb = download_result["data"]["image"]

    if not song_download_link or not song_download_link.startswith("http"):
        await status_message.edit_text("<code>Song isn't available for download.</code>")
        return

    await status_message.edit_text(f"<code>Downloading {song_name}...</code>")

    # Download the song and thumbnail
    try:
        thumb_path = f"{song_name}.jpg"
        if song_thumb:
            with open(thumb_path, "wb") as thumb_file:
                thumb_file.write(requests.get(song_thumb, stream=True).content)

        song_path = f"{song_name}.mp3"
        song_response = requests.get(song_download_link, stream=True)
        if "audio" not in song_response.headers.get("Content-Type", ""):
            raise ValueError("Invalid audio file")
        with open(song_path, "wb") as song_file:
            song_file.write(song_response.content)
    except Exception as e:
        await status_message.edit_text(f"<code>Failed to download: {str(e)}</code>")
        return

    await status_message.edit_text(f"<code>Uploading {song_name}...</code>")

    # Upload the song
    try:
        c_time = time.time()
        await client.send_audio(
            message.chat.id,
            song_path,
            caption=f"<b>Song Name:</b> {song_name}\n<b>Artist:</b> {song_artist}",
            progress=progress,
            progress_args=(status_message, c_time, f"<code>Uploading {song_name}...</code>"),
            thumb=thumb_path if os.path.exists(thumb_path) else None,
        )
    except Exception as e:
        await status_message.edit_text(f"<code>Failed to upload: {str(e)}</code>")
        return
    finally:
        # Cleanup temporary files
        for file in [thumb_path, song_path]:
            if os.path.exists(file):
                os.remove(file)

    await status_message.delete()

modules_help["spotify"] = {
    "sdl [song name]": "Search, download, and upload songs from Spotify"
}
