# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
**Send a random sticker:**
• `.dab`:  Dabbing
• `.brain`:  Supermind brain expansion thing
• `.fp`:  Facepalm
• `.hug`:  Hugs
• `.pat`:  Headpats
"""
import random

from telethon import events, types, functions, utils


def chooser(cmd, packs, blacklist={}):
    docs = None
    @borg.on(events.NewMessage(pattern=rf'\.{cmd}', outgoing=True))
    async def handler(event):
        await event.delete()

        nonlocal docs
        if docs is None:
            docs = []
            for pack in packs:
                res = await borg(functions.messages.GetStickerSetRequest(types.InputStickerSetShortName(pack), hash=0))
                docs.extend(
                    utils.get_input_document(x)
                    for x in res.documents
                    if x.id not in blacklist
                )

        await event.respond(file=random.choice(docs), reply_to=event.reply_to_msg_id)


chooser('brain', ['supermind'])
chooser('dab', ['DabOnHaters'], {
    1653974154589768377,
    1653974154589768312,
    1653974154589767857,
    1653974154589768311,
    1653974154589767816,
    1653974154589767939,
    1653974154589767944,
    1653974154589767912,
    1653974154589767911,
    1653974154589767910,
    1653974154589767909,
    1653974154589767863,
    1653974154589767852,
    1653974154589768677,
    1653974154589767120, # furry shit
})
chooser('fp', ['facepalmstickers'], {
    285892071401720411,
    285892071401725809
})

chooser('hug', ['JurreHugs'], {
    558487714329003463,
    558487714329003569,
    558487714329003571,
    558487714329003450,
})

chooser('pat', ['Patpackv4', 'PerplexedPat'], {
    1066778402112930981,
    1066778402112930658,
    1066778402112930914,
    1066778402112930949,
    1066778402112931126,
    1066778402112930946,
    1066778402112930925,
    1066778402112930919,
    1066778402112930915,
    1066778402112930958,
    1066778402112930961,
    1066778402112930968,
    1066778402112931013,
    1066778402112931163,
    1066778402112931162,
    1066778402112931023,
    1066778402112930910,
    1066778402112930906,
    1066778402112930995,
})

chooser('uoh', ['JanniesOnSuicideWatch', 'uohhhhhh', 'uohhhhh'], {
    5814695650683521701,
})

