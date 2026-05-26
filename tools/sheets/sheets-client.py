#!/usr/bin/env python3
"""
Thin wrapper around gspread for the Cyvore GTM Weekly Sync workbook.

Sole edit surface for the Monday weekly customer sync (replaces the
deprecated `state/weekly-customer-sync.xlsx`). One Google Sheet, one tab per
week named `DD.MM.YYYY`. Tab schema is unchanged from the xlsx era — 8
columns: Tier | Company/Lead Name | Deal/Lead Stage | Status | Next Step |
Assignee | Done? | moving status.

Auth: service account credentials at `tools/sheets/google-sheets-credentials.json`
(gitignored). The Sheet ID + credentials path live in
`tools/sheets/google-sheets-config.json` (also gitignored). Sheet must be shared
with the service account email as Editor.

Imported by:
  - tools/sheets/generate-weekly-tab.py     (writes new Monday tab from HubSpot)
  - tools/sheets/read-weekly-sync.py        (reads tab JSON for the digest)
  - tools/email/send-digest.py              (CSV export + Sheet link for emails)
  - tools/sheets/migrate-xlsx-to-sheet.py   (one-time: xlsx history -> Sheet)

Usage as a module:
    from sheets_client import SheetsClient, EXPECTED_HEADERS
    sc = SheetsClient()                 # reads config
    sc.list_tabs()                      # ['10.05.2026', '17.05.2026', ...]
    sc.read_tab('17.05.2026')           # list[dict] keyed by EXPECTED_HEADERS
    sc.clone_tab('17.05.2026', '24.05.2026')
    sc.update_row_cells('24.05.2026', 5, [(3, 'Connected'), (4, 'met them')])
    sc.append_rows('24.05.2026', [['', 'Acme Corp', 'New', '', '', '', '', '']])
    sc.export_tab_csv('24.05.2026', '/tmp/weekly.csv')
    sc.tab_url('24.05.2026')

Usage as CLI (smoke tests; intentionally minimal):
    python3 tools/sheets/sheets-client.py info        # print Sheet URL + tabs
    python3 tools/sheets/sheets-client.py list        # list tabs (one per line)
    python3 tools/sheets/sheets-client.py read TAB    # dump tab as JSON
    python3 tools/sheets/sheets-client.py url TAB     # print URL pointing to that tab
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = REPO_ROOT / "tools" / "sheets" / "google-sheets-config.json"

EXPECTED_HEADERS = [
    "Tier",
    "Company/Lead Name",
    "Deal/Lead Stage",
    "Status",
    "Next Step",
    "Assignee",
    "Done?",
    "moving status",
]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _die(msg, code=2):
    sys.stderr.write(f"ERROR: {msg}\n")
    sys.exit(code)


def _import_gspread():
    """Defer import so the rest of the repo doesn't crash if gspread is unset
    up. Provide a precise install hint when it's missing."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        return gspread, Credentials
    except ImportError as e:
        _die(
            "Google Sheets dependencies are not installed. "
            "Run: pip install -r requirements.txt  (adds gspread + google-auth). "
            f"Underlying import error: {e}"
        )


class SheetsClient:
    """Thin convenience wrapper around gspread.Spreadsheet for the GTM weekly
    workbook. All methods raise on auth/network errors with a useful hint."""

    def __init__(self, config_path=None):
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG
        if not self.config_path.exists():
            _die(
                f"Missing {self.config_path}. Copy "
                "tools/sheets/google-sheets-config.template.json to that path, "
                "fill in your sheet_id, and ensure the service account "
                "credentials JSON is at the credentials_path."
            )
        cfg = json.loads(self.config_path.read_text(encoding="utf-8"))

        sheet_id = cfg.get("sheet_id")
        if not sheet_id:
            _die(f"{self.config_path} has no 'sheet_id'. Paste the ID from your Google Sheet URL.")

        creds_rel = cfg.get("credentials_path") or "tools/sheets/google-sheets-credentials.json"
        creds_path = Path(creds_rel)
        if not creds_path.is_absolute():
            creds_path = REPO_ROOT / creds_rel
        if not creds_path.exists():
            _die(
                f"Service account credentials not found at {creds_path}. "
                "Download the JSON key from Google Cloud Console -> IAM -> "
                "Service Accounts -> your service account -> Keys -> Add key."
            )

        gspread, Credentials = _import_gspread()
        creds = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
        self._gc = gspread.authorize(creds)
        self.sheet_id = sheet_id
        try:
            self._ss = self._gc.open_by_key(sheet_id)
        except Exception as e:
            cls = type(e).__name__
            _die(
                f"Could not open Sheet {sheet_id!r} ({cls}: {e}). "
                "Verify the Sheet exists and is shared with the service "
                "account email as Editor (the email is in your credentials "
                "JSON under 'client_email')."
            )
        self._ws_cache = {}

    @property
    def spreadsheet_title(self):
        return self._ss.title

    @property
    def spreadsheet_url(self):
        return self._ss.url

    def _ws(self, name):
        if name in self._ws_cache:
            return self._ws_cache[name]
        try:
            ws = self._ss.worksheet(name)
        except Exception as e:
            available = [w.title for w in self._ss.worksheets()]
            _die(f"Tab {name!r} not found. Available: {available}. ({e})")
        self._ws_cache[name] = ws
        return ws

    def list_tabs(self):
        """Return all worksheet titles in the spreadsheet, in the order they
        appear in the Sheets UI."""
        return [w.title for w in self._ss.worksheets()]

    def tab_exists(self, name):
        try:
            self._ss.worksheet(name)
            return True
        except Exception:
            return False

    def read_tab(self, name):
        """Read a tab and return list[dict] keyed by EXPECTED_HEADERS.
        Skips:
          - fully empty rows
          - section header rows (Company/Lead Name starts with 'PIPELINE:' or '---')
          - stage subheader rows (Company/Lead Name is the only filled cell)
        String values are stripped; empty -> None. Mirrors the openpyxl
        semantics of the legacy read-weekly-sync.read_tab."""
        ws = self._ws(name)
        values = ws.get_all_values()
        if not values:
            return []
        # Header row sanity check (warn but don't fail — manual edits happen)
        header = [c.strip() if isinstance(c, str) else c for c in values[0][: len(EXPECTED_HEADERS)]]
        if header != EXPECTED_HEADERS:
            sys.stderr.write(
                f"WARNING: tab {name!r} headers don't match expected. "
                f"Got: {header}. Expected: {EXPECTED_HEADERS}\n"
            )
        out = []
        # Indices of non-name columns; if all of these are empty AND name is
        # filled, the row is a section/stage marker and we skip it.
        non_name_cols = [i for i, h in enumerate(EXPECTED_HEADERS) if h != "Company/Lead Name"]
        for raw in values[1:]:
            cells = list(raw)[: len(EXPECTED_HEADERS)]
            cells += [None] * (len(EXPECTED_HEADERS) - len(cells))
            if all((c is None) or (isinstance(c, str) and c.strip() == "") for c in cells):
                continue
            name_value = cells[1] if len(cells) > 1 else None
            if isinstance(name_value, str):
                stripped = name_value.strip()
                if stripped.upper().startswith("PIPELINE:") or stripped.startswith("---"):
                    continue
            non_name_filled = any(
                (cells[i] is not None) and not (isinstance(cells[i], str) and cells[i].strip() == "")
                for i in non_name_cols
            )
            if not non_name_filled and name_value:
                # Section / stage marker (e.g. "  Connected" sub-header).
                continue
            rec = {}
            for i, h in enumerate(EXPECTED_HEADERS):
                v = cells[i]
                if isinstance(v, str):
                    v = v.strip()
                    if v == "":
                        v = None
                rec[h] = v
            out.append(rec)
        return out

    def read_tab_raw(self, name):
        """Return the full grid as list[list[str]], including the header row.
        Used by the migration script to copy tabs verbatim."""
        return self._ws(name).get_all_values()

    def clone_tab(self, source_name, new_name, force=False):
        """Server-side duplicate of source_name -> new_name. If new_name
        exists and force=False, raises. Returns the new worksheet's title."""
        source = self._ws(source_name)
        if self.tab_exists(new_name):
            if not force:
                _die(
                    f"Tab {new_name!r} already exists. Use force=True (or "
                    f"--force on the CLI) to overwrite."
                )
            self.delete_tab(new_name)

        self._ss.duplicate_sheet(
            source_sheet_id=source.id,
            new_sheet_name=new_name,
        )
        # Bust caches
        self._ws_cache.pop(new_name, None)
        return new_name

    def create_tab(self, name, rows=1000, cols=12):
        """Create a fresh empty tab with EXPECTED_HEADERS in row 1."""
        if self.tab_exists(name):
            _die(f"Tab {name!r} already exists; use clone_tab or delete_tab first.")
        ws = self._ss.add_worksheet(title=name, rows=rows, cols=cols)
        ws.update("A1", [EXPECTED_HEADERS])
        self._ws_cache[name] = ws
        return name

    def delete_tab(self, name):
        ws = self._ws(name)
        self._ss.del_worksheet(ws)
        self._ws_cache.pop(name, None)

    def write_full_tab(self, name, rows, with_header=True):
        """Replace all content of `name`. `rows` is list[dict] keyed by
        EXPECTED_HEADERS, OR list[list]. If with_header=True a header row is
        prepended automatically when rows are dicts."""
        ws = self._ws(name) if self.tab_exists(name) else self._ss.add_worksheet(
            title=name, rows=max(len(rows) + 5, 100), cols=max(len(EXPECTED_HEADERS), 12)
        )
        self._ws_cache[name] = ws

        body = []
        if rows and isinstance(rows[0], dict):
            if with_header:
                body.append(EXPECTED_HEADERS)
            for r in rows:
                body.append([_cell(r.get(h)) for h in EXPECTED_HEADERS])
        else:
            if with_header and (not rows or rows[0] != EXPECTED_HEADERS):
                body.append(EXPECTED_HEADERS)
            for r in rows or []:
                body.append([_cell(c) for c in r])

        ws.clear()
        if body:
            # gspread.update accepts a 2D values matrix anchored at A1
            ws.update("A1", body)

    def update_row_cells(self, name, row_idx, col_value_pairs):
        """Update specific cells in a single row. row_idx and column indices
        are 1-based to match Google Sheets convention. col_value_pairs is a
        list of (col_idx, value) tuples. Batched into one API call."""
        if not col_value_pairs:
            return
        ws = self._ws(name)
        data = [
            {"range": _a1(row_idx, col), "values": [[_cell(val)]]}
            for col, val in col_value_pairs
        ]
        ws.batch_update(data)

    def append_rows(self, name, rows, value_input_option="USER_ENTERED"):
        """Append rows to the end of `name`. `rows` is list[list]."""
        if not rows:
            return
        ws = self._ws(name)
        body = [[_cell(c) for c in r] for r in rows]
        ws.append_rows(body, value_input_option=value_input_option)

    def find_row_by_value(self, name, col_idx, value, case_insensitive=True):
        """Find the first 1-indexed row whose cell at col_idx equals value.
        Returns None if not found. Skips header (row 1)."""
        ws = self._ws(name)
        col_values = ws.col_values(col_idx)
        target = (value or "").strip()
        if case_insensitive:
            target = target.lower()
        for i, v in enumerate(col_values, start=1):
            if i == 1:
                continue
            v_norm = (v or "").strip()
            if case_insensitive:
                v_norm = v_norm.lower()
            if v_norm == target:
                return i
        return None

    def last_data_row(self, name):
        """Return the 1-indexed row number of the last non-empty row."""
        ws = self._ws(name)
        values = ws.get_all_values()
        for i in range(len(values), 0, -1):
            if any((c or "").strip() for c in values[i - 1]):
                return i
        return 1

    def export_tab_csv(self, name, out_path):
        """Write the tab's full content (including header) to a CSV file."""
        rows = self.read_tab_raw(name)
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for r in rows:
                w.writerow(r)
        return str(out)

    def tab_url(self, name):
        """Direct link to the specific tab in a browser."""
        ws = self._ws(name)
        return f"https://docs.google.com/spreadsheets/d/{self.sheet_id}/edit#gid={ws.id}"

    def tab_gid(self, name):
        """Numeric sheetId (gid) for a tab — needed by the raw batchUpdate API."""
        return self._ws(name).id

    def batch_update_format(self, name, formats, chunk_size=200):
        """Apply a list of cell-formatting requests in (chunked) batchUpdate calls.

        formats = [
            {
                # Range is 1-indexed inclusive on both ends.
                'range': {'start_row': N, 'end_row': N, 'start_col': M, 'end_col': M},
                'background': {'red': 0..1, 'green': 0..1, 'blue': 0..1},   # optional
                'foreground': {'red': 0..1, 'green': 0..1, 'blue': 0..1},   # optional (text color)
                'bold': True,                                                # optional
                'italic': True,                                              # optional
                'horizontal_alignment': 'LEFT' | 'CENTER' | 'RIGHT',         # optional
            },
            ...
        ]
        """
        if not formats:
            return
        sheet_gid = self._ws(name).id
        requests = []
        for f in formats:
            rng = f["range"]
            cell_format = {}
            if "background" in f:
                cell_format["backgroundColor"] = f["background"]
            text_format = {}
            if f.get("bold"):
                text_format["bold"] = True
            if f.get("italic"):
                text_format["italic"] = True
            if "foreground" in f:
                text_format["foregroundColor"] = f["foreground"]
            if text_format:
                cell_format["textFormat"] = text_format
            if "horizontal_alignment" in f:
                cell_format["horizontalAlignment"] = f["horizontal_alignment"]
            if not cell_format:
                continue
            field_keys = []
            if "backgroundColor" in cell_format:
                field_keys.append("backgroundColor")
            if "textFormat" in cell_format:
                field_keys.append("textFormat")
            if "horizontalAlignment" in cell_format:
                field_keys.append("horizontalAlignment")
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_gid,
                        "startRowIndex": rng["start_row"] - 1,
                        "endRowIndex": rng["end_row"],
                        "startColumnIndex": rng["start_col"] - 1,
                        "endColumnIndex": rng["end_col"],
                    },
                    "cell": {"userEnteredFormat": cell_format},
                    "fields": "userEnteredFormat(" + ",".join(field_keys) + ")",
                }
            })
        if not requests:
            return
        for i in range(0, len(requests), chunk_size):
            self._ss.batch_update({"requests": requests[i:i + chunk_size]})

    def apply_data_validations(self, name, validations, chunk_size=200):
        """Set ONE_OF_LIST data-validation rules (dropdowns) on cell ranges.

        validations = [
            {
                # 1-indexed inclusive range
                'range': {'start_row': 2, 'end_row': 76, 'start_col': 1, 'end_col': 1},
                'values': ['A', 'B'],         # dropdown options (strings)
                'strict': False,              # default: allow values outside the list
                'show_custom_ui': True,       # default: show the dropdown arrow
                'input_message': 'Pick A or B', # optional cell hint
            },
            ...
        ]
        Pass `values=None` to CLEAR existing validation on the range.
        """
        if not validations:
            return
        sheet_gid = self._ws(name).id
        requests = []
        for v in validations:
            rng = v["range"]
            api_range = {
                "sheetId": sheet_gid,
                "startRowIndex": rng["start_row"] - 1,
                "endRowIndex": rng["end_row"],
                "startColumnIndex": rng["start_col"] - 1,
                "endColumnIndex": rng["end_col"],
            }
            if v.get("values") is None:
                # Clear validation: setDataValidation with no rule.
                requests.append({"setDataValidation": {"range": api_range}})
                continue
            rule = {
                "condition": {
                    "type": "ONE_OF_LIST",
                    "values": [{"userEnteredValue": str(val)} for val in v["values"]],
                },
                "showCustomUi": v.get("show_custom_ui", True),
                "strict": v.get("strict", False),
            }
            if v.get("input_message"):
                rule["inputMessage"] = v["input_message"]
            requests.append({
                "setDataValidation": {"range": api_range, "rule": rule}
            })
        if not requests:
            return
        for i in range(0, len(requests), chunk_size):
            self._ss.batch_update({"requests": requests[i:i + chunk_size]})


def _cell(v):
    """Coerce a Python value into something gspread can write. None -> ''."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    return v if isinstance(v, (str, int, float)) else str(v)


def _a1(row, col):
    """Convert 1-indexed (row, col) -> A1 notation. col=1 -> 'A', col=27 -> 'AA'."""
    s = ""
    c = col
    while c > 0:
        c, rem = divmod(c - 1, 26)
        s = chr(65 + rem) + s
    return f"{s}{row}"


def _retry(fn, *args, attempts=4, base_delay=1.0, **kwargs):
    """Tiny retry helper for transient Sheets API rate-limit / 5xx errors.
    Used by the migration script to throttle through 31 historical tabs."""
    last = None
    for i in range(attempts):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last = e
            msg = str(e)
            if any(s in msg for s in ("429", "500", "502", "503", "504", "RATE_LIMIT")):
                time.sleep(base_delay * (2 ** i))
                continue
            raise
    raise last


def _cli_info(args):
    sc = SheetsClient(args.config)
    print(f"Title: {sc.spreadsheet_title}")
    print(f"URL:   {sc.spreadsheet_url}")
    print(f"Tabs ({len(sc.list_tabs())}):")
    for t in sc.list_tabs():
        print(f"  {t}")


def _cli_list(args):
    sc = SheetsClient(args.config)
    for t in sc.list_tabs():
        print(t)


def _cli_read(args):
    sc = SheetsClient(args.config)
    print(json.dumps(sc.read_tab(args.tab), indent=2, ensure_ascii=False))


def _cli_url(args):
    sc = SheetsClient(args.config)
    print(sc.tab_url(args.tab))


def main():
    p = argparse.ArgumentParser(description="Smoke tests for the Sheets client.")
    p.add_argument("--config", default=str(DEFAULT_CONFIG))
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("info").set_defaults(func=_cli_info)
    sub.add_parser("list").set_defaults(func=_cli_list)
    rd = sub.add_parser("read"); rd.add_argument("tab"); rd.set_defaults(func=_cli_read)
    u = sub.add_parser("url"); u.add_argument("tab"); u.set_defaults(func=_cli_url)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
