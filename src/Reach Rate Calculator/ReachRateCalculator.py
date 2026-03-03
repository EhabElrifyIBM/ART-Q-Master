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
        self.pa_df = self._load_pa_sheet(pa_path)
        self._log(f"  ✓ PA Cases: {len(self.pa_df)} rows | {list(self.pa_df.columns[:5])}…", "SUCCESS")

        self._log("Loading SMS View sheet…")
        self.sms_df = self._load_first_sheet(sms_path, "SMS")
        self._log(f"  ✓ SMS:      {len(self.sms_df)} rows", "SUCCESS")

        self._log("Loading Email View sheet…")
        self.email_df = self._load_first_sheet(email_path, "Email")
        self._log(f"  ✓ Email:    {len(self.email_df)} rows", "SUCCESS")

        self._log("Loading Phone Call View sheet…")
        self.phone_df = self._load_first_sheet(phone_path, "Phone Call")
        self._log(f"  ✓ Phone:    {len(self.phone_df)} rows", "SUCCESS")

    def _load_first_sheet(self, path: str, label: str = "") -> pd.DataFrame:
        """Always load the first (and usually only) sheet — used for channel view files."""
        xl = pd.ExcelFile(path)
        sheet = xl.sheet_names[0]
        self._log(f"  → {label}: using sheet '{sheet}' from {os.path.basename(path)}")
        return pd.read_excel(xl, sheet_name=sheet, dtype=str)

    def _load_pa_sheet(self, path: str) -> pd.DataFrame:
        """
        Load the PA Cases workbook.  Looks for a sheet named 'PA Cases';
        falls back to the first sheet if not found.
        """
        xl = pd.ExcelFile(path)
        target = next((n for n in xl.sheet_names
                       if "pa cases" in n.lower()), None)
        if target:
            self._log(f"  → PA Cases: using sheet '{target}' from {os.path.basename(path)}")
        else:
            target = xl.sheet_names[0]
            self._log(f"  → 'PA Cases' sheet not found; using first sheet '{target}'", "WARNING")
        return pd.read_excel(xl, sheet_name=target, dtype=str)

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
        col_case     = _find_col(pa, ["Case Number"])
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

        for _, row in pa.iterrows():
            case_num = row["__case_num"]

            # ── NaN-safe Final Action read ─────────────────────────────────────
            fa_val  = row.get(col_fa)
            fa_raw  = "" if (fa_val is None or (isinstance(fa_val, float) and pd.isna(fa_val)))\
                      else str(fa_val).strip()
            fa_norm = fa_raw.lower()

            # Channel matching
            in_sms   = case_num in sms_cases
            in_email = case_num in email_cases
            in_phone = case_num in phone_cases

            channels = []
            if in_sms:   channels.append("SMS")
            if in_email: channels.append("Email")
            if in_phone: channels.append("Confirmed Call")

            if not channels:
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
        """Return a dict of metric DataFrames."""
        metrics  = {}
        total_all = len(pa)

        # ── Overall Reach Rate ─────────────────────────────────────────────────
        reach_counts = pa["Reach Status"].value_counts().reindex(
            ["Reached", "Not Reached", "Unknown"], fill_value=0
        )
        reach_pct = (reach_counts / total_all * 100).round(1) if total_all > 0 else reach_counts
        metrics["overall_reach"] = pd.DataFrame({
            "Status":         reach_counts.index,
            "Count":          reach_counts.values,
            "% of All Cases": reach_pct.values,
        })
        metrics["total_all"] = total_all

        # ── Final Action distribution (all cases) ──────────────────────────────
        fa_filled = pa[col_fa].fillna("").apply(
            lambda v: "" if (isinstance(v, float) and pd.isna(v)) else str(v).strip()
        ).replace("", "(blank)")
        fa_counts  = fa_filled.value_counts().reset_index()
        fa_counts.columns = ["Final Action", "Count"]
        fa_counts["% of All Cases"] = (
            fa_counts["Count"] / total_all * 100
        ).round(1) if total_all > 0 else 0
        metrics["final_action_all"] = fa_counts

        # ── Channel Summary: cross-channel comparison ──────────────────────────
        summary_rows = []
        for ch in ["SMS", "Email", "Confirmed Call", "Expected Call", "Not Found"]:
            mask     = pa["Matching Channel"].str.contains(ch, case=False, na=False)
            sub      = pa[mask]
            ch_total = len(sub)
            if ch_total == 0:
                continue
            ch_reached     = int((sub["Reach Status"] == "Reached").sum())
            ch_not_reached = int((sub["Reach Status"] == "Not Reached").sum())
            ch_unknown     = ch_total - ch_reached - ch_not_reached
            reach_rate     = round(ch_reached / ch_total * 100, 1)
            summary_rows.append({
                "Channel":         ch,
                "Cases":           ch_total,
                "% of All Cases":  round(ch_total / total_all * 100, 1) if total_all > 0 else 0,
                "Reached":         ch_reached,
                "% Reached":       round(ch_reached     / ch_total * 100, 1),
                "Not Reached":     ch_not_reached,
                "% Not Reached":   round(ch_not_reached / ch_total * 100, 1),
                "Unknown":         ch_unknown,
                "Reach Rate (%)":  reach_rate,
            })
        metrics["channel_summary"] = (
            pd.DataFrame(summary_rows) if summary_rows else pd.DataFrame()
        )

        # ── Per-channel detail metrics ─────────────────────────────────────────
        for ch in ["SMS", "Email", "Confirmed Call", "Expected Call"]:
            mask  = pa["Matching Channel"].str.contains(ch, case=False, na=False)
            sub   = pa[mask]
            if len(sub) == 0:
                continue

            sub_total = len(sub)

            # Final action breakdown (count + % within channel + % of all cases)
            ch_fa = fa_filled[mask].value_counts().reset_index()
            ch_fa.columns = ["Final Action", "Count"]
            ch_fa["% within Channel"] = (ch_fa["Count"] / sub_total  * 100).round(1)
            ch_fa["% of All Cases"]   = (ch_fa["Count"] / total_all  * 100).round(1) if total_all > 0 else 0

            # Reach rate (count + % within channel + % of all cases)
            ch_reached     = int((sub["Reach Status"] == "Reached").sum())
            ch_not_reached = int((sub["Reach Status"] == "Not Reached").sum())
            ch_unknown     = sub_total - ch_reached - ch_not_reached

            def _pct(n, d):  return round(n / d * 100, 1) if d > 0 else 0

            ch_reach_df = pd.DataFrame({
                "Status":            ["Reached",    "Not Reached",    "Unknown"],
                "Count":             [ch_reached,    ch_not_reached,   ch_unknown],
                "% within Channel": [_pct(ch_reached, sub_total),
                                      _pct(ch_not_reached, sub_total),
                                      _pct(ch_unknown, sub_total)],
                "% of All Cases":   [_pct(ch_reached, total_all),
                                      _pct(ch_not_reached, total_all),
                                      _pct(ch_unknown, total_all)],
            })

            key = ch.lower().replace(" ", "_")
            metrics[f"{key}_total"] = sub_total
            metrics[f"{key}_fa"]    = ch_fa
            metrics[f"{key}_reach"] = ch_reach_df

        return metrics

    # ── Excel Writer ───────────────────────────────────────────────────────────

    def _write_excel(self, output_path: str, total_df: pd.DataFrame,
                     metrics: dict, pa: pd.DataFrame, col_fa: str):
        workbook = xlsxwriter.Workbook(output_path)

        # ── Shared Formats ─────────────────────────────────────────────────────
        fmt_title      = workbook.add_format({"bold": True, "font_size": 14,
                                               "font_color": "#0f62fe",
                                               "font_name": "IBM Plex Sans"})
        fmt_header     = workbook.add_format({"bold": True, "bg_color": "#0f62fe",
                                               "font_color": "#ffffff", "border": 1,
                                               "font_name": "IBM Plex Sans",
                                               "text_wrap": True, "valign": "vcenter"})
        fmt_row        = workbook.add_format({"border": 1, "font_name": "IBM Plex Sans"})
        fmt_row_alt    = workbook.add_format({"border": 1, "bg_color": "#f4f4f4",
                                               "font_name": "IBM Plex Sans"})
        fmt_reached    = workbook.add_format({"border": 1, "bg_color": "#defbe6",
                                               "font_color": "#198038", "bold": True,
                                               "font_name": "IBM Plex Sans"})
        fmt_notreached = workbook.add_format({"border": 1, "bg_color": "#fff1f1",
                                               "font_color": "#da1e28", "bold": True,
                                               "font_name": "IBM Plex Sans"})
        fmt_section    = workbook.add_format({"bold": True, "font_size": 12,
                                               "font_color": "#0f62fe",
                                               "font_name": "IBM Plex Sans",
                                               "bottom": 2, "bottom_color": "#0f62fe"})
        fmt_sub        = workbook.add_format({"bold": True, "font_size": 10,
                                               "font_color": "#525252",
                                               "font_name": "IBM Plex Sans",
                                               "italic": True})

        # ── Helpers ────────────────────────────────────────────────────────────
        def _setup_metrics_sheet(ws):
            ws.set_zoom(90)
            ws.set_column("A:A", 30)
            ws.set_column("B:B", 12)
            ws.set_column("C:C", 16)
            ws.set_column("D:Z", 14)

        def _write_table(ws, df: pd.DataFrame, start_row: int):
            """Write table headers+data to ws starting at start_row. Returns (data_start, data_end)."""
            hdrs = list(df.columns)
            for ci, h in enumerate(hdrs):
                ws.write(start_row, ci, h, fmt_header)
            data_start = start_row + 1
            for ri, row in df.iterrows():
                r_idx = start_row + 1 + list(df.index).index(ri)
                for ci, h in enumerate(hdrs):
                    val = row[h]
                    if pd.isna(val):
                        val = ""
                    if isinstance(val, float):
                        ws.write(r_idx, ci, val, fmt_row)
                    else:
                        ws.write(r_idx, ci, str(val), fmt_row)
            data_end = start_row + len(df)
            return data_start, data_end

        def _add_chart(ws, label_col, value_col, data_start, data_end,
                       title, chart_row, chart_col=4, chart_type="bar"):
            chart = workbook.add_chart({"type": chart_type})
            chart.add_series({
                "name":        title,
                "categories":  [ws.name, data_start, label_col, data_end, label_col],
                "values":      [ws.name, data_start, value_col, data_end, value_col],
                "data_labels": {"value": True},
            })
            chart.set_title({"name": title,
                             "name_font": {"name": "IBM Plex Sans", "bold": True}})
            chart.set_chartarea({"border": {"color": "#e0e0e0"}})
            chart.set_plotarea({"border":  {"color": "#e0e0e0"}})
            chart.set_size({"width": 500, "height": 260})
            ws.insert_chart(chart_row, chart_col, chart)

        # ==================================================================
        # Sheet 1 — Total Cases
        # ==================================================================
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
            fmt_base  = fmt_row_alt if row_idx % 2 == 0 else fmt_row
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

        self._log("  Written: Total Cases sheet")

        # ==================================================================
        # Sheet 2 — Overall Summary
        # ==================================================================
        ws_ov = workbook.add_worksheet("Overall Summary")
        _setup_metrics_sheet(ws_ov)
        # Wider columns for the bigger tables
        ws_ov.set_column("A:A", 22)
        ws_ov.set_column("B:J", 16)
        r = 0
        total_all = metrics.get("total_all", 0)
        ws_ov.write(r, 0, f"Reach Rate Calculator — Overall Summary  ({total_all} total cases)", fmt_title)
        r += 2

        # ── Channel Comparison table (core ask) ──────────────────────────────
        ws_ov.write(r, 0, "Channel Reach Rate Comparison", fmt_section)
        r += 1
        ch_sum_df = metrics.get("channel_summary")
        if ch_sum_df is not None and len(ch_sum_df) > 0:
            tbl_r = r
            ds, de = _write_table(ws_ov, ch_sum_df, r)
            r = de + 2
            # Bar chart: reach rate (%) per channel
            _add_chart(ws_ov, 0, 8, ds, de,   # col 8 = "Reach Rate (%)"
                       "Reach Rate (%) by Channel",
                       chart_row=tbl_r, chart_col=10, chart_type="bar")
            r = max(r, tbl_r + 16)

        # ── Overall reach rate table + pie chart ────────────────────────────
        ws_ov.write(r, 0, "Overall Reach Rate (all channels)", fmt_section)
        r += 1
        reach_df = metrics.get("overall_reach")
        if reach_df is not None:
            tbl_r = r
            ds, de = _write_table(ws_ov, reach_df, r)
            r = de + 2
            _add_chart(ws_ov, 0, 1, ds, de, "Overall Reach Rate",
                       chart_row=tbl_r, chart_col=4, chart_type="pie")
            r = max(r, tbl_r + 14)

        # ── Final action distribution + bar chart ────────────────────────────
        ws_ov.write(r, 0, "Final Action Distribution (All Cases)", fmt_section)
        r += 1
        fa_df = metrics.get("final_action_all")
        if fa_df is not None:
            tbl_r = r
            ds, de = _write_table(ws_ov, fa_df, r)
            r = de + 2
            _add_chart(ws_ov, 0, 1, ds, de, "Final Action Distribution",
                       chart_row=tbl_r, chart_col=4, chart_type="bar")

        self._log("  Written: Overall Summary sheet")

        # ==================================================================
        # Sheets 3–6 — Per-channel metric sheets
        # ==================================================================
        channel_tags = [
            ("SMS",           "sms",           "SMS Channel"),
            ("Email",          "email",          "Email Channel"),
            ("Confirmed Call", "confirmed_call", "Confirmed Call Channel"),
            ("Expected Call",  "expected_call",  "Expected Call Channel"),
        ]

        for ch_label, ch_key, sheet_name in channel_tags:
            fa_key    = f"{ch_key}_fa"
            reach_key = f"{ch_key}_reach"
            tot_key   = f"{ch_key}_total"

            if fa_key not in metrics:
                self._log(f"  Skipping {ch_label} (no data found)")
                continue

            total_ch  = metrics.get(tot_key, 0)
            pct_of_all = round(total_ch / total_all * 100, 1) if total_all > 0 else 0
            ws_ch = workbook.add_worksheet(sheet_name)
            _setup_metrics_sheet(ws_ch)
            # Wider columns for the extra metric columns
            ws_ch.set_column("A:A", 22)
            ws_ch.set_column("B:E", 18)
            r = 0

            ws_ch.write(r, 0,
                        f"{ch_label}  —  {total_ch} cases  ({pct_of_all}% of all cases)", fmt_title)
            r += 2

            # ── Final Action Breakdown ─────────────────────────────────────
            ws_ch.write(r, 0, "Final Action Breakdown", fmt_section)
            r += 1
            ch_fa_df = metrics[fa_key]
            tbl_r = r
            ds, de = _write_table(ws_ch, ch_fa_df, r)
            r = de + 2
            _add_chart(ws_ch, 0, 1, ds, de,
                       f"{ch_label} — Final Actions",
                       chart_row=tbl_r, chart_col=4, chart_type="bar")
            r = max(r, tbl_r + 15)  # leave room for chart

            # ── Reach Rate ─────────────────────────────────────────────────
            ws_ch.write(r, 0, "Reach Rate", fmt_section)
            r += 1
            ch_reach_df = metrics[reach_key]
            tbl_r = r
            ds, de = _write_table(ws_ch, ch_reach_df, r)
            _add_chart(ws_ch, 0, 1, ds, de,
                       f"{ch_label} — Reach Rate",
                       chart_row=tbl_r, chart_col=4, chart_type="pie")

            self._log(f"  Written: {sheet_name} sheet ({total_ch} cases)")

        workbook.close()
        self._log(f"Output saved → {output_path}", "SUCCESS")
