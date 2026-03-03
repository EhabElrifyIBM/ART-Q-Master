"""
Reach Rate Calculator Engine
============================
Pure-logic module — no UI dependencies.

Usage:
    from ReachRateCalculator import ReachRateCalculator
    calc = ReachRateCalculator(log_fn=my_log)
    calc.load_files(pa_path, sms_path, email_path, phone_path)
    calc.run(output_path, start_date=None, end_date=None)
"""

import pandas as pd
import xlsxwriter
import os
from datetime import datetime, date
from typing import Optional, Callable

# ── Constants ──────────────────────────────────────────────────────────────────

REACHED_ACTIONS = {
    "fixed", "issue not fixed", "not yet tested", "escalation", "dnd",
    "not yet tested"
}
NOT_REACHED_ACTIONS = {
    "sent sms", "sent email", "left vm", "reviewed",
    "bank/sutherland", "not reached"
}

ALL_FINAL_ACTIONS = [
    "Fixed", "Refused Callback", "Issue Not Fixed", "Not yet Tested",
    "Escalation", "Sent SMS", "Sent Email", "Left VM", "Reviewed",
    "Bank/Sutherland", "Not Reached", "DND"
]

# ── Column name helpers ────────────────────────────────────────────────────────

def _find_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    """Return the first column name that matches (case-insensitive)."""
    lower_map = {c.lower().strip(): c for c in df.columns}
    for cand in candidates:
        matched = lower_map.get(cand.lower().strip())
        if matched:
            return matched
    return None


def _normalize_case_num(val) -> str:
    if pd.isna(val):
        return ""
    return str(val).strip()


# ── Main Class ─────────────────────────────────────────────────────────────────

class ReachRateCalculator:

    def __init__(self, log_fn: Optional[Callable] = None):
        """
        Args:
            log_fn: Callable(message: str, level: str) used for progress logging.
                    Levels: INFO, SUCCESS, WARNING, ERROR
        """
        self.log_fn = log_fn or (lambda msg, lvl="INFO": print(f"[{lvl}] {msg}"))
        self.pa_df: Optional[pd.DataFrame] = None
        self.sms_df: Optional[pd.DataFrame] = None
        self.email_df: Optional[pd.DataFrame] = None
        self.phone_df: Optional[pd.DataFrame] = None

    # ── Logging shortcuts ──────────────────────────────────────────────────────

    def _log(self, msg: str, level: str = "INFO"):
        try:
            self.log_fn(msg, level)
        except Exception:
            pass

    # ── File Loading ───────────────────────────────────────────────────────────

    def load_files(self, pa_path: str, sms_path: str, email_path: str, phone_path: str):
        """Load the 4 required Excel sheets into DataFrames."""
        self._log("Loading PA Cases sheet…")
        self.pa_df = self._load_sheet(pa_path, sheet_hint="PA Cases")
        self._log(f"  ✓ PA Cases: {len(self.pa_df)} rows | {list(self.pa_df.columns[:5])}…", "SUCCESS")

        self._log("Loading SMS View sheet…")
        self.sms_df = self._load_sheet(sms_path, sheet_hint="SMS")
        self._log(f"  ✓ SMS:      {len(self.sms_df)} rows", "SUCCESS")

        self._log("Loading Email View sheet…")
        self.email_df = self._load_sheet(email_path, sheet_hint="Email")
        self._log(f"  ✓ Email:    {len(self.email_df)} rows", "SUCCESS")

        self._log("Loading Phone Call View sheet…")
        self.phone_df = self._load_sheet(phone_path, sheet_hint="Phone")
        self._log(f"  ✓ Phone:    {len(self.phone_df)} rows", "SUCCESS")

    def _load_sheet(self, path: str, sheet_hint: str = "") -> pd.DataFrame:
        """
        Try to load an Excel file.  If it has multiple sheets, pick the one
        whose name best matches sheet_hint; otherwise load the first sheet.
        """
        xl = pd.ExcelFile(path)
        if len(xl.sheet_names) == 1:
            return pd.read_excel(xl, sheet_name=xl.sheet_names[0], dtype=str)

        # Find best matching sheet
        hint_lower = sheet_hint.lower()
        for name in xl.sheet_names:
            if hint_lower in name.lower():
                self._log(f"  → Using sheet '{name}' from {os.path.basename(path)}")
                return pd.read_excel(xl, sheet_name=name, dtype=str)

        self._log(f"  → No sheet matched '{sheet_hint}'; using first sheet '{xl.sheet_names[0]}'", "WARNING")
        return pd.read_excel(xl, sheet_name=xl.sheet_names[0], dtype=str)

    # ── Core Processing ────────────────────────────────────────────────────────

    def run(
        self,
        output_path: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> str:
        """
        Run the full calculation and write the output Excel file.

        Args:
            output_path: Full path for the output .xlsx file.
            start_date:  Start of date range filter (inclusive), or None for all.
            end_date:    End of date range filter (inclusive), or None for all.

        Returns:
            output_path on success.
        """
        if self.pa_df is None:
            raise RuntimeError("Files not loaded — call load_files() first.")

        # ── Step 1: Prepare PA Cases ───────────────────────────────────────────
        self._log("Preparing PA Cases data…")
        pa = self.pa_df.copy()

        # Identify key columns
        col_case     = _find_col(pa, ["Case", "Case Number"])
        col_fa       = _find_col(pa, ["Final Action"])
        col_wot      = _find_col(pa, ["Work Order Type"])
        col_channel  = _find_col(pa, ["Incoming Channel"])
        col_date     = _find_col(pa, ["Completion Date"])
        col_serial   = _find_col(pa, ["Serial Number"])

        missing = [n for n, c in [("Case Number", col_case), ("Final Action", col_fa),
                                   ("Completion Date", col_date)] if c is None]
        if missing:
            raise ValueError(f"Required columns not found in PA Cases sheet: {missing}\n"
                             f"Available columns: {list(pa.columns)}")

        # Normalize case numbers
        pa["__case_num"] = pa[col_case].apply(_normalize_case_num)

        # ── Step 2: Date range filtering ───────────────────────────────────────
        if start_date or end_date:
            self._log(f"Applying date filter: {start_date} → {end_date}")
            pa["__comp_date"] = pd.to_datetime(pa[col_date], errors="coerce")

            before = len(pa)
            if start_date:
                pa = pa[pa["__comp_date"].dt.date >= start_date]
            if end_date:
                pa = pa[pa["__comp_date"].dt.date <= end_date]
            self._log(f"  → Filtered PA Cases: {before} → {len(pa)} rows", "INFO")

            # Also filter channel sheets by their respective date columns
            self.sms_df   = self._filter_df_by_date(self.sms_df,   "Date Created",   start_date, end_date, "SMS")
            self.email_df = self._filter_df_by_date(self.email_df,  "Entered Queue",  start_date, end_date, "Email")
            self.phone_df = self._filter_df_by_date(self.phone_df,  "Date Created",   start_date, end_date, "Phone Call")

        if len(pa) == 0:
            raise ValueError("No PA Cases rows remain after date filtering. Check your date range.")

        # ── Step 3: Build channel case number sets ─────────────────────────────
        self._log("Building channel case sets…")

        sms_cases   = self._get_case_set(self.sms_df,   ["Case Number (Regarding) (Case)", "Case Number"])
        email_cases = self._get_case_set(self.email_df,  ["Case Number (Object) (Email)", "Case Number"])
        phone_cases = self._get_case_set(self.phone_df,  ["Case Number (Regarding) (Case)", "Case Number"])

        self._log(f"  SMS cases: {len(sms_cases)} | Email cases: {len(email_cases)} | Phone cases: {len(phone_cases)}")

        # ── Step 4: Match channels and classify outcomes ───────────────────────
        self._log("Matching cases to channels and classifying outcomes…")

        matching_channel_list = []
        reach_status_list     = []
        final_actions_norm    = []

        for _, row in pa.iterrows():
            case_num = row["__case_num"]
            fa_raw   = str(row.get(col_fa, "")).strip()
            fa_norm  = fa_raw.lower()

            # Channel matching
            in_sms   = case_num in sms_cases
            in_email = case_num in email_cases
            in_phone = case_num in phone_cases

            channels = []
            if in_sms:   channels.append("SMS")
            if in_email: channels.append("Email")
            if in_phone: channels.append("Confirmed Call")

            if not channels:
                # Determine if it was expected via phone based on Final Action
                if fa_norm in REACHED_ACTIONS:
                    channels = ["Expected Call"]
                else:
                    channels = ["Not Found"]

            matching_channel_list.append(", ".join(channels))

            # Reach status
            if fa_norm in REACHED_ACTIONS:
                reach_status_list.append("Reached")
            elif fa_norm in NOT_REACHED_ACTIONS:
                reach_status_list.append("Not Reached")
            else:
                reach_status_list.append("Unknown")

            final_actions_norm.append(fa_raw)

        pa["Matching Channel"] = matching_channel_list
        pa["Reach Status"]     = reach_status_list

        # ── Step 5: Build Total Cases sheet ───────────────────────────────────
        self._log("Building Total Cases sheet…")

        total_cols = {}
        total_cols["Case Number"]      = pa["__case_num"]
        if col_wot:
            total_cols["Work Order Type"] = pa[col_wot]
        if col_channel:
            total_cols["Incoming Channel"] = pa[col_channel]
        if col_date:
            total_cols["Completion Date"] = pa[col_date]
        total_cols["Final Action"]     = pa[col_fa]
        total_cols["Matching Channel"] = pa["Matching Channel"]
        total_cols["Reach Status"]     = pa["Reach Status"]
        if col_serial:
            total_cols["Serial Number"] = pa[col_serial]

        total_df = pd.DataFrame(total_cols)

        # ── Step 6: Compute metrics ────────────────────────────────────────────
        self._log("Computing metrics…")
        metrics = self._compute_metrics(pa, col_fa)

        # ── Step 7: Write Excel output ─────────────────────────────────────────
        self._log(f"Writing output to: {output_path}")
        self._write_excel(output_path, total_df, metrics, pa, col_fa)

        self._log(f"✓ Done — {len(total_df)} cases processed.", "SUCCESS")
        return output_path

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _filter_df_by_date(self, df: pd.DataFrame, date_col_hint: str,
                            start_date, end_date, label: str) -> pd.DataFrame:
        col = _find_col(df, [date_col_hint, "Date Created", "Entered Queue", "Date"])
        if col is None:
            self._log(f"  {label}: date column '{date_col_hint}' not found — skipping date filter", "WARNING")
            return df
        df = df.copy()
        df["__date_tmp"] = pd.to_datetime(df[col], errors="coerce")
        before = len(df)
        if start_date:
            df = df[df["__date_tmp"].dt.date >= start_date]
        if end_date:
            df = df[df["__date_tmp"].dt.date <= end_date]
        df = df.drop(columns=["__date_tmp"])
        self._log(f"  {label}: {before} → {len(df)} rows after date filter")
        return df

    def _get_case_set(self, df: pd.DataFrame, candidates: list[str]) -> set:
        col = _find_col(df, candidates)
        if col is None:
            self._log(f"  WARNING: case number column not found (tried {candidates})", "WARNING")
            return set()
        return set(df[col].apply(_normalize_case_num).dropna())

    def _compute_metrics(self, pa: pd.DataFrame, col_fa: str) -> dict:
        """Return a dict of metric DataFrames for the Metrics sheet."""
        metrics = {}

        # ── Overall Reach Rate ─────────────────────────────────────────────────
        reach_counts = pa["Reach Status"].value_counts().reindex(
            ["Reached", "Not Reached", "Unknown"], fill_value=0
        )
        total = reach_counts.sum()
        reach_pct = (reach_counts / total * 100).round(1) if total > 0 else reach_counts
        metrics["overall_reach"] = pd.DataFrame({
            "Status": reach_counts.index,
            "Count":  reach_counts.values,
            "Percentage (%)": reach_pct.values,
        })

        # ── Final Action distribution (all) ───────────────────────────────────
        fa_counts = pa[col_fa].fillna("(blank)").value_counts().reset_index()
        fa_counts.columns = ["Final Action", "Count"]
        fa_counts["Percentage (%)"] = (fa_counts["Count"] / total * 100).round(1) if total > 0 else 0
        metrics["final_action_all"] = fa_counts

        # ── Per-channel metrics ────────────────────────────────────────────────
        channel_tags = ["SMS", "Email", "Confirmed Call", "Expected Call"]
        for ch in channel_tags:
            mask = pa["Matching Channel"].str.contains(ch, case=False, na=False)
            sub  = pa[mask]
            if len(sub) == 0:
                continue

            # Final action breakdown for this channel
            ch_fa = sub[col_fa].fillna("(blank)").value_counts().reset_index()
            ch_fa.columns = ["Final Action", "Count"]
            sub_total = len(sub)
            ch_fa["Percentage (%)"] = (ch_fa["Count"] / sub_total * 100).round(1)

            # Reach rate for this channel
            ch_reach = sub["Reach Status"].value_counts().reindex(
                ["Reached", "Not Reached", "Unknown"], fill_value=0
            )
            ch_reach_df = pd.DataFrame({
                "Status": ch_reach.index,
                "Count":  ch_reach.values,
                "Percentage (%)": (ch_reach / sub_total * 100).round(1).values,
            })

            key = ch.lower().replace(" ", "_")
            metrics[f"{key}_total"]   = sub_total
            metrics[f"{key}_fa"]      = ch_fa
            metrics[f"{key}_reach"]   = ch_reach_df

        return metrics

    # ── Excel Writer ───────────────────────────────────────────────────────────

    def _write_excel(self, output_path: str, total_df: pd.DataFrame,
                     metrics: dict, pa: pd.DataFrame, col_fa: str):
        workbook  = xlsxwriter.Workbook(output_path)

        # ── Formats ────────────────────────────────────────────────────────────
        fmt_title  = workbook.add_format({"bold": True, "font_size": 14,
                                           "font_color": "#0f62fe", "font_name": "IBM Plex Sans"})
        fmt_header = workbook.add_format({"bold": True, "bg_color": "#0f62fe",
                                           "font_color": "#ffffff", "border": 1,
                                           "font_name": "IBM Plex Sans", "text_wrap": True})
        fmt_row    = workbook.add_format({"border": 1, "font_name": "IBM Plex Sans"})
        fmt_row_alt= workbook.add_format({"border": 1, "bg_color": "#f4f4f4",
                                           "font_name": "IBM Plex Sans"})
        fmt_pct    = workbook.add_format({"border": 1, "num_format": "0.0%",
                                           "font_name": "IBM Plex Sans"})
        fmt_reached    = workbook.add_format({"border": 1, "bg_color": "#defbe6",
                                               "font_color": "#198038", "bold": True,
                                               "font_name": "IBM Plex Sans"})
        fmt_notreached = workbook.add_format({"border": 1, "bg_color": "#fff1f1",
                                               "font_color": "#da1e28", "bold": True,
                                               "font_name": "IBM Plex Sans"})
        fmt_section = workbook.add_format({"bold": True, "font_size": 11,
                                            "font_color": "#161616",
                                            "font_name": "IBM Plex Sans",
                                            "bottom": 2, "bottom_color": "#0f62fe"})
        fmt_number = workbook.add_format({"border": 1, "num_format": "#,##0",
                                           "font_name": "IBM Plex Sans"})

        # ── Total Cases Sheet ──────────────────────────────────────────────────
        ws_total = workbook.add_worksheet("Total Cases")
        ws_total.set_zoom(90)
        ws_total.freeze_panes(1, 0)
        ws_total.set_row(0, 30)

        cols = list(total_df.columns)
        col_widths = {
            "Case Number": 18, "Work Order Type": 22, "Incoming Channel": 20,
            "Completion Date": 18, "Final Action": 18, "Matching Channel": 22,
            "Reach Status": 16, "Serial Number": 18,
        }
        for ci, c in enumerate(cols):
            ws_total.write(0, ci, c, fmt_header)
            ws_total.set_column(ci, ci, col_widths.get(c, 18))

        for ri, row_data in total_df.iterrows():
            row_idx = list(total_df.index).index(ri) + 1
            fmt_base = fmt_row_alt if row_idx % 2 == 0 else fmt_row
            reach_val = str(row_data.get("Reach Status", ""))
            for ci, c in enumerate(cols):
                val = row_data[c]
                val = "" if pd.isna(val) else str(val)
                if c == "Reach Status":
                    if reach_val == "Reached":
                        ws_total.write(row_idx, ci, val, fmt_reached)
                    elif reach_val == "Not Reached":
                        ws_total.write(row_idx, ci, val, fmt_notreached)
                    else:
                        ws_total.write(row_idx, ci, val, fmt_base)
                else:
                    ws_total.write(row_idx, ci, val, fmt_base)

        # ── Metrics Sheet ──────────────────────────────────────────────────────
        ws_m = workbook.add_worksheet("Metrics")
        ws_m.set_zoom(90)
        ws_m.set_column("A:A", 28)
        ws_m.set_column("B:B", 12)
        ws_m.set_column("C:C", 16)
        ws_m.set_column("D:Z", 14)

        cur_row = 0

        def write_section(title: str) -> int:
            nonlocal cur_row
            ws_m.write(cur_row, 0, title, fmt_section)
            cur_row += 1
            return cur_row

        def write_table(df: pd.DataFrame, chart_type="bar") -> int:
            nonlocal cur_row
            hdrs = list(df.columns)
            for ci, h in enumerate(hdrs):
                ws_m.write(cur_row, ci, h, fmt_header)
            data_start = cur_row + 1
            for ri, row in df.iterrows():
                r_idx = cur_row + 1 + list(df.index).index(ri)
                for ci, h in enumerate(hdrs):
                    val = row[h]
                    if pd.isna(val):
                        val = ""
                    if isinstance(val, float):
                        ws_m.write(r_idx, ci, val, fmt_row)
                    else:
                        ws_m.write(r_idx, ci, str(val), fmt_row)
            data_end = cur_row + len(df)
            cur_row = data_end + 2
            return data_start, data_end

        def add_chart(label_col: int, value_col: int, data_start: int, data_end: int,
                      title: str, chart_row: int, chart_col_x: int = 4, chart_type: str = "bar"):
            chart = workbook.add_chart({"type": chart_type})
            chart.add_series({
                "name":       title,
                "categories": [ws_m.name, data_start, label_col, data_end, label_col],
                "values":     [ws_m.name, data_start, value_col, data_end, value_col],
                "data_labels": {"value": True},
            })
            chart.set_title({"name": title, "name_font": {"name": "IBM Plex Sans", "bold": True}})
            chart.set_chartarea({"border": {"color": "#e0e0e0"}})
            chart.set_plotarea({"border": {"color": "#e0e0e0"}})
            chart.set_size({"width": 480, "height": 240})
            ws_m.insert_chart(chart_row, chart_col_x, chart)

        # ── 1. Overall Summary ─────────────────────────────────────────────────
        ws_m.write(cur_row, 0, "Reach Rate Calculator — Metrics Overview", fmt_title)
        cur_row += 2

        write_section("1. Overall Reach Rate")
        reach_df = metrics.get("overall_reach")
        if reach_df is not None:
            tbl_chart_row = cur_row
            ds, de = write_table(reach_df, chart_type="pie")
            add_chart(label_col=0, value_col=1, data_start=ds-1+1, data_end=de,
                      title="Overall Reach Rate", chart_row=tbl_chart_row, chart_type="pie")
        cur_row += 3

        # ── 2. Final Action Distribution (all cases) ───────────────────────────
        write_section("2. Final Action Distribution (All Cases)")
        fa_df = metrics.get("final_action_all")
        if fa_df is not None:
            tbl_chart_row = cur_row
            ds, de = write_table(fa_df, chart_type="bar")
            add_chart(label_col=0, value_col=1, data_start=ds-1+1, data_end=de,
                      title="Final Action Distribution", chart_row=tbl_chart_row, chart_type="bar")
        cur_row += 3

        # ── 3. Per-Channel Sections ────────────────────────────────────────────
        channel_tags = [
            ("SMS",           "sms"),
            ("Email",          "email"),
            ("Confirmed Call", "confirmed_call"),
            ("Expected Call",  "expected_call"),
        ]

        for ch_label, ch_key in channel_tags:
            fa_key    = f"{ch_key}_fa"
            reach_key = f"{ch_key}_reach"
            tot_key   = f"{ch_key}_total"

            if fa_key not in metrics:
                continue

            total_ch = metrics.get(tot_key, 0)
            write_section(f"3. {ch_label} Channel  ({total_ch} cases)")

            # Final action sub-table
            ws_m.write(cur_row, 0, "Final Action Breakdown", fmt_section)
            cur_row += 1
            ch_fa_df = metrics[fa_key]
            tbl_chart_row = cur_row
            ds, de = write_table(ch_fa_df)
            add_chart(label_col=0, value_col=1, data_start=ds-1+1, data_end=de,
                      title=f"{ch_label} — Final Actions", chart_row=tbl_chart_row,
                      chart_col_x=4, chart_type="bar")
            cur_row += 2

            # Reach rate sub-table
            ws_m.write(cur_row, 0, "Reach Rate", fmt_section)
            cur_row += 1
            ch_reach_df = metrics[reach_key]
            tbl_chart_row = cur_row
            ds, de = write_table(ch_reach_df)
            add_chart(label_col=0, value_col=1, data_start=ds-1+1, data_end=de,
                      title=f"{ch_label} — Reach Rate", chart_row=tbl_chart_row,
                      chart_col_x=4, chart_type="pie")
            cur_row += 5

        workbook.close()
        self._log(f"Output saved → {output_path}", "SUCCESS")
