import json
import requests
import time
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.misc import modules_help, prefix
from utils.scripts import progress

@Client.on_message(filters.command(["amusic", "applemusic"], prefix))
async def apple_music(client: Client, message: Message):
    chat_id = message.chat.id
    is_self = message.from_user and message.from_user.is_self

    if len(message.command) > 1:
        query = message.text.split(maxsplit=1)[1]
    elif message.reply_to_message:
        query = message.reply_to_message.text
    else:
        if is_self:
            await message.edit(
                f"<b>Usage:</b> <code>{prefix}amusic [song name]</code>"
            )
        else:
            await message.reply(
                f"<b>Usage:</b> <code>{prefix}amusic [song name]</code>"
            )
        return
    
    if is_self:
        ms = await message.edit_text(f"<code>Searching for {query} on Apple Music...</code>")
    else:
        ms = await message.reply(f"<code>Searching for {query} on Apple Music...</code>")
    
    try:
        search_url = f"https://delirius-apiofc.vercel.app/search/applemusicv2?query={query}"
        search_response = requests.get(search_url)
        search_response.raise_for_status()
        search_result = search_response.json()
    except Exception as e:
        await ms.edit_text(f"<code>Failed to search for the song: {str(e)}</code>")
        return

    if search_result.get('status') and search_result.get('data'):
        song_details = search_result['data'][0]
        song_name = song_details['title']
        song_artist = song_details['artist']
        song_thumb = song_details['image']
        song_url = song_details['url']

        await ms.edit_text(f"<code>Found: {song_name} by {song_artist}</code>\n<code>Fetching download link...</code>")

        try:
            download_url = f"https://delirius-apiofc.vercel.app/download/applemusicdl?url={song_url}"
            download_response = requests.get(download_url)
            download_response.raise_for_status()
            download_result = download_response.json()
        except Exception as e:
            await ms.edit_text(f"<code>Failed to fetch download link: {str(e)}</code>")
            return

        if download_result.get('status'):
            song_download_link = download_result['data'].get('download')
            if not song_download_link or 'undefined' in song_download_link:
                await ms.edit_text("<code>Song isn't available.</code>")
                return

            song_name = download_result['data']['name']
            song_thumb = download_result['data']['image']

            await ms.edit_text(f"<code>Downloading {song_name}...</code>")
            try:
                thumb_response = requests.get(song_thumb, stream=True)
                thumb_response.raise_for_status()
                with open(f"{song_name}.jpg", "wb") as f:
                    f.write(thumb_response.content)

                song_response = requests.get(song_download_link, stream=True)
                song_response.raise_for_status()
                with open(f"{song_name}.mp3", "wb") as f:
                    f.write(song_response.content)
            except Exception as e:
                await ms.edit_text(f"<code>Failed to download the song: {str(e)}</code>")
                return

            await ms.edit_text(f"<code>Uploading {song_name}...</code>")
            c_time = time.time()
            
            try:
                await client.send_audio(
                    chat_id,
                    f"{song_name}.mp3",
                    caption=f"<b>Song Name:</b> {song_name}\n<b>Artist:</b> {song_artist}",
                    progress=progress,
                    progress_args=(ms, c_time, f"<code>Uploading {song_name}...</code>"),
                    thumb=f"{song_name}.jpg"
                )
            except Exception as e:
                await ms.edit_text(f"<code>Failed to upload the song: {str(e)}</code>")
                return
            finally:
                if os.path.exists(f"{song_name}.jpg"):
                    os.remove(f"{song_name}.jpg")
                if os.path.exists(f"{song_name}.mp3"):
                    os.remove(f"{song_name}.mp3")

            await ms.delete()
        else:
            await ms.edit_text(f"<code>Failed to fetch download link for {song_name}</code>")
    else:
        await ms.edit_text(f"<code>No results found for {query}</code>")

modules_help["applemusic"] = {
    "amusic": "search, download and upload songs from Apple Music"
}
