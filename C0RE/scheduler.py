"""APScheduler setup — daily reminders + snooze polling."""
from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot

from config import ADMIN_CHAT_ID, QUOTES, REMINDERS, TZ
from core.streak import pop_due_snoozes

logger = logging.getLogger(__name__)


async def _send_reminder(bot: Bot, task: str) -> None:
    emoji_map = {
        "Wake Up":               "🌅",
        "Drink 500ml Water":     "💧",
        "Warm Up":               "🏃",
        "Yoga":                  "🧘",
        "Surya Namaskar & Pranayama": "☀️",
        "Breakfast":             "🍳",
        "Lunch":                 "🍱",
        "Water Reminder":        "💦",
        "Healthy Snack":         "🍎",
        "Evening Walk":          "🚶",
        "Workout (M/W/F)":       "🏋️",
        "Dinner":                "🍽️",
        "Crypto Study":          "📈",
        "Sleep by 10:30 PM":     "🌙",
    }
    emoji = emoji_map.get(task, "⏰")
    text = (
        f"{emoji} *{task}* ka time ho gaya bhai\\!\n\n"
        f"Apna task mark karo 👇\n"
        f"/today"
    )
    try:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=text,
            parse_mode="MarkdownV2",
        )
    except Exception as exc:
        logger.error("Reminder send failed (%s): %s", task, exc)


async def _morning_motivation(bot: Bot) -> None:
    quote = random.choice(QUOTES)
    text = f"🌄 *Good Morning\\!* \n\n{_escape(quote)}\n\n/today karke shuru karo 💪"
    try:
        await bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=text,
            parse_mode="MarkdownV2",
        )
    except Exception as exc:
        logger.error("Morning motivation failed: %s", exc)


async def _check_snoozes(bot: Bot) -> None:
    now_str = datetime.now(tz=TZ).isoformat(timespec="minutes")
    due = pop_due_snoozes(now_str)
    for item in due:
        await _send_reminder(bot, item["task"])


def _escape(text: str) -> str:
    """Escape special chars for MarkdownV2."""
    for ch in r"_*[]()~`>#+-=|{}.!\\":
        text = text.replace(ch, f"\\{ch}")
    return text


def build_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Create and return a configured scheduler (not yet started)."""
    scheduler = AsyncIOScheduler(timezone=TZ)

    # Morning motivation at 6:00 AM
    scheduler.add_job(
        _morning_motivation,
        CronTrigger(hour=6, minute=0, timezone=TZ),
        args=[bot],
        id="morning_motivation",
        replace_existing=True,
    )

    # Daily task reminders
    for hour, minute, task in REMINDERS:
        job_id = f"reminder_{task.replace(' ', '_')}_{hour}_{minute}"
        scheduler.add_job(
            _send_reminder,
            CronTrigger(hour=hour, minute=minute, timezone=TZ),
            args=[bot, task],
            id=job_id,
            replace_existing=True,
        )

    # Poll snoozes every 5 minutes
    scheduler.add_job(
        _check_snoozes,
        "interval",
        minutes=5,
        args=[bot],
        id="snooze_poll",
        replace_existing=True,
    )

    logger.info("Scheduler built with %d jobs.", len(scheduler.get_jobs()))
    return scheduler
