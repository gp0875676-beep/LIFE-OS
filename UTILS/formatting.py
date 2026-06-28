"""Message formatting helpers for LifeOS."""
from __future__ import annotations

import re
from datetime import date
from typing import Any


def escape_md(text: str) -> str:
    """Escape all MarkdownV2 special characters."""
    return re.sub(r"([_*\[\]()~`>#+\-=|{}.!\\])", r"\\\1", str(text))


def format_today_message(status: dict[str, Any], for_date: date) -> str:
    """Build the /today task overview message."""
    tasks: dict[str, bool] = status["tasks"]
    pct: float = status["completion_pct"]
    done_count = sum(tasks.values())
    total = len(tasks)

    day_name = for_date.strftime("%A")
    date_str = for_date.strftime("%d %b %Y")

    bar_filled = int(pct / 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)

    lines = [
        f"📅 *{escape_md(day_name)}, {escape_md(date_str)}*",
        "",
        f"Progress: `{bar}` {escape_md(str(pct))}%",
        f"✅ {done_count}/{total} tasks done",
        "",
        "*── Tasks ──*",
    ]

    for task, done in tasks.items():
        icon = "✅" if done else "☐"
        lines.append(f"{icon} {escape_md(task)}")

    lines.extend(["", "_Tap a task below to mark it:_"])
    return "\n".join(lines)


def format_stats_message(
    today_pct: float,
    week_pct: float,
    month_pct: float,
    streaks: dict[str, dict[str, int]],
    measurements: dict[str, str],
) -> str:
    """Build the /stats dashboard message."""
    def _bar(pct: float) -> str:
        filled = int(pct / 10)
        return "█" * filled + "░" * (10 - filled)

    lines = [
        "📊 *LifeOS Dashboard*",
        "",
        f"*Today:*    `{_bar(today_pct)}` {escape_md(str(today_pct))}%",
        f"*This Week:* `{_bar(week_pct)}` {escape_md(str(week_pct))}%",
        f"*This Month:* `{_bar(month_pct)}` {escape_md(str(month_pct))}%",
        "",
        "*── Streaks 🔥 ──*",
    ]

    streak_emoji = {
        "Workout (M/W/F)":   "🏋️",
        "Drink 500ml Water":  "💧",
        "Yoga":               "🧘",
        "Crypto Study":       "📈",
        "Sleep by 10:30 PM":  "🌙",
        "Evening Walk":       "🚶",
    }

    if streaks:
        for task, data in streaks.items():
            emoji = streak_emoji.get(task, "⚡")
            cur = data.get("current", 0)
            lon = data.get("longest", 0)
            lines.append(
                f"{emoji} {escape_md(task)}: *{cur}d* current \\| {escape_md(str(lon))}d best"
            )
    else:
        lines.append("_No streak data yet_")

    if measurements:
        lines.extend(["", "*── Body Stats 💪 ──*"])
        show_keys = ["Weight (kg)", "Waist (cm)", "Chest (cm)", "BMI"]
        for k in show_keys:
            if k in measurements:
                lines.append(f"• {escape_md(k)}: {escape_md(measurements[k])}")

    return "\n".join(lines)


def format_reminder_message(task: str) -> str:
    emoji_map = {
        "Wake Up":               "🌅",
        "Drink 500ml Water":     "💧",
        "Yoga":                  "🧘",
        "Workout (M/W/F)":       "🏋️",
        "Breakfast":             "🍳",
        "Lunch":                 "🍱",
        "Dinner":                "🍽️",
        "Crypto Study":          "📈",
        "Sleep by 10:30 PM":     "🌙",
        "Evening Walk":          "🚶",
    }
    emoji = emoji_map.get(task, "⏰")
    return (
        f"{emoji} *Reminder:* {escape_md(task)}\n"
        f"_Ab karo isko\\! /today_"
    )
