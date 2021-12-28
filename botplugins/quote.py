"""Quotes

Add a quote to the database with `/quote` and recall with `/recall search term`.
It only works with messages sent to a group by a user (no forwards).
Quotes are recalled with the text, the sender's name, and date it was originally sent.

patterns:
 • `q(uote)?|cite`
 • `(r(ecall)?|(get|fetch)quote)(?: ([\s\S]+))?`
 • `lq|listquotes?`
ADMIN ONLY:
 • `rmq(uote)? (\d+)(?:\:(\d+))?`
"""

import html
from asyncio import sleep
from random import choice
from datetime import datetime, timedelta
import struct
from collections import defaultdict
from telethon import types, events, errors
from uniborg.util import cooldown, blacklist


# Convert from old list format to defaultdict
quotes = defaultdict(dict, storage.quotes or {})
for chat_id, quote_list in quotes.items():
    if isinstance(quote_list, dict):
        continue
    quotes[chat_id] = {
        quote["id"]: {
            k: v for k, v in quote.items() if k != "id"
        } for quote in quote_list
    }
storage.quotes = quotes

quote_list_auths = set()


@borg.on(borg.cmd(r"(q(uote)?|cite)"))
@cooldown(15)
async def add_quote(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    if event.is_private:
        return

    chat = str(event.chat_id)
    if not event.is_reply:
        await prelist_quotes(event)
        return

    reply_msg = await event.get_reply_message()
    if reply_msg.forward:
        return

    text = reply_msg.raw_text
    if not text:
        return

    sender = await reply_msg.get_sender()
    if isinstance(sender, types.Channel) or sender.bot:
        return

    quote_id = str(reply_msg.id)
    quote = {
        "text": text,
        "sender": sender,
        "date": reply_msg.date
    }

    quotes = storage.quotes
    if quote_id in quotes[chat]:
        msg = await event.reply("Duplicate quote in database")
        await sleep(10)
        await msg.delete()
        try:
            await event.delete()
        except:
            pass
        return

    quotes[chat][quote_id] = quote
    storage.quotes = quotes

    user = (await event.get_sender()).first_name
    await event.respond(f"Quote saved by {user}!  (ID:  `{reply_msg.id}`)",
                        reply_to=reply_msg)
    try:
        await sleep(10)
        await event.delete()
    except:
        pass


@borg.on(borg.admin_cmd(r"rmq(?:uote)?", r"(\d+)(?:\:(\-?\d+))?"))
@cooldown(5)
async def rm_quote(event):
    match = event.pattern_match
    query_id = match.group(1)
    chat = match.group(2) or str(event.chat_id)

    quotes = storage.quotes

    try:
        del quotes[chat][query_id]
        storage.quotes = quotes
        await event.reply(f"Quote `{query_id}` in chat: `{chat}` removed")
    except KeyError:
        await event.reply(f"No quote with ID `{query_id}`")


@borg.on(borg.cmd(r"(r(ecall)?|(get|fetch)quote)(?: (?P<phrase>[\s\S]+))?"))
@cooldown(10)
async def recall_quote(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    if event.is_private:
        return

    phrase = event.pattern_match["phrase"]
    chat = str(event.chat_id)

    match_quotes = []
    quotes = storage.quotes

    if not quotes[chat]:
        return

    if not phrase:
        match_quotes = list(quotes[chat].keys())
    else:
        phrase = phrase.lower()
        for id, q in quotes[chat].items():
            text = q["text"].lower()
            sender = q["sender"]
            first_name = sender.first_name.lower()
            last_name = (sender.last_name or "").lower()
            full_name = f"{first_name} {last_name}"
            username = (sender.username or "").lower()

            if phrase == id:
                match_quotes.append(id)
                break
            if phrase in text:
                match_quotes.append(id)
                continue
            if phrase in full_name:
                match_quotes.append(id)
                continue
            if phrase in username:
                match_quotes.append(id)
                continue

    if not match_quotes:
        msg = await event.reply(f"No quotes matching query:  `{phrase}`")
        await sleep(10)
        await msg.delete()
        await event.delete()
        return

    id = choice(match_quotes)
    quote = quotes[chat][id]
    reply_msg = await event.get_reply_message()
    msg = await event.respond(format_quote(id, quote, True, max_text_len=3000), parse_mode="html", reply_to=reply_msg)
    await sleep(0.5)
    await msg.edit(format_quote(id, quote, max_text_len=3000), parse_mode="html")

    try:
        await sleep(5)
        await event.delete()
    except:
        pass


@borg.on(borg.cmd(r"(lq|listquotes?)"))
async def prelist_quotes(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    if event.is_private:
        return

    chat = str(event.chat_id)
    quotes = storage.quotes

    if not quotes[chat]:
        await event.reply("There are no quotes saved for this group"
            + "\nReply to a message with `/quote` to cite that message, "
            + "and `/recall` to recall.")
        return

    button_data = struct.pack("!cBq", b"q", 0, event.chat_id)

    await event.reply(
        f"There are `{len(quotes[chat])}` quotes saved for this group"
        "\nReply to a message with `/quote` to cite that message, "
        "and `/recall` to recall."
        "\n\nAlternatively, press the button below to view all the saved quotes",
        buttons=[[
            types.KeyboardButtonCallback("View quotes", button_data)
        ]]
    )


@borg.on(events.CallbackQuery(pattern=b"(?s)^q\x00.{8}$"))
async def prelist_quotes_button(event):
    chat_id, = struct.unpack("!xxq", event.data)

    quote_list_auths.add((chat_id, event.query.user_id))

    await event.answer(
        url=f"http://t.me/{borg.me.username}?start=ql_{chat_id}"
    )


@borg.on(events.CallbackQuery(pattern=b"(?s)^q[\x01\x02].{16}$"))
async def paginate_quotes_button(event):
    direction, chat_id, quote_id = struct.unpack("!xBqq", event.data)

    msg = await event.get_message()
    age = datetime.utcnow() - msg.date.replace(tzinfo=None)
    if age >= timedelta(hours=1):
        await event.edit("Sorry, this quote list has expired. "
            "Please request a new list in the group.")
        return

    formatted, fmt_range, match_ids = fetch_quotes_near(
        chat_id, quote_id, before=(direction == 1)
    )
    if not match_ids:
        await event.answer("No more quotes to display")
        return
    try:
        await borg.edit_message(
            await event.get_input_chat(),
            event.query.msg_id,
            formatted,
            parse_mode="html",
            buttons=get_quote_list_buttons(chat_id, match_ids, fmt_range)
        )
    except errors.MessageNotModifiedError:
        await event.answer("No more quotes to display")


@borg.on(events.CallbackQuery(pattern=b"(?s)^q\x04$"))
async def do_nothing_button(event):
    await event.answer()


@borg.on(borg.cmd(r"start ql_(-?\d+)$"))
async def on_start_quote_list(event):
    chat_id = int(event.pattern_match.group(1))

    try:
        quote_list_auths.remove((chat_id, event.sender_id)) 
    except KeyError:
        return

    formatted, fmt_range, match_ids = fetch_quotes_near(chat_id, 0)
    await event.respond(
        formatted,
        parse_mode="html",
        buttons=get_quote_list_buttons(chat_id, match_ids, fmt_range)
    )


def get_quote_list_buttons(chat_id, match_ids, fmt_range):
    if not match_ids:
        return None

    prev_data = struct.pack("!cBqq", b"q", 1, chat_id, match_ids[0])
    next_data = struct.pack("!cBqq", b"q", 2, chat_id, match_ids[-1])
    return [[
        types.KeyboardButtonCallback("<", prev_data),
        types.KeyboardButtonCallback(fmt_range, b'q\x04'),
        types.KeyboardButtonCallback(">", next_data),
    ]]


def fetch_quotes_near(chat_id, quote_id, count=8, before=False):
    quotes = storage.quotes[str(chat_id)]
    quote_id = int(quote_id)
    ids = sorted(int(id) for id in quotes.keys())
    if not ids:
        return "No quotes to display.", "", []
    ids_len = len(ids)
    count = min(count, ids_len)

    # search for the index where quote_id is (or was, in case of deletion)
    start_i = next((i for i, id in enumerate(ids) if id >= quote_id), 0)
    if before:
        # we're slicing starting `count` quotes before this one
        start_i -= count
    elif ids and ids[start_i] == quote_id:
        # skip matched quote when going forward
        start_i += 1
    # fetch `count` quotes starting from `start_i`, wrapping around
    match_ids = [ids[(start_i + i) % ids_len] for i in range(count)]

    fmt_range = f"{round((start_i % ids_len) / ids_len * 100, 1)}%"
    formatted = "\n\n".join(format_quote(id, quotes[id]) for id in map(str, match_ids))
    return formatted, fmt_range, match_ids


def format_quote(id, quote, only_text=False, max_text_len=250):
    text = quote["text"]
    if len(text) > max_text_len:
        text = f"{text[:max_text_len]}…"
    formatted = f"<b>{html.escape(text)}</b>"
    if only_text:
        return formatted

    sender = quote["sender"]
    sender_name = html.escape(f"{sender.first_name} {sender.last_name or ''}")
    msg_date = (quote["date"]).strftime("%B, %Y")

    formatted += f"\n<i>- <a href='tg://user?id={sender.id}'>{sender_name}</a>, "
    formatted += f"<a href='t.me/share/url?url=%2Frecall+{id}'>{msg_date}</a></i>"

    return formatted


@borg.on(borg.blacklist_plugin())
async def on_blacklist(event):
    storage.blacklist = await blacklist(event, storage.blacklist)
