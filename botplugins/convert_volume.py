r"""Convert Weight

Convert weights to other common weights. 
Plugin gets triggered by a standalone message in the form of `{number} {weight1} in/to {weight2}`

Use /weights to list accepted weight units.

patterns: 
`(?i)^(\d+(?:(?:\.|,)\d+)?)? ?(k?g|ton(?:ne)?s?|lbs|oz|st(?:one)?) (?:to|in) (k?g|ton(?:ne)?s?|lbs|oz|st(?:one)?)$`
`/weights`
"""

from telethon import events
from uniborg.util import cooldown, blacklist


units = {
    "m³": 1,
    "barrel": 0.158987294928,
    "ft³": 0.028316846592,
    "litre": 0.001,
    "in³": 0.000016387064,
    "cm³": 0.000001,
    "uk gallon": 0.00455,
    "uk pint": 0.00057,
    "us gallon": 0.003785411784,
    "us pint": 0.000473176473
}

def singular(unit):
    if "3" in unit:
        return f"{unit.rstrip("^3")}³"
    if "cent" in unit:
        return "cm³"
    if "cubic metre" in unit:
        return "m³"
    if "inch" in unit:
        return "in³"
    if unit in ["feet", "ft"]:
        return "ft³"
    if "gb" in unit:
        return singular(unit.replace("gb", "uk"))
    if unit.endswith("s"):
        return unit[:-1]

    return unit


def plural(unit, amount):
    if amount == 1:
        return unit
    if len(unit) < 3:
        return unit
    if "³" in unit:
        return unit

    return unit + "s"

pattern_measurements = r"(c?m\^?3|cubic (?:(?:centi)?metres?|f[eo]*t|inch(?:es)?)|barrels?|litres?|(?:uk|us|gb)? ?(?:gallon|pint)s?)"

@borg.on(events.NewMessage(
    pattern=rf"(?i)^(\d+(?:[\.,]\d+)?)? ?{pattern_measurements} (?:to|in) {pattern_measurements}$"
))
async def calculate(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    m = event.pattern_match
    value = m.group(1)

    if not value:
        value = 1
    value = value.replace(",", ".")

    unitfrom = singular(m.group(2).lower())
    unitto = singular(m.group(3).lower())
    print(unitfrom, unitto)

    try:
        result = round(float(value)*units[unitfrom]/units[unitto], 3)
    except ValueError:
        pass
    except KeyError:
        return

    plural_from = plural(unitfrom, float(value))
    plural_to = plural(unitto, result)

    await event.reply(f"**{value} {plural_from} is:**  `{result} {plural_to}`")


@borg.on(borg.cmd(r"volumes$"))
@cooldown(60, delete=True)
async def list_measurements(event):
    blacklist = storage.blacklist or set()
    if event.chat_id in blacklist:
        return

    text = f"**List of supported volumes:**\n" + ", ".join(sorted(units.keys()))
    await event.reply(text)

@borg.on(borg.blacklist_plugin())
async def on_blacklist(event):
    storage.blacklist = await blacklist(event, storage.blacklist)

