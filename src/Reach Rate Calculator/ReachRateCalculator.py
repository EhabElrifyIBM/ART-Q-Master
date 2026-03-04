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
    "fixed", "issue not fixed", "not yet tested", "escalation",
    "not yet tested"
}
NOT_REACHED_ACTIONS = {
    "sent sms", "sent email", "left vm", "reviewed",
    "bank/sutherland", "not reached" , "dnd"
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

        # ── Step 1b: Complete missing Completion Dates from Last Status Change ─────
        col_last_status = _find_col(pa, ["Last Status Change"])
        if col_last_status:
            def _is_blank(v):
                if v is None: return True
                if isinstance(v, float) and pd.isna(v): return True
                return str(v).strip().lower() in ("", "nan", "none", "nat")

            before_fill = pa[col_date].apply(_is_blank).sum()
            if before_fill > 0:
                fill_mask = pa[col_date].apply(_is_blank)
                pa.loc[fill_mask, col_date] = pa.loc[fill_mask, col_last_status]
                after_fill = pa[col_date].apply(_is_blank).sum()
                self._log(
                    f"  Completion Date: filled {before_fill - after_fill} empty cells"
                    f" from 'Last Status Change' ({after_fill} still blank)"
                )
        else:
            self._log("  'Last Status Change' column not found — skipping date completion", "WARNING")

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
        metrics = self._compute_metrics(pa, col_fa, col_date=col_date, col_wot=col_wot)

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

    def _compute_metrics(self, pa: pd.DataFrame, col_fa: str,
                          col_date: str = None, col_wot: str = None) -> dict:
        """Return a dict of metric DataFrames."""
        metrics   = {}
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

        # ── Helper: clean Final Action series ─────────────────────────────────
        fa_filled = pa[col_fa].fillna("").apply(
            lambda v: "" if (isinstance(v, float) and pd.isna(v)) else str(v).strip()
        ).replace("", "(blank)")

        # ── Final Action distribution (all cases) ──────────────────────────────
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

        # ── Monthly × Channel pivot (reference chart format) ───────────────────
        # Rows = months, Columns = Email / SMS / Calls  (count + reach %),  GT
        if col_date:
            pa["__month_period"] = pd.to_datetime(pa[col_date], errors="coerce").dt.to_period("M")
            months = sorted(pa["__month_period"].dropna().unique())
            ch_cols = [
                ("Email",          "Emails"),
                ("SMS",            "SMS"),
                ("Confirmed Call", "Calls"),
            ]
            pivot_rows = []
            for period in months:
                m_mask = pa["__month_period"] == period
                m_sub  = pa[m_mask]
                row    = {"Month": period.strftime("%B %Y")}
                gt     = 0
                for ch_tag, col_name in ch_cols:
                    ch_mask  = m_sub["Matching Channel"].str.contains(ch_tag, case=False, na=False)
                    ch_sub   = m_sub[ch_mask]
                    count    = len(ch_sub)
                    reached  = int((ch_sub["Reach Status"] == "Reached").sum())
                    rate     = round(reached / count * 100, 1) if count > 0 else 0
                    gt      += count
                    row[f"{col_name}_Count"]    = count
                    row[f"{col_name}_Reach%"]   = rate
                row["Grand Total"] = gt
                pivot_rows.append(row)

            # Grand Total summary row
            if pivot_rows:
                gt_row = {"Month": "Grand Total"}
                for ch_tag, col_name in ch_cols:
                    ch_mask  = pa["Matching Channel"].str.contains(ch_tag, case=False, na=False)
                    ch_sub   = pa[ch_mask]
                    count    = len(ch_sub)
                    reached  = int((ch_sub["Reach Status"] == "Reached").sum())
                    gt_row[f"{col_name}_Count"]  = count
                    gt_row[f"{col_name}_Reach%"] = round(reached / count * 100, 1) if count > 0 else 0
                gt_row["Grand Total"] = sum(r["Grand Total"] for r in pivot_rows)
                pivot_rows.append(gt_row)

            metrics["monthly_pivot"] = pd.DataFrame(pivot_rows) if pivot_rows else pd.DataFrame()
            metrics["monthly_ch_cols"] = ch_cols  # keep label mapping for chart
        else:
            metrics["monthly_pivot"]    = pd.DataFrame()
            metrics["monthly_ch_cols"]  = []

        # ── Work Order Type reach rate (overall + per channel) ────────────────
        if col_wot:
            CHANNELS = ["SMS", "Email", "Confirmed Call", "Expected Call"]
            wot_rows = []
            for wot, grp in pa.groupby(pa[col_wot].fillna("(blank)")):
                g_total    = len(grp)
                g_reached  = int((grp["Reach Status"] == "Reached").sum())
                g_not      = int((grp["Reach Status"] == "Not Reached").sum())
                row = {
                    "Work Order Type": str(wot).strip(),
                    "Total Cases":     g_total,
                    "Reached":         g_reached,
                    "Not Reached":     g_not,
                    "Reach Rate (%)":  round(g_reached / g_total * 100, 1) if g_total > 0 else 0,
                }
                for ch in CHANNELS:
                    ch_mask   = grp["Matching Channel"].str.contains(ch, case=False, na=False)
                    ch_grp    = grp[ch_mask]
                    ch_total  = len(ch_grp)
                    ch_reach  = int((ch_grp["Reach Status"] == "Reached").sum())
                    safe_name = ch.replace(" ", "_")
                    row[f"{ch}_Cases"]    = ch_total
                    row[f"{ch}_Reached"]  = ch_reach
                    row[f"{ch}_Rate(%)"]  = round(ch_reach / ch_total * 100, 1) if ch_total > 0 else 0
                wot_rows.append(row)
            wot_rows.sort(key=lambda r: r["Total Cases"], reverse=True)
            metrics["work_order_reach"] = pd.DataFrame(wot_rows) if wot_rows else pd.DataFrame()
        else:
            metrics["work_order_reach"] = pd.DataFrame()

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

        # Charts removed — tables only

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

        # ── Overall reach rate table + pie chart ────────────────────────────
        ws_ov.write(r, 0, "Overall Reach Rate (all channels)", fmt_section)
        r += 1
        reach_df = metrics.get("overall_reach")
        if reach_df is not None:
            tbl_r = r
            ds, de = _write_table(ws_ov, reach_df, r)
            r = de + 2

        # ── Final action distribution + bar chart ────────────────────────────
        ws_ov.write(r, 0, "Final Action Distribution (All Cases)", fmt_section)
        r += 1
        fa_df = metrics.get("final_action_all")
        if fa_df is not None:
            tbl_r = r
            ds, de = _write_table(ws_ov, fa_df, r)
            r = de + 2

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

            # ── Reach Rate ─────────────────────────────────────────────────
            r += 1
            ch_reach_df = metrics[reach_key]
            tbl_r = r
            ds, de = _write_table(ws_ch, ch_reach_df, r)

            self._log(f"  Written: {sheet_name} sheet ({total_ch} cases)")

        # ==================================================================
        # Sheet: Monthly Breakdown  &  By Work Order Type
        # ==================================================================
        self._add_monthly_sheet(workbook, metrics,
                                 fmt_title, fmt_header, fmt_row, fmt_row_alt, fmt_section)
        self._add_wot_sheet(workbook, metrics,
                             fmt_title, fmt_header, fmt_row, fmt_row_alt, fmt_section)

        workbook.close()
        self._log(f"Output saved → {output_path}", "SUCCESS")

    # ── Monthly Breakdown sheet writer (used by _write_excel) ────────────────

    def _add_monthly_sheet(self, workbook, metrics: dict,
                            fmt_title, fmt_header, fmt_row, fmt_row_alt, fmt_section):
        pivot_df = metrics.get("monthly_pivot", pd.DataFrame())
        if pivot_df.empty:
            self._log("  Skipping Monthly Breakdown (no date data)")
            return

        ch_cols = metrics.get("monthly_ch_cols", [])  # [(tag, label), …]
        ws = workbook.add_worksheet("Monthly Breakdown")
        ws.set_zoom(90)
        ws.freeze_panes(3, 0)  # freeze below double-header rows

        # ── Column widths ──────────────────────────────────────────────────────
        ws.set_column(0, 0, 16)    # Month
        # Each channel has 2 sub-cols (Count + Reach%), then GT
        #  col 1,2 = Emails count/%  |  3,4 = SMS count/%  |  5,6 = Calls count/%  |  7 = GT
        ws.set_column(1, 6, 12)
        ws.set_column(7, 7, 13)    # Grand Total

        total_all = metrics.get("total_all", 0)

        # ── Shared sub-formats ─────────────────────────────────────────────────
        ch_bg = {
            "Emails": "#0043ce",   # IBM Blue 70
            "SMS":    "#da1e28",   # IBM Red 60  (warm contrast)
            "Calls":  "#198038",   # IBM Green 60
        }
        fmt_gt_label = workbook.add_format({
            "bold": True, "border": 1, "font_size": 11,
            "font_name": "IBM Plex Sans", "bg_color": "#e8daff",
        })
        fmt_gt_num = workbook.add_format({
            "bold": True, "border": 1, "font_size": 11,
            "font_name": "IBM Plex Sans", "bg_color": "#e8daff", "num_format": "0",
        })
        fmt_gt_pct = workbook.add_format({
            "bold": True, "border": 1, "font_size": 11,
            "font_name": "IBM Plex Sans", "bg_color": "#e8daff",
            "font_color": "#0043ce", "num_format": "0\"%\"",
        })
        fmt_gt_total = workbook.add_format({
            "bold": True, "border": 1, "font_size": 11,
            "font_name": "IBM Plex Sans", "bg_color": "#a56eff",
            "font_color": "#ffffff", "num_format": "0",
        })
        fmt_num = workbook.add_format({
            "border": 1, "font_name": "IBM Plex Sans", "num_format": "0",
        })
        fmt_num_alt = workbook.add_format({
            "border": 1, "font_name": "IBM Plex Sans",
            "bg_color": "#f4f4f4", "num_format": "0",
        })
        fmt_pct = workbook.add_format({
            "border": 1, "font_name": "IBM Plex Sans",
            "font_color": "#0043ce", "bold": True, "num_format": "0\"%\"",
        })
        fmt_pct_alt = workbook.add_format({
            "border": 1, "font_name": "IBM Plex Sans",
            "bg_color": "#f4f4f4", "font_color": "#0043ce",
            "bold": True, "num_format": "0\"%\"",
        })
        fmt_gt_col = workbook.add_format({
            "border": 1, "font_name": "IBM Plex Sans",
            "bg_color": "#d0e2ff", "bold": True, "num_format": "0",
        })
        fmt_gt_col_alt = workbook.add_format({
            "border": 1, "font_name": "IBM Plex Sans",
            "bg_color": "#c0d6f4", "bold": True, "num_format": "0",
        })

        # ── Row 0: title ───────────────────────────────────────────────────────
        ws.set_row(0, 24)
        ws.write(0, 0, "Reach Rate Breakdown by Communication Channel", fmt_title)

        # ── Row 1: channel group headers (merged 2 cols each) ──────────────────
        ws.set_row(1, 22)
        ws.write(1, 0, "", fmt_header)          # Month label cell
        col = 1
        for _tag, label in ch_cols:
            bg = ch_bg.get(label, "#0f62fe")
            f  = workbook.add_format({
                "bold": True, "align": "center", "valign": "vcenter",
                "border": 1, "font_name": "IBM Plex Sans", "font_size": 11,
                "bg_color": bg, "font_color": "#ffffff",
            })
            ws.merge_range(1, col, 1, col + 1, label, f)
            col += 2
        # Grand Total header
        fmt_gt_hdr = workbook.add_format({
            "bold": True, "align": "center", "valign": "vcenter",
            "border": 1, "font_name": "IBM Plex Sans",
            "bg_color": "#6929c4", "font_color": "#ffffff",
        })
        ws.write(1, col, "GT", fmt_gt_hdr)

        # ── Row 2: sub-column headers ──────────────────────────────────────────
        ws.set_row(2, 20)
        ws.write(2, 0, "Month", fmt_header)
        col = 1
        for _tag, label in ch_cols:
            ws.write(2, col,     "Count",   fmt_header)
            ws.write(2, col + 1, "Reach %", fmt_header)
            col += 2
        ws.write(2, col, "Total", fmt_header)

        # ── Data rows: all months (last row in pivot_rows is Grand Total) ──────
        data_rows = pivot_df.to_dict(orient="records")

        # separate grand total row if it exists
        normal_rows = [r for r in data_rows if r.get("Month") != "Grand Total"]
        gt_rows     = [r for r in data_rows if r.get("Month") == "Grand Total"]

        for ri, row in enumerate(normal_rows):
            r_idx    = ri + 3
            is_alt   = ri % 2 == 1
            f_label  = fmt_row_alt if is_alt else fmt_row
            f_num    = fmt_num_alt if is_alt else fmt_num
            f_pct    = fmt_pct_alt if is_alt else fmt_pct
            f_gt_col = fmt_gt_col_alt if is_alt else fmt_gt_col

            ws.set_row(r_idx, 18)
            ws.write(r_idx, 0, str(row.get("Month", "")), f_label)
            col = 1
            for _tag, label in ch_cols:
                count = row.get(f"{label}_Count", 0) or 0
                pct   = row.get(f"{label}_Reach%", 0) or 0
                ws.write_number(r_idx, col,     int(count), f_num)
                ws.write_number(r_idx, col + 1, float(pct),  f_pct)
                col += 2
            gt_val = row.get("Grand Total", 0) or 0
            ws.write_number(r_idx, col, int(gt_val), f_gt_col)

        # ── Grand Total row ────────────────────────────────────────────────────
        if gt_rows:
            gr     = gt_rows[0]
            r_idx  = len(normal_rows) + 3
            ws.set_row(r_idx, 20)
            ws.write(r_idx, 0, "Grand Total", fmt_gt_label)
            col = 1
            for _tag, label in ch_cols:
                count = gr.get(f"{label}_Count", 0) or 0
                pct   = gr.get(f"{label}_Reach%", 0) or 0
                ws.write_number(r_idx, col,     int(count),   fmt_gt_num)
                ws.write_number(r_idx, col + 1, float(pct),   fmt_gt_pct)
                col += 2
            gt_val = gr.get("Grand Total", 0) or 0
            ws.write_number(r_idx, col, int(gt_val), fmt_gt_total)

        self._log(f"  Written: Monthly Breakdown sheet ({len(normal_rows)} months)")

    def _add_wot_sheet(self, workbook, metrics: dict,
                        fmt_title, fmt_header, fmt_row, fmt_row_alt, fmt_section):
        wot_df = metrics.get("work_order_reach", None)
        if wot_df is None or wot_df.empty:
            self._log("  Skipping By Work Order Type (no data or column missing)")
            return

        ws = workbook.add_worksheet("By Work Order Type")
        ws.set_zoom(85)
        ws.freeze_panes(1, 0)

        # ── Column widths ──────────────────────────────────────────────────────
        ws.set_column(0, 0, 32)   # Work Order Type
        ws.set_column(1, 4, 14)   # Overall columns
        # Per-channel groups:  SMS(3) + Email(3) + Confirmed Call(3) + Expected Call(3)
        for c in range(5, 5 + 4 * 3):
            ws.set_column(c, c, 16)

        # ── Title ──────────────────────────────────────────────────────────────
        ws.set_row(0, 24)
        ws.write(0, 0, "Reach Rate by Work Order Type", fmt_title)

        # ── Group header row (row 1): channel labels spanning 3 sub-cols each ─
        fmt_ch_hdr = workbook.add_format({
            "bold": True, "align": "center", "valign": "vcenter",
            "border": 1, "text_wrap": True,
            "font_name": "IBM Plex Sans", "font_size": 11,
        })
        fmt_ov_hdr = workbook.add_format({
            "bold": True, "bg_color": "#0f62fe", "font_color": "#ffffff",
            "border": 1, "align": "center", "valign": "vcenter",
            "font_name": "IBM Plex Sans",
        })
        ch_colors = {
            "SMS":           "#005d5d",
            "Email":         "#6929c4",
            "Confirmed Call":"#005d5d",
            "Expected Call": "#b45309",
        }
        CHANNELS = ["SMS", "Email", "Confirmed Call", "Expected Call"]

        # Row 1 — group headers
        ws.write(1, 0, "", fmt_ov_hdr)        # WO Type label cell
        ws.write(1, 1, "Overall", fmt_ov_hdr)
        ws.merge_range(1, 2, 1, 4, "", fmt_ov_hdr)  # Overall spans cols 2-4 → only Total/Reached/Not Reached/Rate
        col = 5
        for ch in CHANNELS:
            bg = ch_colors.get(ch, "#0f62fe")
            f  = workbook.add_format({
                "bold": True, "align": "center", "valign": "vcenter",
                "border": 1, "font_name": "IBM Plex Sans",
                "bg_color": bg, "font_color": "#ffffff",
            })
            ws.merge_range(1, col, 1, col + 2, ch, f)
            col += 3

        # Row 2 — sub-column headers
        sub_hdrs_overall = ["Work Order Type", "Total Cases", "Reached", "Not Reached", "Reach Rate (%)"]
        sub_hdrs_ch      = ["Cases", "Reached", "Rate (%)"]

        for ci, h in enumerate(sub_hdrs_overall):
            ws.write(2, ci, h, fmt_header)
        col = 5
        for ch in CHANNELS:
            for sh in sub_hdrs_ch:
                ws.write(2, col, sh, fmt_header)
                col += 1

        # ── Data rows ─────────────────────────────────────────────────────────
        fmt_rate = workbook.add_format({
            "border": 1, "bold": True,
            "font_color": "#198038", "font_name": "IBM Plex Sans",
        })
        fmt_zero = workbook.add_format({
            "border": 1, "font_color": "#8d8d8d", "font_name": "IBM Plex Sans",
        })

        for ri, row in wot_df.iterrows():
            r_idx  = ri + 3
            base_f = fmt_row_alt if ri % 2 == 0 else fmt_row
            # Overall columns
            ws.write(r_idx, 0, str(row.get("Work Order Type", "")), base_f)
            ws.write(r_idx, 1, int(row.get("Total Cases",  0)),     base_f)
            ws.write(r_idx, 2, int(row.get("Reached",       0)),    base_f)
            ws.write(r_idx, 3, int(row.get("Not Reached",   0)),    base_f)
            rate_val = row.get("Reach Rate (%)", 0)
            ws.write(r_idx, 4, rate_val if not (hasattr(rate_val, "__class__") and str(rate_val) == "nan") else 0,
                     fmt_rate)
            # Per-channel columns
            col = 5
            for ch in CHANNELS:
                cases  = int(row.get(f"{ch}_Cases",   0))
                reachd = int(row.get(f"{ch}_Reached", 0))
                rate   = row.get(f"{ch}_Rate(%)",     0)
                f_c    = base_f if cases > 0 else fmt_zero
                ws.write(r_idx, col,     cases,  f_c)
                ws.write(r_idx, col + 1, reachd, f_c)
                ws.write(r_idx, col + 2, rate if cases > 0 else "-", fmt_rate if cases > 0 else fmt_zero)
                col += 3

        self._log(f"  Written: By Work Order Type sheet ({len(wot_df)} WO types)")
