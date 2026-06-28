"""Google Sheets integration — read & write daily task data."""
from __future__ import annotations

import json
import logging
from datetime import date, datetime
from typing import Any, Optional

import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError

from config import (
    GOOGLE_CREDS_JSON,
    MONTH_DATA_START_ROW,
    MONTH_SHEETS,
    SCOPES,
    SPREADSHEET_ID,
    TASKS,
    COL_COMP_PCT,
    TZ,
)

logger = logging.getLogger(__name__)


def _get_client() -> gspread.Client:
    """Return an authorised gspread client."""
    creds = Credentials.from_service_account_file(GOOGLE_CREDS_JSON, scopes=SCOPES)
    return gspread.authorize(creds)


def _open_spreadsheet() -> gspread.Spreadsheet:
    return _get_client().open_by_key(SPREADSHEET_ID)


def _month_sheet(target: date) -> Optional[gspread.Worksheet]:
    """Return the correct Month worksheet for a given date."""
    sheet_name = MONTH_SHEETS.get(target.month)
    if not sheet_name:
        return None
    try:
        return _open_spreadsheet().worksheet(sheet_name)
    except Exception as exc:
        logger.error("Sheet open error: %s", exc)
        return None


def _find_row(ws: gspread.Worksheet, target: date) -> Optional[int]:
    """Return 1-based row index for the given date. Searches column B."""
    col_b = ws.col_values(2)  # column B = Date
    for idx, cell in enumerate(col_b):
        if not cell:
            continue
        try:
            parsed = datetime.strptime(str(cell).split("T")[0][:10], "%Y-%m-%d").date()
        except ValueError:
            try:
                parsed = datetime.strptime(cell, "%d/%m/%Y").date()
            except ValueError:
                continue
        if parsed == target:
            return idx + 1  # gspread rows are 1-indexed
    return None


def get_day_status(target: date) -> Optional[dict[str, Any]]:
    """
    Fetch task completion status for *target* date.

    Returns dict:
        {
          "date": date,
          "tasks": {"Task Name": True/False, ...},
          "completion_pct": float,
          "row": int,
          "sheet_name": str,
        }
    or None if not found.
    """
    ws = _month_sheet(target)
    if ws is None:
        return None
    row = _find_row(ws, target)
    if row is None:
        logger.warning("Date %s not found in sheet.", target)
        return None

    row_data: list[Any] = ws.row_values(row)
    # Pad row if shorter than expected
    while len(row_data) < 26:
        row_data.append("")

    task_status: dict[str, bool] = {}
    for i, task_name in enumerate(TASKS):
        col_idx = 3 + i  # D=3 (0-based in list)
        raw = row_data[col_idx] if col_idx < len(row_data) else ""
        task_status[task_name] = str(raw).upper() in ("TRUE", "1", "YES", "✓")

    done_count = sum(task_status.values())
    total = len(TASKS)
    pct = round((done_count / total) * 100, 1)

    return {
        "date": target,
        "tasks": task_status,
        "completion_pct": pct,
        "row": row,
        "sheet_name": MONTH_SHEETS.get(target.month, ""),
    }


def mark_task(target: date, task_name: str, value: bool) -> bool:
    """
    Set a task checkbox to *value* and update the completion % column.

    Returns True on success.
    """
    ws = _month_sheet(target)
    if ws is None:
        return False
    row = _find_row(ws, target)
    if row is None:
        return False

    try:
        task_idx = TASKS.index(task_name)
    except ValueError:
        logger.error("Unknown task: %s", task_name)
        return False

    col_letter = chr(ord("D") + task_idx)          # D, E, F …
    comp_col   = chr(ord("A") + COL_COMP_PCT)       # W

    try:
        ws.update_acell(f"{col_letter}{row}", str(value).upper())

        # Recalculate completion % client-side and write it
        row_data = ws.row_values(row)
        while len(row_data) < 26:
            row_data.append("")
        done = sum(
            1 for i in range(len(TASKS))
            if str(row_data[3 + i] if 3 + i < len(row_data) else "").upper()
            in ("TRUE", "1", "YES", "✓")
        )
        pct = round((done / len(TASKS)) * 100, 1)
        ws.update_acell(f"{comp_col}{row}", pct)
        logger.info("Marked %s=%s on %s (row %d). PCT=%.1f", task_name, value, target, row, pct)
        return True
    except APIError as exc:
        logger.error("Sheets API error: %s", exc)
        return False


def get_week_completion() -> float:
    """Average completion % for the past 7 days (current month only)."""
    today = date.today()
    ws = _month_sheet(today)
    if ws is None:
        return 0.0

    totals: list[float] = []
    col_w = ws.col_values(23)  # column W = Comp %
    dates_col = ws.col_values(2)  # column B = Date
    for raw_date, raw_pct in zip(dates_col[MONTH_DATA_START_ROW - 1:], col_w[MONTH_DATA_START_ROW - 1:]):
        if not raw_date or not raw_pct:
            continue
        try:
            d = datetime.strptime(str(raw_date).split("T")[0][:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        if (today - d).days > 6:
            continue
        try:
            totals.append(float(raw_pct))
        except ValueError:
            pass

    return round(sum(totals) / len(totals), 1) if totals else 0.0


def get_month_completion(target_month: Optional[int] = None) -> float:
    """Average completion % for the given month (default: current)."""
    today = date.today()
    month = target_month or today.month
    target_date = today.replace(month=month, day=1)
    ws = _month_sheet(target_date)
    if ws is None:
        return 0.0

    col_w = ws.col_values(23)
    values = []
    for v in col_w[MONTH_DATA_START_ROW - 1:]:
        try:
            values.append(float(v))
        except (ValueError, TypeError):
            pass
    return round(sum(values) / len(values), 1) if values else 0.0


def get_streaks() -> dict[str, int]:
    """
    Calculate current consecutive streaks for STREAK_TASKS.
    Returns {"Task Name": streak_count, ...}
    """
    from config import STREAK_TASKS, TASKS

    today = date.today()
    ws = _month_sheet(today)
    if ws is None:
        return {}

    dates_col = ws.col_values(2)[MONTH_DATA_START_ROW - 1:]
    all_rows = ws.get_all_values()[MONTH_DATA_START_ROW - 1:]

    # Build sorted list of (date, row_list)
    dated_rows: list[tuple[date, list[str]]] = []
    for raw_date, row in zip(dates_col, all_rows):
        if not raw_date:
            continue
        try:
            d = datetime.strptime(str(raw_date).split("T")[0][:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        if d <= today:
            dated_rows.append((d, row))

    dated_rows.sort(key=lambda x: x[0], reverse=True)

    streaks: dict[str, int] = {}
    for task in STREAK_TASKS:
        try:
            t_idx = TASKS.index(task)
        except ValueError:
            continue
        col = 3 + t_idx
        streak = 0
        prev_date: Optional[date] = None
        for d, row in dated_rows:
            if prev_date and (prev_date - d).days != 1:
                break
            val = str(row[col] if col < len(row) else "").upper()
            if val in ("TRUE", "1", "YES", "✓"):
                streak += 1
                prev_date = d
            else:
                break
        streaks[task] = streak

    return streaks


def get_crypto_tracker_today() -> dict[str, Any]:
    """Fetch today's row from Crypto Tracker sheet."""
    today = date.today()
    try:
        ws = _open_spreadsheet().worksheet("Crypto Tracker")
    except Exception:
        return {}

    dates_col = ws.col_values(2)
    for idx, cell in enumerate(dates_col):
        if not cell:
            continue
        try:
            d = datetime.strptime(str(cell).split("T")[0][:10], "%Y-%m-%d").date()
        except ValueError:
            continue
        if d == today:
            row = ws.row_values(idx + 1)
            while len(row) < 11:
                row.append("")
            return {
                "news":       str(row[3]).upper() in ("TRUE", "1"),
                "btc":        str(row[4]).upper() in ("TRUE", "1"),
                "eth":        str(row[5]).upper() in ("TRUE", "1"),
                "altcoin":    str(row[6]).upper() in ("TRUE", "1"),
                "journal":    str(row[7]).upper() in ("TRUE", "1"),
                "sentiment":  row[8] or "—",
                "hours":      row[9] or "0",
            }
    return {}


def get_body_measurements() -> dict[str, str]:
    """Return latest non-empty measurements from Body Measurements sheet."""
    try:
        ws = _open_spreadsheet().worksheet("Body Measurements")
    except Exception:
        return {}

    all_rows = ws.get_all_values()
    # Header is row 7 (index 6); data from row 8
    if len(all_rows) < 8:
        return {}

    header = all_rows[6]  # row 7
    latest: dict[str, str] = {}
    for row in all_rows[7:]:
        for i, val in enumerate(row):
            if val and i < len(header) and header[i]:
                latest[header[i]] = val

    return latest
