# Run this to download emojis
import os
from io import BytesIO
from pathlib import Path

import pyrogram.emoji
import requests
from bs4 import BeautifulSoup
from PIL import Image

emojiTypesMap = {
    "A": ("apple",),
    "F": ("facebook",),
    "G": ("google",),
    "H": ("htc",),
    "J": ("joypixels",),
    "L": ("lg",),
    "M": ("microsoft",),
    "ME": ("messenger",),
    "MZ": ("mozilla",),
    "O": ("openmoji",),
    "S": ("samsung",),
    "SB": ("softbank",),
}
emojiTypesMap["ALL"] = tuple(emojiTypesMap.values())


def main() -> int:
    if not os.path.exists(Path("resources") / "emojis"):
        os.mkdir(Path("resources") / "emojis")
    emojiTypes = input(
        "Which emojis do you want to download?\n"
        "[A] Apple (best)\n"
        "[E] Emojidex\n"
        "[F] Facebook\n"
        "[G] Google\n"
        "[H] Htc\n"
        "[J] JoyPixels\n"
        "[L] LG\n"
        "[M] Microsoft\n"
        "[ME] Messenger\n"
        "[MZ] Mozilla\n"
        "[O] OpenMoji\n"
        "[S] Samsung\n"
        "[SB] SoftBank\n"
        "[ALL] All of them\n"
        "> "
    ).upper()

    while emojiTypes not in emojiTypesMap:
        print("Invalid choice!")
        emojiTypes = input("> ").upper()

    for emojiType in emojiTypesMap[emojiTypes]:
        for imgTag in BeautifulSoup(
            requests.get("https://emojipedia.org/" + emojiType).text, "html.parser"
        ).select("img"):

            print(f"Downloading {emojiType} - {imgTag.attrs.get('alt')}")
            emojiPath = (
                Path("resources")
                / "emojis"
                / (
                    imgTag.attrs.get("alt")
                    .upper()
                    .replace(" ", "_")
                    .replace(":", "_")
                    .replace("-", "_")
                    .replace(",", "")
                    .replace("__", "_")
                    + "-"
                    + emojiType
                    + ".png"
                )
            )

            if os.path.exists(emojiPath):
                print(f"Skipped! This emoji has already been downloaded.")
                continue

            emojiImg = Image.open(
                BytesIO(
                    requests.get(
                        imgTag.attrs.get("data-src") or imgTag.attrs.get("src")
                    ).content
                )
            )
            emojiImg.resize((100, 100)).convert("RGBA").save(emojiPath)

    for emojiFName in os.listdir(Path("resources") / "emojis"):
        try:
            getattr(pyrogram.emoji, emojiFName.split("-")[0])
        except AttributeError:
            print(f"Deleting {emojiFName}: not in pyrogram.emoji")
            os.remove(Path("resources") / "emojis" / emojiFName)

    return 0


if __name__ == "__main__":
    exit(main())
