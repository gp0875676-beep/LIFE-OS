"""Google Sheets integration — read & write daily task data."""
from __future__ import annotations

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
    STREAK_TASKS,
)

logger = logging.getLogger(__name__)


def _get_client() -> gspread.Client:
    creds = Credentials.from_service_account_file(GOOGLE_CREDS_JSON, scopes=SCOPES)
    return gspread.authorize(creds)


def _open_spreadsheet() -> gspread.Spreadsheet:
    return _get_client().open_by_key(SPREADSHEET_ID)


def _month_sheet(target: date) -> Optional[gspread.Worksheet]:
    sheet_name = MONTH_SHEETS.get(target.month)
    if not sheet_name:
        return None
    try:
        return _open_spreadsheet().worksheet(sheet_name)
    except Exception as exc:
        logger.error("Sheet open error: %s", exc)
        return None


def _parse_date(cell: str) -> Optional[date]:
    cell = str(cell).strip()
    if not cell:
        return None
    for fmt in ("%d-%b", "%d-%b-%y", "%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            d = datetime.strptime(cell, fmt).date()
            if d.year == 1900:
                d = d.replace(year=2026)
            return d
        except ValueError:
            continue
    return None


def _find_row(ws: gspread.Worksheet, target: date) -> Optional[int]:
    """Scan column B for date — col A has merged title cell."""
    try:
        col_b = ws.col_values(2)  # Column B = dates like '01-Jul'
        logger.info("Col B sample: %s", col_b[:6])
        for idx, cell in enumerate(col_b):
            parsed = _parse_date(cell)
            if parsed and parsed == target:
                found_row = idx + 1
                logger.info("Found date %s at row %d", target, found_row)
                return found_row
        logger.warning("Date %s not found in Col B. Sample: %s", target, col_b[:6])
        return None
    except Exception as exc:
        logger.error("Error scanning Col B: %s", exc)
        return None


def get_day_status(target: date) -> Optional[dict[str, Any]]:
    ws = _month_sheet(target)
    if ws is None:
        return None
    row = _find_row(ws, target)
    if row is None:
        return None

    try:
        row_data: list[Any] = ws.row_values(row)
    except Exception as exc:
        logger.error("Error fetching row: %s", exc)
        return None

    while len(row_data) < 26:
        row_data.append("")

    task_status: dict[str, bool] = {}
    for i, task_name in enumerate(TASKS):
        col_idx = 3 + i
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

    col_letter = chr(ord("D") + task_idx)

    try:
        ws.update_acell(f"{col_letter}{row}", str(value).upper())
        row_data = ws.row_values(row)
        while len(row_data) < 26:
            row_data.append("")
        done = sum(
            1 for i in range(len(TASKS))
            if str(row_data[3 + i] if 3 + i < len(row_data) else "").upper()
            in ("TRUE", "1", "YES", "✓")
        )
        pct = round((done / len(TASKS)) * 100, 1)
        ws.update_acell(f"W{row}", pct)
        logger.info("Marked %s=%s row=%d PCT=%.1f%%", task_name, value, row, pct)
        return True
    except APIError as exc:
        logger.error("Sheets API error: %s", exc)
        return False


def get_week_completion() -> float:
    today = date.today()
    ws = _month_sheet(today)
    if ws is None:
        return 0.0
    col_b = ws.col_values(2)
    col_w = ws.col_values(23)
    totals: list[float] = []
    for raw_date, raw_pct in zip(col_b, col_w):
        d = _parse_date(raw_date)
        if not d or not raw_pct:
            continue
        if 0 <= (today - d).days <= 6:
            try:
                totals.append(float(str(raw_pct).replace("%", "")))
            except ValueError:
                pass
    return round(sum(totals) / len(totals), 1) if totals else 0.0


def get_month_completion(target_month: Optional[int] = None) -> float:
    today = date.today()
    month = target_month or today.month
    target_date = today.replace(month=month, day=1)
    ws = _month_sheet(target_date)
    if ws is None:
        return 0.0
    col_w = ws.col_values(23)
    values = []
    for v in col_w[1:]:
        try:
            values.append(float(str(v).replace("%", "")))
        except (ValueError, TypeError):
            pass
    return round(sum(values) / len(values), 1) if values else 0.0


def get_streaks() -> dict[str, int]:
    today = date.today()
    ws = _month_sheet(today)
    if ws is None:
        return {}
    col_b    = ws.col_values(2)
    all_rows = ws.get_all_values()
    dated_rows: list[tuple[date, list[str]]] = []
    for idx, cell in enumerate(col_b):
        d = _parse_date(cell)
        if d and d <= today and idx < len(all_rows):
            dated_rows.append((d, all_rows[idx]))
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


def get_body_measurements() -> dict[str, str]:
    try:
        ws = _open_spreadsheet().worksheet("Body Measurements")
    except Exception:
        return {}
    all_rows = ws.get_all_values()
    if len(all_rows) < 8:
        return {}
    header = all_rows[6]
    latest: dict[str, str] = {}
    for row in all_rows[7:]:
        for i, val in enumerate(row):
            if val and i < len(header) and header[i]:
                latest[header[i]] = val
    return latest
