import os
import re
import uvicorn
import asyncio
from fastapi import FastAPI
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import KeyboardButtonUrl

# --- Credentials ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")

# --- Channels ---
SOURCE_CHANNEL = "@goldmasterclub"
TARGET_CHANNEL = "@forthgoldtrader"

# --- Replacement ---
REPLACE_WITH = "@aimanagementteambot"

# --- FastAPI App ---
app = FastAPI()

# --- Telethon Client (using SESSION_STRING) ---
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# --- Clean text ---
def clean_text(text: str) -> str:
    if not text:
        return text
    text = re.sub(r"@\w+", REPLACE_WITH, text, flags=re.IGNORECASE)
    text = re.sub(r"https?://[^\s)>\]]+", REPLACE_WITH, text, flags=re.IGNORECASE)
    return text

# --- Replace/add custom button ---
def replace_buttons(reply_markup):
    custom_button = [KeyboardButtonUrl(text="💬 Join Our Bot", url="https://t.me/aimanagementteambot")]
    return reply_markup or [custom_button]

# --- Forward new messages ---
@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def handler(event):
    try:
        reply_markup = replace_buttons(event.message.reply_markup) if event.message.reply_markup else None
        text_content = clean_text(event.raw_text)

        # Handle albums (media groups)
        if event.message.grouped_id:
            media_group = [event.message]
            async for m in client.iter_messages(SOURCE_CHANNEL, reverse=False, offset_id=event.message.id - 1):
                if m.grouped_id == event.message.grouped_id:
                    media_group.append(m)
                else:
                    break
            media_group = sorted(media_group, key=lambda x: x.id)
            files = [m.media for m in media_group if m.media]

            await client.send_file(
                TARGET_CHANNEL,
                files,
                caption=text_content or "",
                buttons=reply_markup
            )

        elif event.message.media:
            await client.send_file(
                TARGET_CHANNEL,
                event.message.media,
                caption=text_content or "",
                buttons=reply_markup
            )

        elif text_content:
            await client.send_message(TARGET_CHANNEL, text_content, buttons=reply_markup)

        elif reply_markup:
            await client.send_message(TARGET_CHANNEL, "📢", buttons=reply_markup)

        print(f"✅ Forwarded new message {event.message.id}")
    except Exception as e:
        print(f"⚠️ Error forwarding message {event.message.id}: {e}")

# --- Healthcheck (for Render/Replit) ---
@app.get("/")
async def root():
    return {"status": "running"}

# --- Start bot on app startup ---
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(client.start())
    print("🚀 Bot started and listening for new messages...")

# --- Run ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
