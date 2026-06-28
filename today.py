"""Handler: /today — show today's tasks with inline action buttons."""
from __future__ import annotations

import logging
from datetime import date, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from core.sheets import get_day_status
from keyboards.inline import task_list_keyboard, today_overview_keyboard
from utils.formatting import escape_md, format_today_message

logger = logging.getLogger(__name__)


def _date_from_iso(iso: str) -> date:
    return date.fromisoformat(iso)


async def today_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show today's task list with action buttons."""
    target = date.today()
    await _send_day(update, ctx, target, edit=False)


async def _send_day(
    update: Update,
    ctx: ContextTypes.DEFAULT_TYPE,
    target: date,
    edit: bool = False,
) -> None:
    msg = update.message or (update.callback_query.message if update.callback_query else None)
    if msg is None:
        return

    await (msg.reply_text if not edit else msg.edit_text)(
        "⏳ _Sheet se data la raha hoon\\.\\.\\._",
        parse_mode="MarkdownV2",
    ) if not edit else None

    status = get_day_status(target)
    if status is None:
        err_text = (
            f"❌ {escape_md(str(target))} ka data nahi mila sheet mein\\.\n"
            "Shayad yeh month ka data sheet mein nahi hai\\."
        )
        if edit:
            await msg.edit_text(err_text, parse_mode="MarkdownV2")
        else:
            await msg.reply_text(err_text, parse_mode="MarkdownV2")
        return

    text = format_today_message(status, target)
    keyboard = task_list_keyboard(status["tasks"], target.isoformat(), page=0)

    if edit:
        await msg.edit_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
    else:
        await msg.reply_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)


async def yesterday_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    target = date.today() - timedelta(days=1)
    await _send_day(update, ctx, target, edit=False)


async def tomorrow_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    target = date.today() + timedelta(days=1)
    await _send_day(update, ctx, target, edit=False)
