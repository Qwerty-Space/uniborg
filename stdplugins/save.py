"""
**Save messages from channels that don't allow saving:**
Command: `s(?:(?:av|har)e)?`

**There are two major modes:**
• First mode: `[message link] [last message]`
• Second mode: `[channel link, username, or ID] [message ID] [last message]`

**Last message argument:**
Both modes take a message ID as the last argument, or an increment in the format of `+5`
The first mode also takes another message link as a second argument

**Examples:**
• `.save https://t.me/telegram/123 456`
• `.save https://t.me/telegram/123 +5`
• `.save https://t.me/telegram/ 123 456`
• `.save https://t.me/telegram/ 123 +5`
• `.save @telegram 123 456`
• `.save @telegram 123 +5`
• `.save 1005640892 123 456`
• `.save 1005640892 123 +5`
"""
from re import search
from io import BytesIO

from telethon import events

cmd = r"s(?:(?:av|har)e)?"
link_base = r"(?:https?:\/\/)?t(?:elegram)?\.(?:me|dog)\/"
link_pattern = rf"(?:{link_base}(?:c\/(\d+)|(\S+))\/(\d+))"
alt_link_pattern = rf"(?:{link_base}(\S+)\/|(@\S+)|(-?\d+))"
end_pattern = r"(?:(\s*\+?)(\d+))"

first_mode = rf"{link_pattern} (?:{link_pattern}|{end_pattern})"
second_mode = rf"{alt_link_pattern} (\d+){end_pattern}"


@borg.on(borg.cmd(cmd, pattern=first_mode))
async def mode_one(event):
    m = event.pattern_match
 
    chat = m.group(1) or f"@{m.group(2)}"

    first_message = int(m.group(3)) - 1
    last_message = int(m.group(6) or m.group(8)) + 1
    if '+' in m.group(7):
        last_message = first_message + last_message + 1

    await save(event, chat, first_message, last_message)


@borg.on(borg.cmd(cmd, pattern=second_mode))
async def mode_two(event):
    m = event.pattern_match
    print(m.groups())
    if m.group(1):
        chat = f"@{m.group(1).strip('/')}"
    else:
        chat = m.group(2) or m.group(3)

    first_message = int(m.group(4)) - 1

    last_message = int(m.group(6)) + 1
    if '+' in m.group(5):
        last_message = first_message + last_message + 1

    await save(event, chat, first_message, last_message)

async def save(event, chat, first_message, last_message):
    await event.delete()
    files = list()

    async for m in borg.iter_messages(chat, min_id=first_message, max_id=last_message, reverse=True):
        try:
            file = await m.download_media(file=BytesIO())
            file.seek(0)
            file.name = f'{m.id}{m.file.ext}'
            files.append(file)
        except: 
            pass

    images = ['jpg', 'jpeg', 'png', 'webp']
    for f in files:
        image = any(i in f.name for i in images)
        await borg.send_file('me', f, force_document=image, supports_streaming=True)

