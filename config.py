"""LifeOS Configuration — all constants and environment loading."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

TZ = ZoneInfo("Asia/Kolkata")

# ── Sheet column mapping (1-indexed for gspread, 0-indexed for list ops) ──────
# Row 3 is the header row in every Month sheet; data starts at row 4.
MONTH_HEADER_ROW = 3
MONTH_DATA_START_ROW = 4

# Column letter → task name (exactly as in the sheet header row)
TASK_COLUMNS: dict[str, str] = {
    "D": "Wake Up",
    "E": "Drink 500ml Water",
    "F": "Warm Up",
    "G": "Yoga",
    "H": "Surya Namaskar",
    "I": "Pranayama",
    "J": "Bath",
    "K": "Breakfast",
    "L": "Temple",
    "M": "Office",
    "N": "Lunch",
    "O": "Water Reminder",
    "P": "Healthy Snack",
    "Q": "Evening Walk",
    "R": "Workout (M/W/F)",
    "S": "Dinner",
    "T": "Crypto Study",
    "U": "Global News",
    "V": "Sleep by 10:30 PM",
}

# Column indices (0-based within the sheet row list)
COL_DATE = 1        # B
COL_DAY  = 2        # C
TASK_COL_START = 3  # D  (first task column, 0-based)
TASK_COL_END   = 21 # V  (inclusive, 0-based)
COL_COMP_PCT   = 22 # W
COL_MOOD       = 23 # X
COL_ENERGY     = 24 # Y
COL_NOTES      = 25 # Z

# Ordered task list (same order as columns D→V)
TASKS: list[str] = list(TASK_COLUMNS.values())

# Tasks to show in the daily message (subset — important ones)
DAILY_TASKS: list[str] = [
    "Wake Up",
    "Drink 500ml Water",
    "Warm Up",
    "Yoga",
    "Surya Namaskar",
    "Pranayama",
    "Bath",
    "Breakfast",
    "Temple",
    "Lunch",
    "Water Reminder",
    "Healthy Snack",
    "Evening Walk",
    "Workout (M/W/F)",
    "Dinner",
    "Crypto Study",
    "Global News",
    "Sleep by 10:30 PM",
]

# Month sheet mapping: month number → sheet name
MONTH_SHEETS: dict[int, str] = {
    7:  "Month 1",   # July
    8:  "Month 2",   # August
    9:  "Month 3",   # September
    10: "Month 4",   # October
    11: "Month 5",   # November
    12: "Month 6",   # December
}

# ── Reminders (IST 24h) ───────────────────────────────────────────────────────
REMINDERS: list[tuple[int, int, str]] = [
    (6,  30, "Wake Up"),
    (6,  35, "Drink 500ml Water"),
    (6,  40, "Warm Up"),
    (6,  50, "Yoga"),
    (7,  10, "Surya Namaskar & Pranayama"),
    (8,   0, "Breakfast"),
    (13,  0, "Lunch"),
    (15, 30, "Water Reminder"),
    (18, 45, "Healthy Snack"),
    (19,  0, "Evening Walk"),
    (19, 30, "Workout (M/W/F)"),
    (20,  0, "Dinner"),
    (20, 45, "Crypto Study"),
    (22, 30, "Sleep by 10:30 PM"),
]

# ── Streak tasks ──────────────────────────────────────────────────────────────
STREAK_TASKS: list[str] = [
    "Workout (M/W/F)",
    "Drink 500ml Water",
    "Yoga",
    "Crypto Study",
    "Sleep by 10:30 PM",
    "Evening Walk",
]

# ── Motivational quotes ───────────────────────────────────────────────────────
QUOTES: list[str] = [
    "🌅 Subah ka pehla qadam aaj ka sabse bada faisla hai — uth ja!",
    "💪 Discipline beats motivation — har roz, bina excuse ke.",
    "🔥 Jo aaj uthega, woh kal sab se aage hoga.",
    "🧘 Yoga karo, paani piyo, crypto padho — ek din mein poori duniya badlo.",
    "⚡ Small wins, every day — yahi bada badlav laata hai.",
    "🌟 Streak mat todna — teri mehnat ka sabse bada reward hai consistency.",
    "🏋️ Workout skip karna easy hai. Regret feel karna zyada tough — choose wisely.",
    "📈 Crypto seekhna investing hai khud mein — koi aur nahi karega teri care.",
    "💧 Paani hi life hai — 8 glass, no excuse.",
    "🌙 10:30 pe so ja — neend hi teri superpower hai.",
]

# ── Environment ───────────────────────────────────────────────────────────────
BOT_TOKEN: str        = os.environ["BOT_TOKEN"]
SPREADSHEET_ID: str   = os.environ["SPREADSHEET_ID"]
ADMIN_CHAT_ID: int    = int(os.environ["ADMIN_CHAT_ID"])
GOOGLE_CREDS_JSON: str = os.environ.get("GOOGLE_CREDS_JSON", "credentials.json")

SCOPES: list[str] = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
