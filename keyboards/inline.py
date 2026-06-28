"""Inline keyboard factories for LifeOS."""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def task_action_keyboard(task_name: str, date_iso: str) -> InlineKeyboardMarkup:
    """Return Done / Skip / Snooze keyboard for a task."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Done",
                callback_data=f"done|{date_iso}|{task_name}",
            ),
            InlineKeyboardButton(
                "❌ Skip",
                callback_data=f"skip|{date_iso}|{task_name}",
            ),
            InlineKeyboardButton(
                "⏰ Snooze 15m",
                callback_data=f"snooze|{date_iso}|{task_name}",
            ),
        ]
    ])


def today_overview_keyboard(date_iso: str) -> InlineKeyboardMarkup:
    """Quick action buttons under the /today summary."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Stats",     callback_data=f"stats|{date_iso}"),
            InlineKeyboardButton("🔄 Refresh",   callback_data=f"refresh|{date_iso}"),
        ],
        [
            InlineKeyboardButton("⬅️ Yesterday", callback_data=f"yesterday|{date_iso}"),
            InlineKeyboardButton("➡️ Tomorrow",  callback_data=f"tomorrow|{date_iso}"),
        ],
    ])


def task_list_keyboard(
    tasks: dict[str, bool],
    date_iso: str,
    page: int = 0,
    page_size: int = 5,
) -> InlineKeyboardMarkup:
    """
    Paginated list of task buttons.
    Each button shows the current status and lets user toggle.
    """
    task_items = list(tasks.items())
    start = page * page_size
    chunk = task_items[start: start + page_size]

    rows = []
    for task, done in chunk:
        icon = "✅" if done else "☐"
        rows.append([
            InlineKeyboardButton(
                f"{icon} {task}",
                callback_data=f"toggle|{date_iso}|{task}",
            )
        ])

    # Navigation
    nav: list[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"page|{date_iso}|{page-1}"))
    total_pages = -(-len(task_items) // page_size)  # ceil
    if (page + 1) < total_pages:
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"page|{date_iso}|{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([
        InlineKeyboardButton("🏠 Today Overview", callback_data=f"refresh|{date_iso}"),
    ])
    return InlineKeyboardMarkup(rows)
