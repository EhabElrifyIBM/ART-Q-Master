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
import io
from datetime import datetime, date
from typing import Optional, Callable, Dict

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

# ── Chart Configuration Constants ──────────────────────────────────────────────

# IBM Carbon Design System Colors
IBM_BLUE_60 = "#0f62fe"      # Primary brand color
IBM_BLUE_70 = "#0043ce"      # Darker blue for emphasis
IBM_BLUE_10 = "#d0e2ff"      # Light blue backgrounds
IBM_GREEN_60 = "#198038"     # Success/Reached/Positive
IBM_GREEN_10 = "#defbe6"     # Light green backgrounds
IBM_RED_60 = "#da1e28"       # Error/Not Reached/Negative
IBM_RED_10 = "#fff1f1"       # Light red backgrounds
IBM_ORANGE_60 = "#eb6200"    # Warning/SMS channel
IBM_PURPLE_60 = "#8a3ffc"    # Alternative/Escalation
IBM_GRAY_10 = "#f4f4f4"      # Alternating row backgrounds
IBM_GRAY_50 = "#8d8d8d"      # Secondary text
IBM_GRAY_100 = "#161616"     # Primary text
DARK_GRAY = "#393939"        # Bar charts (ART Cases)
YELLOW_HIGHLIGHT = "#f1c21b" # Data labels on bars
LIGHT_BLUE = "#8ab8ff"       # Not yet tested

# Channel-Specific Colors
CHANNEL_COLORS = {
    "Emails": IBM_BLUE_60,
    "SMS": IBM_RED_60,
    "Calls": IBM_GREEN_60,
    "Confirmed Call": "#005d5d",
    "Expected Call": "#b45309",
}

# Standard chart dimensions
CHART_WIDTH = 720   # pixels (10 inches at 72 DPI)
CHART_HEIGHT = 432  # pixels (6 inches at 72 DPI)
SMALL_WIDTH = 350   # For small multiples
SMALL_HEIGHT = 260  # For small multiples

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

def _normalize_date(val) -> str:
    """
    Normalize a date value to YYYY-MM-DD format.
    Handles:
    - Already correct format: 2026-03-11
    - DateTime format: 2025-12-01 14:35:51
    - Pandas datetime objects
    - Empty/NaN values
    Returns empty string if invalid.
    """
    if val is None:
        return ""
    if isinstance(val, float) and pd.isna(val):
        return ""
    
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ("", "nan", "none", "nat"):
        return ""
    
    # Try to parse as datetime
    try:
        dt = pd.to_datetime(val_str, errors="coerce")
        if pd.isna(dt):
            return ""
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return ""

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

        # ── Step 1b: Complete missing Completion Dates with fallback hierarchy ───
        # Fallback 1: Last Status Change (if available)
        # Fallback 2: Earliest date from SMS/Email/Phone channels
        col_last_status = _find_col(pa, ["Last Status Change"])
        
        def _is_blank(v):
            if v is None: return True
            if isinstance(v, float) and pd.isna(v): return True
            return str(v).strip().lower() in ("", "nan", "none", "nat")
        
        # Count initial blanks
        before_fill = pa[col_date].apply(_is_blank).sum()
        
        # Fallback 1: Fill from Last Status Change
        if col_last_status:
            fill_mask = pa[col_date].apply(_is_blank)
            pa.loc[fill_mask, col_date] = pa.loc[fill_mask, col_last_status]
        
        # Fallback 2: Fill from channel dates (SMS/Email/Phone)
        remaining_blanks = pa[col_date].apply(_is_blank)
        if remaining_blanks.any():
            def get_fallback_date(case_num):
                if not _is_blank(case_num):
                    return self._get_date_from_channels(case_num)
                return ""
            
            fill_mask_2 = pa[col_date].apply(_is_blank)
            pa.loc[fill_mask_2, col_date] = pa.loc[fill_mask_2, "__case_num"].apply(get_fallback_date)
        
        # Count after all fallbacks
        after_fill = pa[col_date].apply(_is_blank).sum()
        filled_from_last_status = before_fill - after_fill
        remaining_blank = after_fill
        
        if filled_from_last_status > 0 or before_fill > 0:
            self._log(
                f"  Completion Date: filled {filled_from_last_status} from 'Last Status Change', "
                f"filled more from channel dates ({remaining_blank} still blank)"
            )
        
        # Normalize all dates to YYYY-MM-DD format
        pa[col_date] = pa[col_date].apply(_normalize_date)
        self._log("  All dates normalized to YYYY-MM-DD format")

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

        # ── Step 7: Generate charts as PNG images ──────────────────────────────
        self._log("Generating charts as PNG images...")
        try:
            from chart_generator import generate_all_charts
            charts = generate_all_charts(metrics, pa, col_date, col_wot)
            self._log(f"  ✓ Generated {len(charts)} chart images", "SUCCESS")
        except Exception as e:
            self._log(f"  ⚠ Chart generation failed: {e}", "WARNING")
            charts = {}
        
        # ── Step 8: Write Excel output ─────────────────────────────────────────
        self._log(f"Writing output to: {output_path}")
        self._write_excel(output_path, total_df, metrics, pa, col_fa, charts)

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

    def _get_date_from_channels(self, case_num: str) -> str:
        """
        Look up a case number in SMS/Email/Phone sheets and return the earliest
        'Date Created' or 'Entered Queue' date found, normalized to YYYY-MM-DD.
        Returns empty string if not found in any channel.
        """
        dates_found = []
        
        # SMS: look for Date Created
        if self.sms_df is not None:
            col = _find_col(self.sms_df, ["Date Created"])
            case_col = _find_col(self.sms_df, ["Case Number (Regarding) (Case)", "Case Number"])
            if col and case_col:
                mask = self.sms_df[case_col].apply(_normalize_case_num) == case_num
                if mask.any():
                    date_val = self.sms_df.loc[mask, col].iloc[0]
                    norm_dt = _normalize_date(date_val)
                    if norm_dt:
                        dates_found.append(norm_dt)
        
        # Email: look for Entered Queue
        if self.email_df is not None:
            col = _find_col(self.email_df, ["Entered Queue"])
            case_col = _find_col(self.email_df, ["Case Number (Object) (Email)", "Case Number"])
            if col and case_col:
                mask = self.email_df[case_col].apply(_normalize_case_num) == case_num
                if mask.any():
                    date_val = self.email_df.loc[mask, col].iloc[0]
                    norm_dt = _normalize_date(date_val)
                    if norm_dt:
                        dates_found.append(norm_dt)
        
        # Phone: look for Date Created
        if self.phone_df is not None:
            col = _find_col(self.phone_df, ["Date Created"])
            case_col = _find_col(self.phone_df, ["Case Number (Regarding) (Case)", "Case Number"])
            if col and case_col:
                mask = self.phone_df[case_col].apply(_normalize_case_num) == case_num
                if mask.any():
                    date_val = self.phone_df.loc[mask, col].iloc[0]
                    norm_dt = _normalize_date(date_val)
                    if norm_dt:
                        dates_found.append(norm_dt)
        
        # Return the earliest date found
        if dates_found:
            return min(dates_found)  # lexicographic sort works for YYYY-MM-DD
        return ""

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

        # ── Monthly breakdowns ─────────────────────────────────────────────---
        if col_date:
            pa["__month_period"] = pd.to_datetime(pa[col_date], errors="coerce").dt.to_period("M")
            months = sorted(pa["__month_period"].dropna().unique())
            # Helper to get mask for channel (calls = confirmed+expected)
            def ch_mask(df, ch):
                if ch == "Calls":
                    return df["Matching Channel"].str.contains("Confirmed Call|Expected Call", case=False, na=False)
                return df["Matching Channel"].str.contains(ch, case=False, na=False)

            # Breakdown 1: Total Numbers
            breakdown1 = []
            for period in months:
                m_mask = pa["__month_period"] == period
                m_sub  = pa[m_mask]
                sms    = len(m_sub[ch_mask(m_sub, "SMS")])
                email  = len(m_sub[ch_mask(m_sub, "Email")])
                calls  = len(m_sub[ch_mask(m_sub, "Calls")])
                gt     = sms + email + calls
                breakdown1.append({
                    "Month": period.strftime("%B %Y"),
                    "SMS": sms,
                    "Emails": email,
                    "Calls": calls,
                    "Grand Total": gt
                })
            if breakdown1:
                gt_row = {"Month": "Grand Total"}
                for k in ["SMS", "Emails", "Calls"]:
                    gt_row[k] = sum(r[k] for r in breakdown1)
                gt_row["Grand Total"] = sum(r["Grand Total"] for r in breakdown1)
                breakdown1.append(gt_row)
            metrics["monthly_total_numbers"] = pd.DataFrame(breakdown1)

            # Breakdown 2: Reached vs Not Reached
            breakdown2 = []
            for period in months:
                m_mask = pa["__month_period"] == period
                m_sub  = pa[m_mask]
                def reached(df, ch):
                    mask = ch_mask(df, ch)
                    return int((df[mask]["Reach Status"] == "Reached").sum())
                def not_reached(df, ch):
                    mask = ch_mask(df, ch)
                    return int((df[mask]["Reach Status"] == "Not Reached").sum())
                sms_r, sms_nr = reached(m_sub, "SMS"), not_reached(m_sub, "SMS")
                email_r, email_nr = reached(m_sub, "Email"), not_reached(m_sub, "Email")
                calls_r, calls_nr = reached(m_sub, "Calls"), not_reached(m_sub, "Calls")
                gt = sms_r + sms_nr + email_r + email_nr + calls_r + calls_nr
                breakdown2.append({
                    "Month": period.strftime("%B %Y"),
                    "SMS Reached": sms_r,
                    "SMS Not Reached": sms_nr,
                    "Emails Reached": email_r,
                    "Emails Not Reached": email_nr,
                    "Calls Reached": calls_r,
                    "Calls Not Reached": calls_nr,
                    "Grand Total": gt
                })
            if breakdown2:
                gt_row = {"Month": "Grand Total"}
                for k in ["SMS Reached", "SMS Not Reached", "Emails Reached", "Emails Not Reached", "Calls Reached", "Calls Not Reached"]:
                    gt_row[k] = sum(r[k] for r in breakdown2)
                gt_row["Grand Total"] = sum(r["Grand Total"] for r in breakdown2)
                breakdown2.append(gt_row)
            metrics["monthly_reached_vs_not"] = pd.DataFrame(breakdown2)

            # Breakdown 3: Each Channel Reach Rate (reached only) with correct GT and percentages
            breakdown3 = []
            for period in months:
                m_mask = pa["__month_period"] == period
                m_sub  = pa[m_mask]
                sms    = int((m_sub[ch_mask(m_sub, "SMS")]["Reach Status"] == "Reached").sum())
                email  = int((m_sub[ch_mask(m_sub, "Email")]["Reach Status"] == "Reached").sum())
                calls  = int((m_sub[ch_mask(m_sub, "Calls")]["Reach Status"] == "Reached").sum())
                gt     = sms + email + calls
                breakdown3.append({
                    "Month": period.strftime("%B %Y"),
                    "SMS": sms,
                    "Emails": email,
                    "Calls": calls,
                    "Grand Total": gt
                })
            if breakdown3:
                gt_row = {"Month": "Grand Total"}
                for k in ["SMS", "Emails", "Calls"]:
                    gt_row[k] = sum(r[k] for r in breakdown3)
                gt_row["Grand Total"] = sum(r["Grand Total"] for r in breakdown3)
                breakdown3.append(gt_row)
            metrics["monthly_channel_reach"] = pd.DataFrame(breakdown3)
            
            # Create monthly pivot data for the Monthly Breakdown sheet
            pivot_rows = []
            for period in months:
                m_mask = pa["__month_period"] == period
                m_sub = pa[m_mask]
                row = {"Month": period.strftime("%B %Y")}
                
                # For each channel: count and reach %
                for ch_label in ["Emails", "SMS", "Calls"]:
                    if ch_label == "Emails":
                        ch = "Email"
                    elif ch_label == "SMS":
                        ch = "SMS"
                    else:  # Calls
                        ch = "Calls"
                    
                    mask = ch_mask(m_sub, ch)
                    ch_sub = m_sub[mask]
                    count = len(ch_sub)
                    reached = int((ch_sub["Reach Status"] == "Reached").sum())
                    reach_pct = round(reached / count * 100, 1) if count > 0 else 0
                    
                    row[f"{ch_label}_Count"] = count
                    row[f"{ch_label}_Reach%"] = reach_pct
                
                # Grand Total
                row["Grand Total"] = len(m_sub)
                pivot_rows.append(row)
            
            # Add Grand Total row
            if pivot_rows:
                gt_row = {"Month": "Grand Total"}
                for ch_label in ["Emails", "SMS", "Calls"]:
                    gt_row[f"{ch_label}_Count"] = sum(r[f"{ch_label}_Count"] for r in pivot_rows)
                    # Weighted average for reach %
                    total_count = gt_row[f"{ch_label}_Count"]
                    if total_count > 0:
                        total_reached = sum(
                            r[f"{ch_label}_Count"] * r[f"{ch_label}_Reach%"] / 100
                            for r in pivot_rows
                        )
                        gt_row[f"{ch_label}_Reach%"] = round(total_reached / total_count * 100, 1)
                    else:
                        gt_row[f"{ch_label}_Reach%"] = 0
                gt_row["Grand Total"] = sum(r["Grand Total"] for r in pivot_rows)
                pivot_rows.append(gt_row)
            
            metrics["monthly_pivot"] = pd.DataFrame(pivot_rows)
            metrics["monthly_ch_cols"] = [("emails", "Emails"), ("sms", "SMS"), ("calls", "Calls")]
            
            # Prepare monthly chart data for chart generator
            chart_data = []
            for period in months:
                m_mask = pa["__month_period"] == period
                m_sub = pa[m_mask]
                
                # Calculate reach rates per channel
                email_mask = ch_mask(m_sub, "Email")
                sms_mask = ch_mask(m_sub, "SMS")
                calls_mask = ch_mask(m_sub, "Calls")
                
                email_count = len(m_sub[email_mask])
                sms_count = len(m_sub[sms_mask])
                calls_count = len(m_sub[calls_mask])
                
                email_reached = int((m_sub[email_mask]["Reach Status"] == "Reached").sum())
                sms_reached = int((m_sub[sms_mask]["Reach Status"] == "Reached").sum())
                calls_reached = int((m_sub[calls_mask]["Reach Status"] == "Reached").sum())
                
                email_rate = round(email_reached / email_count * 100, 1) if email_count > 0 else 0
                sms_rate = round(sms_reached / sms_count * 100, 1) if sms_count > 0 else 0
                calls_rate = round(calls_reached / calls_count * 100, 1) if calls_count > 0 else 0
                
                chart_data.append({
                    "Month": period.strftime("%B %Y"),
                    "ART Cases": len(m_sub),
                    "Emails": email_count,
                    "Email Rate": email_rate,
                    "SMS": sms_count,
                    "SMS Rate": sms_rate,
                    "Calls": calls_count,
                    "Calls Rate": calls_rate,
                })
            
            metrics["monthly_chart_data"] = pd.DataFrame(chart_data)

            # Breakdown 4: Work Order Type reach channels (reached only) as a single pivot table
            # Ignore blank work order types
            wot_types = [w for w in sorted(pa[col_wot].dropna().unique()) if str(w).strip().lower() != "(blank)" and str(w).strip() != ""] if col_wot else []
            pivot_data = {}
            for period in months:
                m_mask = pa["__month_period"] == period
                m_sub  = pa[m_mask]
                row = {"Month": period.strftime("%B %Y")}
                for wot in wot_types:
                    wot_mask = m_sub[col_wot] == wot
                    wot_sub = m_sub[wot_mask]
                    for ch in ["Emails", "SMS", "Calls"]:
                        if ch == "Emails":
                            count = int((wot_sub[ch_mask(wot_sub, "Email")]["Reach Status"] == "Reached").sum())
                        elif ch == "SMS":
                            count = int((wot_sub[ch_mask(wot_sub, "SMS")]["Reach Status"] == "Reached").sum())
                        elif ch == "Calls":
                            count = int((wot_sub[ch_mask(wot_sub, "Calls")]["Reach Status"] == "Reached").sum())
                        row[f"{wot}__{ch}"] = count
                pivot_data[period.strftime("%B %Y")] = row
            # Add Grand Total row
            if pivot_data:
                gt_row = {"Month": "Grand Total"}
                for wot in wot_types:
                    for ch in ["Emails", "SMS", "Calls"]:
                        gt_row[f"{wot}__{ch}"] = sum(pivot_data[m][f"{wot}__{ch}"] for m in pivot_data)
                pivot_data["Grand Total"] = gt_row
            # Convert to DataFrame
            metrics["monthly_wot_channel_reach_pivot"] = pd.DataFrame(list(pivot_data.values()))
        else:
            metrics["monthly_total_numbers"] = pd.DataFrame()
            metrics["monthly_reached_vs_not"] = pd.DataFrame()
            metrics["monthly_channel_reach"] = pd.DataFrame()
            metrics["monthly_wot_channel_reach"] = pd.DataFrame()

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
                     metrics: dict, pa: pd.DataFrame, col_fa: str, charts: Dict[str, bytes] = None):
        """
        Write Excel output with PNG chart images.
        
        Args:
            output_path: Path to output Excel file
            total_df: Total cases DataFrame
            metrics: Calculated metrics dictionary
            pa: PA Cases DataFrame
            col_fa: Final Action column name
            charts: Dictionary of chart names to PNG bytes (from chart_generator)
        """
        if charts is None:
            charts = {}
        
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
        # Sheet 2 — Overall Summary (with charts)
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

        # ── Monthly Overview Chart (Page 3) - PNG Image ────────────────────
        col_date = _find_col(pa, ["Completion Date"])
        if col_date:
            ws_ov.write(r, 0, "Monthly Overview", fmt_section)
            r += 1
            monthly_df = metrics.get("monthly_chart_data")
            if monthly_df is not None and not monthly_df.empty:
                # Write monthly data table
                headers = ["Month", "ART Cases", "Emails", "Email Rate", "SMS", "SMS Rate", "Calls", "Calls Rate"]
                for ci, h in enumerate(headers):
                    ws_ov.write(r, ci, h, fmt_header)
                for ri, row in monthly_df.iterrows():
                    r_idx = r + 1 + list(monthly_df.index).index(ri)
                    for ci, h in enumerate(headers):
                        val = row[h]
                        ws_ov.write(r_idx, ci, val, fmt_row)
                
                # Insert PNG chart image
                if 'monthly_overview' in charts:
                    chart_row = r + len(monthly_df) + 2
                    ws_ov.insert_image(chart_row, 0, 'monthly_overview.png',
                                      {'image_data': io.BytesIO(charts['monthly_overview'])})
                    r = chart_row + 25  # Space for chart image
                else:
                    r += len(monthly_df) + 2
        
        # ── Resolution Status Chart (Page 4) - PNG Image ───────────────────
        if col_date and 'resolution_status' in charts:
            ws_ov.write(r, 0, "Resolution Status Breakdown", fmt_section)
            r += 1
            ws_ov.insert_image(r, 0, 'resolution_status.png',
                              {'image_data': io.BytesIO(charts['resolution_status'])})
            r += 25  # Space for chart image

        # ── Channel Comparison table (core ask) ──────────────────────────────
        ws_ov.write(r, 0, "Channel Reach Rate Comparison", fmt_section)
        r += 1
        ch_sum_df = metrics.get("channel_summary")
        if ch_sum_df is not None and len(ch_sum_df) > 0:
            tbl_r = r
            ds, de = _write_table(ws_ov, ch_sum_df, r)
            r = de + 2

        # ── Overall reach rate table ────────────────────────────────────────
        ws_ov.write(r, 0, "Overall Reach Rate (all channels)", fmt_section)
        r += 1
        reach_df = metrics.get("overall_reach")
        if reach_df is not None:
            tbl_r = r
            ds, de = _write_table(ws_ov, reach_df, r)
            r = de + 2

        # ── Final action distribution + pie chart ───────────────────────────
        ws_ov.write(r, 0, "Final Action Distribution (All Cases)", fmt_section)
        r += 1
        fa_df = metrics.get("final_action_all")
        if fa_df is not None:
            tbl_r = r
            ds, de = _write_table(ws_ov, fa_df, r)
            r = de + 2
        
        # Add PNG pie chart for Final Action distribution
        if 'final_action_pie' in charts:
            ws_ov.write(r, 0, "Final Action Breakdown (Visual)", fmt_section)
            r += 1
            ws_ov.insert_image(r, 0, 'final_action_pie.png',
                              {'image_data': io.BytesIO(charts['final_action_pie'])})
            r += 25  # Space for chart image

        self._log("  Written: Overall Summary sheet with charts")

        # ==================================================================
        # Sheets: SDT Analysis (Pages 7-9: DEPOT, ONSITE, CRU)
        # ==================================================================
        col_wot = None
        for col in pa.columns:
            if "work order type" in col.lower():
                col_wot = col
                break
        
        if col_wot and col_date:
            # SDT Analysis sheets - Add data tables BEFORE charts
            sdt_types = [
                ('Depot', 'sdt_depot', 'DEPOT SDT Analysis', 'DEPOT Service Delivery Type Analysis'),
                ('Onsite', 'sdt_onsite', 'ONSITE SDT Analysis', 'ONSITE Service Delivery Type Analysis'),
                ('CRU', 'sdt_cru', 'CRU SDT Analysis', 'CRU Service Delivery Type Analysis')
            ]
            
            for sdt_name, chart_key, sheet_name, title in sdt_types:
                if chart_key in charts:
                    ws_sdt = workbook.add_worksheet(sheet_name)
                    _setup_metrics_sheet(ws_sdt)
                    r = 0
                    ws_sdt.write(r, 0, title, fmt_title)
                    r += 2
                    
                    # Add data table showing monthly breakdown
                    monthly_chart_data = metrics.get('monthly_chart_data')
                    if monthly_chart_data is not None and not monthly_chart_data.empty:
                        # Filter for this SDT type
                        sdt_mask = pa[col_wot].astype(str).str.lower().str.contains(sdt_name.lower(), case=False, na=False)
                        sdt_df = pa[sdt_mask]
                        
                        if len(sdt_df) > 0:
                            # Prepare monthly data for this SDT
                            from chart_generator import _prepare_monthly_chart_data
                            sdt_monthly = _prepare_monthly_chart_data(sdt_df, col_date)
                            
                            if not sdt_monthly.empty:
                                ws_sdt.write(r, 0, "Monthly Breakdown", fmt_section)
                                r += 1
                                headers = ["Month", "ART Cases", "Emails", "Email Rate", "SMS", "SMS Rate", "Calls", "Calls Rate"]
                                for ci, h in enumerate(headers):
                                    ws_sdt.write(r, ci, h, fmt_header)
                                for ri, row in sdt_monthly.iterrows():
                                    r_idx = r + 1 + list(sdt_monthly.index).index(ri)
                                    for ci, h in enumerate(headers):
                                        val = row[h]
                                        ws_sdt.write(r_idx, ci, val, fmt_row)
                                r = r + len(sdt_monthly) + 2
                    
                    # Insert PNG chart image
                    ws_sdt.write(r, 0, "Visual Analysis", fmt_section)
                    r += 1
                    ws_sdt.insert_image(r, 0, f'{chart_key}.png',
                                       {'image_data': io.BytesIO(charts[chart_key])})
                    self._log(f"  Written: {sheet_name} sheet with table and PNG chart")

        # ==================================================================
        # Sheets 4–7 — Per-channel metric sheets
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
            r = de + 2
            
            # ── Add Pie Chart for Final Action Distribution ────────────────
            pie_chart_key = f'{ch_key}_fa_pie'
            if pie_chart_key in charts:
                ws_ch.write(r, 0, "Final Action Distribution (Visual)", fmt_section)
                r += 1
                ws_ch.insert_image(r, 0, f'{pie_chart_key}.png',
                                  {'image_data': io.BytesIO(charts[pie_chart_key])})
                r += 20  # Space for chart

            self._log(f"  Written: {sheet_name} sheet ({total_ch} cases) with pie chart")

        # ==================================================================
        # Sheet: Monthly Breakdown  &  By Work Order Type
        # ==================================================================
        # Write new monthly breakdown sheets
        def write_simple_table(ws, df, title):
            ws.set_zoom(90)
            ws.freeze_panes(1, 0)
            ws.set_row(0, 24)
            ws.write(0, 0, title, fmt_title)
            # Write headers
            for ci, col in enumerate(df.columns):
                ws.write(1, ci, col, fmt_header)
            # Write data
            for ri, row in enumerate(df.itertuples(index=False), start=2):
                for ci, val in enumerate(row):
                    ws.write(ri, ci, val, fmt_row)

        # Sheet: Monthly Breakdown 1 - Total Numbers (with chart)
        df1 = metrics.get("monthly_total_numbers")
        if df1 is not None and not df1.empty:
            ws1 = workbook.add_worksheet("Monthly Total Numbers")
            write_simple_table(ws1, df1, "Monthly Breakdown: Total Numbers")
            
            # Add stacked column chart
            if 'monthly_total_numbers' in charts:
                row_after_table = len(df1) + 3
                ws1.write(row_after_table, 0, "Visual Breakdown", fmt_section)
                ws1.insert_image(row_after_table + 1, 0, 'monthly_total_numbers.png',
                                {'image_data': io.BytesIO(charts['monthly_total_numbers'])})

        # Sheet: Monthly Breakdown 2 - Reached vs Not Reached (with chart)
        df2 = metrics.get("monthly_reached_vs_not")
        if df2 is not None and not df2.empty:
            ws2 = workbook.add_worksheet("Monthly Reached vs Not")
            write_simple_table(ws2, df2, "Monthly Breakdown: Reached vs Not Reached")
            
            # Add grouped bar chart
            if 'monthly_reached_vs_not' in charts:
                row_after_table = len(df2) + 3
                ws2.write(row_after_table, 0, "Visual Comparison", fmt_section)
                ws2.insert_image(row_after_table + 1, 0, 'monthly_reached_vs_not.png',
                                {'image_data': io.BytesIO(charts['monthly_reached_vs_not'])})

        # Sheet: Monthly Breakdown 3 - Channel Reach Rate (Reached Only) (pivot style)
        df3 = metrics.get("monthly_channel_reach")
        if df3 is not None and not df3.empty:
            ws3 = workbook.add_worksheet("Monthly Channel Reach")
            ws3.set_zoom(90)
            ws3.freeze_panes(1, 0)
            ws3.set_row(0, 24)
            ws3.write(0, 0, "Monthly Reach Rate by Communication Channel (Reached Cases Only)", fmt_title)
            # Headers
            headers = ["Month", "Emails", "SMS", "Calls", "Grand Total"]
            for ci, h in enumerate(headers):
                ws3.write(1, ci, h, fmt_header)
            # Data rows
            for ri, row in enumerate(df3.itertuples(index=False), start=2):
                ws3.write(ri, 0, getattr(row, "Month"), fmt_row)
                # Emails
                ws3.write(ri, 1, getattr(row, "Emails"), fmt_row)
                # SMS
                ws3.write(ri, 2, getattr(row, "SMS"), fmt_row)
                # Calls
                ws3.write(ri, 3, getattr(row, "Calls"), fmt_row)
                # Grand Total
                gt = getattr(row, "Grand Total", 0)
                ws3.write(ri, 4, gt, fmt_row)

        # Sheet: Monthly Breakdown 4 - Work Order Type Channel Reach (single pivot table)
        df4 = metrics.get("monthly_wot_channel_reach_pivot")
        if df4 is not None and not df4.empty:
            wot_types = []
            for col in df4.columns:
                if col != "Month":
                    wot, ch = col.split("__")
                    if wot not in wot_types:
                        wot_types.append(wot)
            channels = ["Emails", "SMS", "Calls"]
            ws4 = workbook.add_worksheet("Monthly WOT Channel Reach")
            ws4.set_zoom(90)
            ws4.freeze_panes(2, 1)
            ws4.set_row(0, 24)
            ws4.write(0, 0, "Monthly Reach Rate by Work Order Type and Channel (Reached Only)", fmt_title)
            # Build headers
            col = 1
            for wot in wot_types:
                ws4.merge_range(1, col, 1, col+2, wot, fmt_header)
                for ci, ch in enumerate(channels):
                    ws4.write(2, col+ci, ch, fmt_header)
                col += 3
            ws4.write(1, 0, "Month", fmt_header)
            ws4.write(2, 0, "Month", fmt_header)
            # Write data
            for ri, row in enumerate(df4.itertuples(index=False), start=3):
                ws4.write(ri, 0, getattr(row, "Month"), fmt_row)
                col = 1
                for wot in wot_types:
                    for ch in channels:
                        val = getattr(row, f"{wot}__{ch}", 0)
                        ws4.write(ri, col, val, fmt_row)
                        col += 1

        # Keep original monthly and WOT sheets for reference
        self._add_monthly_sheet(workbook, metrics,
                                 fmt_title, fmt_header, fmt_row, fmt_row_alt, fmt_section)
        self._add_wot_sheet(workbook, metrics,
                             fmt_title, fmt_header, fmt_row, fmt_row_alt, fmt_section, charts)

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
                        fmt_title, fmt_header, fmt_row, fmt_row_alt, fmt_section, charts: Dict[str, bytes] = None):
        if charts is None:
            charts = {}
        
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
        
        # Add horizontal bar chart for WOT reach rates
        if 'wot_reach_rate' in charts:
            row_after_table = len(wot_df) + 5
            ws.write(row_after_table, 0, "Visual Comparison", fmt_section)
            ws.insert_image(row_after_table + 1, 0, 'wot_reach_rate.png',
                           {'image_data': io.BytesIO(charts['wot_reach_rate'])})
