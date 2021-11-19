"""
Immediately mark messages as read
"""
import asyncio

from telethon import events


@borg.on(events.NewMessage(incoming=True, chats=789995065))
async def _(event):
    event.mark_read()
