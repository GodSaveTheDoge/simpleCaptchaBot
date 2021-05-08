# This plugin will show a captcha to new users
import asyncio
import os
import random
import time
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional, Tuple

import tgcrypto
from PIL import Image
from pyrogram import Client, emoji, filters
from pyrogram.types import (
    CallbackQuery,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)


def get_captcha(outfile: Optional[BytesIO] = None) -> Tuple[str, BytesIO]:
    """Returns a Tuple with the solution and the captcha."""

    captchaImg = Image.open(Path("resources") / "backgrounds" / random.choice(os.listdir(Path("resources") / "backgrounds")))
    emojiFName = random.choice(os.listdir(Path("resources") / "emojis"))
    emojiImg = Image.open(Path("resources") / "emojis" / emojiFName).rotate(
        random.randint(-60, 60), expand=True
    )
    
    captchaImg.paste(
        emojiImg,
        (
            int((captchaImg.size[0] - emojiImg.size[0]) / 2),
            int((captchaImg.size[1] - emojiImg.size[1]) / 2),
        ),
        emojiImg,
    )
    captchaBytesIO = outfile or BytesIO()
    captchaImg.save(captchaBytesIO, format="JPEG")
    
    return emojiFName.split("-")[0], captchaBytesIO


def encrypt_cdata(correct: bool, step: int, mistakes: int, userId: int) -> bytes:
    data = (
        correct.to_bytes(1, "little")
        + step.to_bytes(1, "little")
        + mistakes.to_bytes(1, "little")
        + userId.to_bytes(4, "little")
        + os.urandom(57)
    )
    iv = bytes(32)
    return tgcrypto.ige256_encrypt(data, key, iv)


def decrypt_cdata(data: bytes) -> Tuple[bool, int, int, int]:
    decrypted = tgcrypto.ige256_decrypt(data, key, bytes(32))
    return (
        bool(decrypted[0]),
        decrypted[1],
        decrypted[2],
        int.from_bytes(decrypted[3:7], "little"),
    )


def get_keyboard(correctEmoji: str, userId: int, step: int = 0, mistakes: int = 0) -> InlineKeyboardMarkup:
    buttonList = [InlineKeyboardButton(correctEmoji, encrypt_cdata(True, step, mistakes, userId))]
    
    for i in range(4):
        wrongEmoji = random.choice(allEmojis)
        
        while wrongEmoji == correctEmoji:
            wrongEmoji = random.choice(allEmojis)
        
        buttonList.append(
            InlineKeyboardButton(wrongEmoji, encrypt_cdata(False, step, mistakes, userId))
        )
    
    return InlineKeyboardMarkup(inline_keyboard=[random.sample(buttonList, 5)])


@Client.on_message(filters.new_chat_members)
def on_user_join(client: Client, msg: Message) -> None:
    for user in msg.new_chat_members:

        if client.get_chat_member(msg.chat.id, user.id).can_send_messages == False:
            client.kick_chat_member(
                msg.chat.id, user.id, until_date=int(time.time()) + 36000
            )  # 60*60*10 == 36000 == 10 hours
            msg.reply(f"Banned user {user.first_name} because they rejoined.")
            return

        client.restrict_chat_member(
            msg.chat.id,
            user.id,
            ChatPermissions(
                can_send_messages=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
            ),
        )
        client.send_chat_action(msg.chat.id, "upload_photo")

        captchaSolution, captchaBytesIO = get_captcha()
        captchaBytesIO.name = "captcha.jpeg"
        correctEmoji = getattr(emoji, captchaSolution)
        msg.reply_photo(
            captchaBytesIO,
            caption=f"Welcome {user.first_name}\nYou must complete a captcha to chat.\nChoose the correct emoji.",
            reply_markup=get_keyboard(correctEmoji, user.id,),
        )


@Client.on_callback_query()
def on_captcha_attempt(client: Client, cbQuery: CallbackQuery) -> None:
    isCorrect, step, mistakes, userId = decrypt_cdata(cbQuery.data)

    if not cbQuery.message:
        cbQuery.answer("Something went wrong")
        return

    if not userId == cbQuery.from_user.id:
        cbQuery.answer("This isn't your captcha!", show_alert=True)
        return
    
    if not isCorrect and mistakes >= 1:
        client.kick_chat_member(
            cbQuery.message.chat.id, cbQuery.from_user.id, until_date=int(time.time()) + 36000
        )  # 10 hours
        cbQuery.message.reply(f"Banned {cbQuery.from_user.first_name} because they failed the captcha!")
        cbQuery.message.delete()
        return
    
    if step >= 2:
        client.restrict_chat_member(
            cbQuery.message.chat.id,
            userId,
            ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_stickers=True,
                can_send_animations=True,
                can_send_games=True,
                can_use_inline_bots=True,
                can_add_web_page_previews=True,
                can_send_polls=True,
            ),
        )
        cbQuery.message.delete()
        return 0

    with NamedTemporaryFile(suffix=".png") as ntf:
        captchaSolution = get_captcha(outfile=ntf.file)[0]
        correctEmoji = getattr(emoji, captchaSolution)
        cbQuery.message.edit_media(
            InputMediaPhoto(ntf.name, caption=f"Choose the correct emoji."),
            reply_markup=get_keyboard(correctEmoji, userId, step=step+1, mistakes=mistakes+(not isCorrect)),
        )
    cbQuery.answer("Solve the next one!")


# Key for tgcrypto. Do not leak it, if you do delete .env to generate a new key
# if you change the key the bot won't be able to check any of the captchas already sent
if not os.path.exists(".env"):
    with open(".env", "wb") as fhandle:
        fhandle.write(os.urandom(32))
        # Note that the size must be 32

with open(".env", "rb") as fhandle:
    key = fhandle.read()

allEmojis = tuple(
    getattr(emoji, attrName) for attrName in dir(emoji) if attrName.isupper()
)
