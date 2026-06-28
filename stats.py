"""Handler: /stats — show dashboard."""
from __future__ import annotations

import logging
from datetime import date

from telegram import Message, Update
from telegram.ext import ContextTypes

from core.sheets import (
    get_body_measurements,
    get_day_status,
    get_month_completion,
    get_streaks,
    get_week_completion,
)
from core.streak import get_all_streaks
from utils.formatting import format_stats_message

logger = logging.getLogger(__name__)


async def stats_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_stats(update.message, update.effective_user.id)


async def _send_stats(msg: Message, user_id: int) -> None:
    await msg.reply_text("📊 _Data fetch ho raha hai\\.\\.\\._", parse_mode="MarkdownV2")

    today_status = get_day_status(date.today())
    today_pct   = today_status["completion_pct"] if today_status else 0.0
    week_pct    = get_week_completion()
    month_pct   = get_month_completion()
    sheet_streaks = get_streaks()          # from sheets (for today calculation)
    db_streaks    = get_all_streaks()       # from SQLite (cumulative)

    # Merge: prefer db (has history), fallback to sheet
    merged: dict[str, dict[str, int]] = {}
    for task, streak_count in sheet_streaks.items():
        db_data = db_streaks.get(task, {})
        merged[task] = {
            "current": db_data.get("current", streak_count),
            "longest": db_data.get("longest", streak_count),
        }
    # Add any db-only tasks
    for task, data in db_streaks.items():
        if task not in merged:
            merged[task] = data

    measurements = get_body_measurements()
    text = format_stats_message(today_pct, week_pct, month_pct, merged, measurements)
    await msg.reply_text(text, parse_mode="MarkdownV2")
