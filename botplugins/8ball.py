r"""Magic 8 Ball

Responds with a magic eight-ball answer to `/8ball`

patterns:
`/8ball( .+)?`
"""

import re
from random import choice, randint

from telethon import events
from uniborg.util import blacklist


positive_answers = [
    "Without a doubt.",
    "Yes.",
    "Yes - definitely.",
    "You may rely on it.",
    "Signs point to yes.",
    "Outlook good.",
    "It is certain.",
    "It is decidedly so.",
    "Most likely.",
    "As I see it, yes.",
    "This is the Way",
]

neutral_answers = [
    "Reply hazy, try again.",
    "Ask again later.",
    "Better not tell you now.",
    "Cannot predict now.",
    "Concentrate and ask again.",
]

negative_answers = [
    "Very doubtful.",
    "Very unlikely.",
    "Outlook not so good.",
    "My reply is no.",
    "My sources say no.",
    "No.",
    "No - don't even think about it.",
    "Don't count on it.",
]

# Matches "/8ball" 
@borg.on(borg.cmd(r"8ball( .+)?"))
async def magic(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    answers_list = [
        positive_answers, positive_answers,
        neutral_answers, negative_answers
    ]

    outcome = randint(0, 3)
    await event.reply(choice(answers_list[outcome]))

@borg.on(borg.blacklist_plugin())
async def on_blacklist(event):
    storage.blacklist = await blacklist(event, storage.blacklist)
