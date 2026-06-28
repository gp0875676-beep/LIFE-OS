"""Handlers: /start, /help."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

WELCOME = """
🙏 *Sat Sri Akal bhai\\!* Welcome to *LifeOS* 🚀

Tera personal AI life management system ready hai\\.

*Commands:*
/today — Aaj ke saare tasks
/stats — Dashboard \\& streaks  
/report — Weekly report
/help — Yeh message

*Reminders apne aap aayenge* ⏰
Bas tasks mark karo aur life sahi karo 💪
"""


async def start_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME, parse_mode="MarkdownV2")


async def help_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME, parse_mode="MarkdownV2")
