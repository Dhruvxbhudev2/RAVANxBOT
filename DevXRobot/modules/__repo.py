import os
from pyrogram import Client, filters
from pyrogram.types import *

from DevXRobot.conf import get_str_key
from DevXRobot import pbot

REPO_TEXT = "**A Powerful [DEVX ROBOT](https://telegra.ph/file/6c66c67c6aeac89e3a487.jpg) to Make Your Groups Secured and Organized ! \n\n↼ Øwñêr ⇀ : 『 [HYPER](t.me/HYPER_AD17) 』\n╭──────────────\n┣─ » Python ~ 3.8.6\n┣─ » Update ~ Recently\n╰──────────────\n\n»»» @THN_BOTS «««"
  
BUTTONS = InlineKeyboardMarkup(
      [[
        InlineKeyboardButton("⚡ Source Code🔥", url=f"https://github.com/HyperAD/Dev-XRobot"),
        InlineKeyboardButton(" Support🚀", url=f"https://t.me/THN_BOTS_SUPPORT"),
      ],[
        InlineKeyboardButton("Owner ❣️", url="https://t.me/DEVX_OWNER"),
        InlineKeyboardButton("NETWORK ⚡", url="https://t.me/THN_NETWORK"),
      ],[
        InlineKeyboardButton("⚡ CHITCHAT🤩", url="https://t.me/kritismile1"),
        InlineKeyboardButton("Developer ➡️", url="https://t.me/HYPER_AD17"),
      ]]
    )
  
  
@pbot.on_message(filters.command(["repo"]))
async def repo(pbot, update):
    await update.reply_text(
        text=REPO_TEXT,
        reply_markup=BUTTONS,
        disable_web_page_preview=True,
        quote=True
    )
