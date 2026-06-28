"""Callback query handler — processes inline button presses."""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_CHAT_ID, TASKS, TZ
from core.sheets import get_day_status, mark_task
from core.streak import save_snooze, update_streak
from keyboards.inline import task_list_keyboard
from utils.formatting import escape_md, format_today_message

logger = logging.getLogger(__name__)


async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: C901
    query = update.callback_query
    await query.answer()

    data: str = query.data or ""
    parts = data.split("|", 2)
    action = parts[0]
    date_iso = parts[1] if len(parts) > 1 else date.today().isoformat()
    extra = parts[2] if len(parts) > 2 else ""

    target = date.fromisoformat(date_iso)

    # ── DONE ──────────────────────────────────────────────────────────────────
    if action == "done":
        task = extra
        ok = mark_task(target, task, True)
        update_streak(task, True, target)
        if ok:
            status = get_day_status(target)
            if status:
                text = format_today_message(status, target)
                keyboard = task_list_keyboard(status["tasks"], date_iso, page=0)
                await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
        else:
            await query.edit_message_text(
                f"❌ Error updating *{escape_md(task)}*\\. Sheet check karo\\.",
                parse_mode="MarkdownV2",
            )
        return

    # ── SKIP ──────────────────────────────────────────────────────────────────
    if action == "skip":
        task = extra
        ok = mark_task(target, task, False)
        update_streak(task, False, target)
        if ok:
            await query.answer(f"⏭️ {task} skipped.", show_alert=False)
            status = get_day_status(target)
            if status:
                text = format_today_message(status, target)
                keyboard = task_list_keyboard(status["tasks"], date_iso, page=0)
                await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
        return

    # ── SNOOZE ────────────────────────────────────────────────────────────────
    if action == "snooze":
        task = extra
        fire_at = (datetime.now(tz=TZ) + timedelta(minutes=15)).isoformat(timespec="minutes")
        save_snooze(query.from_user.id, task, fire_at)
        await query.answer(f"⏰ Snoozed 15 min: {task}", show_alert=True)
        return

    # ── TOGGLE ────────────────────────────────────────────────────────────────
    if action == "toggle":
        task = extra
        status = get_day_status(target)
        if status is None:
            await query.answer("Data nahi mila!", show_alert=True)
            return
        current_val = status["tasks"].get(task, False)
        new_val = not current_val
        mark_task(target, task, new_val)
        update_streak(task, new_val, target)
        status = get_day_status(target)
        if status:
            text = format_today_message(status, target)
            page = int(ctx.user_data.get("page", 0))
            keyboard = task_list_keyboard(status["tasks"], date_iso, page=page)
            await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
        return

    # ── PAGE ──────────────────────────────────────────────────────────────────
    if action == "page":
        page = int(extra) if extra.isdigit() else 0
        ctx.user_data["page"] = page
        status = get_day_status(target)
        if status is None:
            await query.answer("Data nahi mila!", show_alert=True)
            return
        text = format_today_message(status, target)
        keyboard = task_list_keyboard(status["tasks"], date_iso, page=page)
        await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
        return

    # ── REFRESH ───────────────────────────────────────────────────────────────
    if action == "refresh":
        status = get_day_status(target)
        if status is None:
            await query.answer("Data nahi mila!", show_alert=True)
            return
        text = format_today_message(status, target)
        keyboard = task_list_keyboard(status["tasks"], date_iso, page=0)
        await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
        return

    # ── STATS shortcut ────────────────────────────────────────────────────────
    if action == "stats":
        from handlers.stats import _send_stats
        await _send_stats(query.message, query.from_user.id)
        return

    # ── YESTERDAY / TOMORROW navigation ──────────────────────────────────────
    if action in ("yesterday", "tomorrow"):
        offset = -1 if action == "yesterday" else 1
        nav_date = target + timedelta(days=offset)
        status = get_day_status(nav_date)
        if status is None:
            await query.answer("Us din ka data nahi mila!", show_alert=True)
            return
        text = format_today_message(status, nav_date)
        keyboard = task_list_keyboard(status["tasks"], nav_date.isoformat(), page=0)
        await query.edit_message_text(text, parse_mode="MarkdownV2", reply_markup=keyboard)
        return
