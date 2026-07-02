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
    # Alag-alag date formats ko handle karne ke liye
    for fmt in ("%d-%b", "%d-%b-%y", "%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            d = datetime.strptime(cell, fmt).date()
            if d.year == 1900:
                d = d.replace(year=2026)
            return d
        except ValueError:
            continue
    return None


def _find_row(ws: gspread.Worksheet, target: date) -> Optional[int]:
    try:
        all_vals = ws.col_values(1)  # Column A scan kar raha hai
        for idx, cell in enumerate(all_vals):
            parsed = _parse_date(cell)
            if parsed and parsed == target:
                found_row = idx + 1
                logger.info("Found date %s at row %d", target, found_row)
                return found_row
        logger.warning("Date %s not found in Column A. Sample: %s", target, all_vals[:5])
        return None
    except Exception as e:
        logger.error("Error scanning Column A: %s", e)
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
        logger.error("Error fetching row values: %s", exc)
        return None

    while len(row_data) < 26:
        row_data.append("")

    task_status: dict[str, bool] = {}
    for i, task_name in enumerate(TASKS):
        col_idx = 3 + i  # Column D se shuru (index 3)
        raw = row_data[col_idx] if col_idx < len(row_data) else ""
        task_status[task_name] = str(raw).upper() in ("TRUE", "1", "YES", "✓")

    done_count = sum(task_status.values())
    total = len(TASKS)
    pct = round((done_count / total) * 100, 1) if total > 0 else 0.0

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
        logger.info("Marked %s=%s on %s row=%d", task_name, value, target, row)
        return True
    except APIError as exc:
        logger.error("Sheets API error: %s", exc)
        return False


def get_week_completion() -> float:
    return 0.0


def get_month_completion(target_month: Optional[int] = None) -> float:
    return 0.0


def get_streaks() -> dict[str, int]:
    return {}


def get_body_measurements() -> dict[str, str]:
    return {}
