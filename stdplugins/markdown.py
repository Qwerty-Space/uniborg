# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
**Markdown**

This plugin automatically reformats messages based on specific text patterns. It supports the following transformations:

• ＡＥＳＴＨＥＴＩＣ Text (`a.. text ..`): Converts text to full-width Unicode characters.

• 🅱️-Meme (`b.. text ..`): Replaces the first letter of each word with 🅱️.

• Random Case (`c.. text ..`): Randomly capitalizes letters for a mocking effect.

• Chopsticks ('ch.. text ..'): 匚囗几ソ乇尺て丂  て乇乂て  て囗  卂丂工卂几  匚卄卂尺卂匚て乇尺丂  て卄卂て  乚囗囗ㄑ  ソ卂已ひ乇乚ㄚ  乚工ㄑ乇  乚卂て工几  乚乇てて乇尺丂

• Subreddit Links (`/r/subreddit` or `/u/username`): Converts subreddit and user mentions into clickable Reddit links.
"""
import re
from random import choice
from functools import partial

from telethon import events
from telethon.tl.functions.messages import EditMessageRequest
from telethon.utils import add_surrogate, del_surrogate
from telethon.tl.types import MessageEntityTextUrl


def parse_chopsticks(m):
    alpha = "卂乃匚刀乇千已卄工丁ㄑ乚爪几囗尸冋尺丂てひソ山乂ㄚ乙"
    mapped_chars= list()
    print(m)
    for c in (m.group(1)).upper():
        if c == " ":
            # make it two double width spaces
            char = u"\u3000\u3000"
        else:
            index = ord(c) - 65
            char = alpha[index]

        mapped_chars.append(char)

    print(''.join(mapped_chars))
    return "".join(mapped_chars), None


def parse_aesthetics(m):
    def aesthetify(string):
        for c in string:
            if " " < c <= "~":
                yield chr(ord(c) + 0xFF00 - 0x20)
            elif c == " ":
                yield "\u3000"
            else:
                yield c
    return "".join(aesthetify(m[1])), None


def parse_randcase(m):
    return ''.join(choice([str.upper, str.lower])(c) for c in m[1]), None

def parse_b_meme(m):
    return re.sub(r'(\s|^)\S(\S)', r'\1🅱️\2', m[1]), None

def parse_subreddit(m):
    text = '/' + m.group(3)
    entity = MessageEntityTextUrl(
        offset=m.start(2),
        length=len(text),
        url=f'https://reddit.com{text}'
    )
    return m.group(1) + text, entity


# A matcher is a tuple of (regex pattern, parse function)
# where the parse function takes the match and returns (text, entity)
MATCHERS = [
    (re.compile(r'a\.\.\s?(.+?)\.\.'), parse_aesthetics),
    (re.compile(r'b\.\.\s?(.+?)\.\.'), parse_b_meme),
    (re.compile(r'c\.\.\s?(.+?)\.\.'), parse_randcase),
    (re.compile(r'([^/\w]|^)(/?([ru]/\w+))'), parse_subreddit),
    (re.compile(r'ch\.\.\s?(.+?)\.\.'), parse_chopsticks),
]


def parse(message, old_entities=None):
    entities = []
    old_entities = sorted(old_entities or [], key=lambda e: e.offset)

    i = 0
    after = 0
    message = add_surrogate(message)
    while i < len(message):
        for after, e in enumerate(old_entities[after:], start=after):
            # If the next entity is strictly to our right, we're done here
            if i < e.offset:
                break
            # Skip already existing entities if we're at one
            if i == e.offset:
                i += e.length
        else:
            after += 1

        # Find the first pattern that matches
        for pattern, parser in MATCHERS:
            match = pattern.match(message, pos=i)
            if match:
                break
        else:
            i += 1
            continue

        text, entity = parser(match)

        # Shift old entities after our current position (so they stay in place)
        shift = len(text) - len(match[0])
        if shift:
            for e in old_entities[after:]:
                e.offset += shift

        # Replace whole match with text from parser
        message = ''.join((
            message[:match.start()],
            text,
            message[match.end():]
        ))

        # Append entity if we got one
        if entity:
            entities.append(entity)

        # Skip past the match
        i += len(text)

    return del_surrogate(message), entities + old_entities


@borg.on(events.MessageEdited(outgoing=True))
@borg.on(events.NewMessage(outgoing=True))
async def reparse(event):
    if not event.raw_text:
        return
    old_entities = event.message.entities or []
    parser = partial(parse, old_entities=old_entities)
    message, msg_entities = await borg._parse_message_text(event.raw_text, parser)
    if len(old_entities) >= len(msg_entities) and event.raw_text == message:
        return

    await borg(EditMessageRequest(
        peer=await event.get_input_chat(),
        id=event.message.id,
        message=message,
        no_webpage=not bool(event.message.media),
        entities=msg_entities
    ))
    raise events.StopPropagation
