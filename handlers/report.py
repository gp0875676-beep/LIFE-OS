"""Handler: /report — weekly summary."""
from __future__ import annotations

import logging
from datetime import date, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from core.sheets import get_day_status, get_month_completion
from utils.formatting import escape_md

logger = logging.getLogger(__name__)


async def report_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    today = date.today()
    week_start = today - timedelta(days=6)

    lines = [
        "📋 *Weekly Report*",
        f"_{escape_md(week_start.strftime('%d %b'))} — {escape_md(today.strftime('%d %b %Y'))}_",
        "",
    ]

    task_totals: dict[str, int] = {}
    task_done:   dict[str, int] = {}
    pcts: list[float] = []

    for offset in range(7):
        d = week_start + timedelta(days=offset)
        status = get_day_status(d)
        if status is None:
            continue
        pcts.append(status["completion_pct"])
        for task, done in status["tasks"].items():
            task_totals[task] = task_totals.get(task, 0) + 1
            if done:
                task_done[task] = task_done.get(task, 0) + 1

    avg = round(sum(pcts) / len(pcts), 1) if pcts else 0.0
    lines.append(f"📈 Avg Completion: *{escape_md(str(avg))}%*")
    lines.append(f"📅 Month so far: *{escape_md(str(get_month_completion()))}%*")
    lines.append("")

    if task_done:
        best  = max(task_done, key=lambda t: task_done[t] / max(task_totals[t], 1))
        worst = min(
            task_totals,
            key=lambda t: task_done.get(t, 0) / max(task_totals[t], 1),
        )
        best_pct  = round(task_done.get(best, 0) / max(task_totals.get(best, 1), 1) * 100)
        worst_pct = round(task_done.get(worst, 0) / max(task_totals.get(worst, 1), 1) * 100)
        lines += [
            f"🏆 Best habit: {escape_md(best)} \\({best_pct}%\\)",
            f"⚠️ Needs work: {escape_md(worst)} \\({worst_pct}%\\)",
            "",
        ]

    lines.append("*Day\\-by\\-Day:*")
    for offset in range(7):
        d = week_start + timedelta(days=offset)
        status = get_day_status(d)
        day_name = d.strftime("%a")
        if status:
            bar_filled = int(status["completion_pct"] / 20)
            bar = "█" * bar_filled + "░" * (5 - bar_filled)
            lines.append(f"{escape_md(day_name)}: `{bar}` {escape_md(str(status['completion_pct']))}%")
        else:
            lines.append(f"{escape_md(day_name)}: _no data_")

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")
