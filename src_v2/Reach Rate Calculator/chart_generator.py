"""
Chart Generator for Reach Rate Calculator
==========================================
Generates professional charts as PNG images using matplotlib/seaborn
for insertion into Excel workbooks.

Uses IBM Carbon Design System colors and styling.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
import io
from typing import Optional, Tuple, List, Dict, Union
import numpy as np

# ── IBM Carbon Design System Colors ────────────────────────────────────────────

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

CHANNEL_COLORS = {
    "Emails": IBM_BLUE_60,
    "SMS": IBM_RED_60,
    "Calls": IBM_GREEN_60,
    "Confirmed Call": "#005d5d",
    "Expected Call": "#b45309",
}

# Standard chart dimensions (in inches for matplotlib)
CHART_WIDTH = 10   # inches
CHART_HEIGHT = 6   # inches
DPI = 100          # dots per inch

# ── Chart Generator Class ───────────────────────────────────────────────────────

class ReachRateChartGenerator:
    """
    Generates professional charts for Reach Rate Calculator reports.
    All charts are generated as PNG images with IBM Carbon styling.
    """
    
    def __init__(self):
        """Initialize chart generator with IBM styling."""
        # Set IBM Plex Sans font if available, fallback to sans-serif
        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = ['IBM Plex Sans', 'Arial', 'Helvetica']
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 11
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['legend.fontsize'] = 10
        
        # Set matplotlib style (whitegrid equivalent without seaborn)
        plt.rcParams['axes.edgecolor'] = '#e0e0e0'
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.color'] = '#e0e0e0'
        plt.rcParams['grid.linestyle'] = '-'
        plt.rcParams['grid.linewidth'] = 0.5
        plt.rcParams['axes.facecolor'] = 'white'
        plt.rcParams['figure.facecolor'] = 'white'
    
    def _save_to_bytes(self, fig: Figure) -> bytes:
        """Save figure to bytes buffer."""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=DPI, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        buf.seek(0)
        return buf.getvalue()
    
    def create_monthly_overview_chart(self, monthly_df: pd.DataFrame) -> bytes:
        """
        Create Page 3 chart: Monthly Overview - Combo chart (Bar + Line)
        Shows ART Cases volume with Email/SMS/Calls reach rate lines.
        
        Args:
            monthly_df: DataFrame with columns: Month, ART Cases, Email Rate, SMS Rate, Calls Rate
        
        Returns:
            PNG image as bytes
        """
        fig, ax1 = plt.subplots(figsize=(CHART_WIDTH, CHART_HEIGHT))
        
        # Bar chart for ART Cases (primary axis)
        x = np.arange(len(monthly_df))
        bars = ax1.bar(x, monthly_df['ART Cases'], color=DARK_GRAY, 
                       width=0.6, label='ART Cases', zorder=2)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}',
                    ha='center', va='bottom', fontsize=11, 
                    fontweight='bold', color=YELLOW_HIGHLIGHT,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor=DARK_GRAY, 
                             edgecolor='none', alpha=0.8))
        
        ax1.set_xlabel('Month', fontsize=11, fontweight='bold')
        ax1.set_ylabel('ART Cases', fontsize=11, fontweight='bold', color=DARK_GRAY)
        ax1.tick_params(axis='y', labelcolor=DARK_GRAY)
        ax1.set_xticks(x)
        ax1.set_xticklabels(monthly_df['Month'], rotation=0)
        ax1.set_ylim(0, monthly_df['ART Cases'].max() * 1.15)
        ax1.grid(True, axis='y', alpha=0.3, zorder=1)
        
        # Line charts for reach rates (secondary axis)
        ax2 = ax1.twinx()
        
        ax2.plot(x, monthly_df['Email Rate'], color=IBM_BLUE_60, 
                marker='o', markersize=8, linewidth=2.5, label='Emails', zorder=3)
        ax2.plot(x, monthly_df['SMS Rate'], color=IBM_ORANGE_60, 
                marker='o', markersize=8, linewidth=2.5, label='SMS', zorder=3)
        ax2.plot(x, monthly_df['Calls Rate'], color=IBM_GREEN_60, 
                marker='o', markersize=8, linewidth=2.5, label='Calls', zorder=3)
        
        ax2.set_ylabel('Reach Rate %', fontsize=11, fontweight='bold')
        ax2.set_ylim(0, 50)
        ax2.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{int(y)}%'))
        
        # Title
        plt.title('Overall Monthly Project ART Case Volume & Reach Attempt Performance',
                 fontsize=14, fontweight='bold', color=IBM_GRAY_100, pad=20)
        
        # Combined legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, 
                  loc='upper center', bbox_to_anchor=(0.5, -0.08),
                  ncol=4, frameon=False)
        
        plt.tight_layout()
        return self._save_to_bytes(fig)
    
    def create_resolution_status_chart(self, status_df: pd.DataFrame) -> bytes:
        """
        Create Page 4 chart: Resolution Status - Stacked bar chart
        Shows percentage breakdown of resolution statuses by month.
        
        Args:
            status_df: DataFrame with columns: Month, Reached %, Not Reached %
        
        Returns:
            PNG image as bytes
        """
        fig, ax = plt.subplots(figsize=(CHART_WIDTH, CHART_HEIGHT))
        
        # Horizontal stacked bar chart
        y = np.arange(len(status_df))
        
        ax.barh(y, status_df['Reached'], color=IBM_GREEN_60, label='Reached')
        ax.barh(y, status_df['Not Reached'], left=status_df['Reached'], 
               color=IBM_RED_60, label='Not Reached')
        
        # Add percentage labels
        for i, (reached, not_reached) in enumerate(zip(status_df['Reached'], status_df['Not Reached'])):
            # Reached label
            if reached > 5:
                ax.text(reached/2, i, f'{reached:.1f}%', 
                       ha='center', va='center', fontsize=9, 
                       fontweight='bold', color='white')
            # Not Reached label
            if not_reached > 5:
                ax.text(reached + not_reached/2, i, f'{not_reached:.1f}%',
                       ha='center', va='center', fontsize=9,
                       fontweight='bold', color='white')
        
        ax.set_yticks(y)
        ax.set_yticklabels(status_df['Month'])
        ax.set_xlabel('Percentage', fontsize=11, fontweight='bold')
        ax.set_xlim(0, 100)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x)}%'))
        ax.invert_yaxis()  # Months from top to bottom
        ax.grid(True, axis='x', alpha=0.3)
        
        plt.title('Resolution Status Breakdown', fontsize=14, 
                 fontweight='bold', color=IBM_GRAY_100, pad=20)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.08),
                 ncol=2, frameon=False)
        
        plt.tight_layout()
        return self._save_to_bytes(fig)
    
    def create_sdt_analysis_chart(self, monthly_df: pd.DataFrame, sdt_type: str) -> bytes:
        """
        Create SDT Analysis chart (Pages 7-9): Combo chart for DEPOT/ONSITE/CRU
        Shows ART Cases volume with Email/SMS/Calls reach rate lines by SDT type.
        
        Args:
            monthly_df: DataFrame with monthly data for specific SDT
            sdt_type: 'Depot', 'Onsite', or 'CRU'
        
        Returns:
            PNG image as bytes
        """
        fig, ax1 = plt.subplots(figsize=(CHART_WIDTH, CHART_HEIGHT))
        
        # Bar chart for ART Cases
        x = np.arange(len(monthly_df))
        bars = ax1.bar(x, monthly_df['ART Cases'], color=DARK_GRAY, 
                       width=0.6, label='ART Cases', zorder=2)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}',
                    ha='center', va='bottom', fontsize=10, 
                    fontweight='bold', color=YELLOW_HIGHLIGHT,
                    bbox=dict(boxstyle='round,pad=0.3', facecolor=DARK_GRAY, 
                             edgecolor='none', alpha=0.8))
        
        ax1.set_xlabel('Month', fontsize=11, fontweight='bold')
        ax1.set_ylabel('ART Cases', fontsize=11, fontweight='bold', color=DARK_GRAY)
        ax1.tick_params(axis='y', labelcolor=DARK_GRAY)
        ax1.set_xticks(x)
        ax1.set_xticklabels(monthly_df['Month'], rotation=0)
        ax1.set_ylim(0, monthly_df['ART Cases'].max() * 1.15)
        ax1.grid(True, axis='y', alpha=0.3, zorder=1)
        
        # Line charts for reach rates
        ax2 = ax1.twinx()
        
        ax2.plot(x, monthly_df['Email Rate'], color=IBM_BLUE_60, 
                marker='o', markersize=8, linewidth=2.5, label='Emails', zorder=3)
        ax2.plot(x, monthly_df['SMS Rate'], color=IBM_ORANGE_60, 
                marker='o', markersize=8, linewidth=2.5, label='SMS', zorder=3)
        ax2.plot(x, monthly_df['Calls Rate'], color=IBM_GREEN_60, 
                marker='o', markersize=8, linewidth=2.5, label='Calls', zorder=3)
        
        ax2.set_ylabel('Reach Rate %', fontsize=11, fontweight='bold')
        ax2.set_ylim(0, 50)
        ax2.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{int(y)}%'))
        
        # Title
        plt.title(f'How are {sdt_type.upper()} Customers Responding to Project ART Follow-ups?',
                 fontsize=14, fontweight='bold', color=IBM_GRAY_100, pad=20)
        
        # Combined legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, 
                  loc='upper center', bbox_to_anchor=(0.5, -0.08),
                  ncol=4, frameon=False)
        
        plt.tight_layout()
        return self._save_to_bytes(fig)
    
    def create_final_action_pie_chart(self, fa_counts: pd.Series) -> bytes:
        """
        Create pie chart showing Final Action distribution.
        
        Args:
            fa_counts: Series with Final Action counts
        
        Returns:
            PNG image as bytes
        """
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Take top 10, group rest as "Other"
        if len(fa_counts) > 10:
            top_10 = fa_counts.head(10)
            other_count = fa_counts[10:].sum()
            fa_counts = pd.concat([top_10, pd.Series({'Other': other_count})])
        
        # Colors
        colors = [
            IBM_BLUE_60, IBM_ORANGE_60, IBM_GREEN_60, IBM_PURPLE_60,
            YELLOW_HIGHLIGHT, '#005d5d', '#6929c4', '#b45309',
            LIGHT_BLUE, IBM_RED_60, IBM_GRAY_50
        ]
        
        # Create pie chart
        pie_result = ax.pie(fa_counts, labels=list(fa_counts.index),
                           autopct='%1.1f%%', startangle=90,
                           colors=colors[:len(fa_counts)],
                           textprops={'fontsize': 9})
        
        # Make percentage text bold and white
        if len(pie_result) == 3:
            wedges, texts, autotexts = pie_result
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(10)
        
        plt.title('Final Action Distribution', fontsize=14, 
                 fontweight='bold', color=IBM_GRAY_100, pad=20)
        
        plt.tight_layout()
        return self._save_to_bytes(fig)
    
    def create_channel_comparison_chart(self, channel_df: pd.DataFrame) -> bytes:
        """
        Create channel comparison bar chart.
        
        Args:
            channel_df: DataFrame with columns: Channel, Cases, Reach Rate (%)
        
        Returns:
            PNG image as bytes
        """
        fig, ax = plt.subplots(figsize=(CHART_WIDTH, CHART_HEIGHT))
        
        # Horizontal bar chart
        y = np.arange(len(channel_df))
        colors_list = [CHANNEL_COLORS.get(ch, IBM_BLUE_60) for ch in channel_df['Channel']]
        
        bars = ax.barh(y, channel_df['Reach Rate (%)'], color=colors_list)
        
        # Add value labels
        for i, (bar, rate) in enumerate(zip(bars, channel_df['Reach Rate (%)'])):
            ax.text(rate + 1, bar.get_y() + bar.get_height()/2,
                   f'{rate:.1f}%',
                   ha='left', va='center', fontsize=10, fontweight='bold')
        
        ax.set_yticks(y)
        ax.set_yticklabels(channel_df['Channel'])
        ax.set_xlabel('Reach Rate %', fontsize=11, fontweight='bold')
        ax.set_xlim(0, 100)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x)}%'))
        ax.invert_yaxis()
        ax.grid(True, axis='x', alpha=0.3)
        
        plt.title('Channel Reach Rate Comparison', fontsize=14,
                 fontweight='bold', color=IBM_GRAY_100, pad=20)
        
        plt.tight_layout()
        return self._save_to_bytes(fig)
    
    def create_channel_final_action_pie(self, fa_counts: pd.Series, channel_name: str) -> bytes:
        """
        Create pie chart for a specific channel's Final Action distribution.
        
        Args:
            fa_counts: Series with Final Action counts for this channel
            channel_name: Name of the channel (e.g., "SMS", "Email")
        
        Returns:
            PNG image as bytes
        """
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Take top 8, group rest as "Other"
        if len(fa_counts) > 8:
            top_8 = fa_counts.head(8)
            other_count = fa_counts[8:].sum()
            fa_counts = pd.concat([top_8, pd.Series({'Other': other_count})])
        
        # Colors
        colors = [
            IBM_BLUE_60, IBM_ORANGE_60, IBM_GREEN_60, IBM_PURPLE_60,
            YELLOW_HIGHLIGHT, '#005d5d', '#6929c4', '#b45309',
            IBM_GRAY_50
        ]
        
        # Create pie chart
        pie_result = ax.pie(fa_counts, labels=list(fa_counts.index),
                           autopct='%1.1f%%', startangle=90,
                           colors=colors[:len(fa_counts)],
                           textprops={'fontsize': 9})
        
        # Make percentage text bold and white
        if len(pie_result) == 3:
            wedges, texts, autotexts = pie_result
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(10)
        
        plt.title(f'{channel_name} - Final Action Distribution', fontsize=14,
                 fontweight='bold', color=IBM_GRAY_100, pad=20)
        
        plt.tight_layout()
        return self._save_to_bytes(fig)
    
    def create_monthly_stacked_column(self, monthly_df: pd.DataFrame) -> bytes:
        """
        Create stacked column chart for monthly channel volumes.
        
        Args:
            monthly_df: DataFrame with Month, SMS, Emails, Calls columns
        
        Returns:
            PNG image as bytes
        """
        fig, ax = plt.subplots(figsize=(CHART_WIDTH, CHART_HEIGHT))
        
        x = np.arange(len(monthly_df))
        width = 0.6
        
        # Stacked bars
        p1 = ax.bar(x, monthly_df['Emails'], width, label='Emails',
                   color=IBM_BLUE_60)
        p2 = ax.bar(x, monthly_df['SMS'], width, bottom=monthly_df['Emails'],
                   label='SMS', color=IBM_ORANGE_60)
        p3 = ax.bar(x, monthly_df['Calls'], width,
                   bottom=monthly_df['Emails'] + monthly_df['SMS'],
                   label='Calls', color=IBM_GREEN_60)
        
        ax.set_xlabel('Month', fontsize=11, fontweight='bold')
        ax.set_ylabel('Number of Cases', fontsize=11, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(monthly_df['Month'], rotation=45, ha='right')
        ax.legend(loc='upper left', frameon=False)
        ax.grid(True, axis='y', alpha=0.3)
        
        plt.title('Monthly Channel Volume Distribution', fontsize=14,
                 fontweight='bold', color=IBM_GRAY_100, pad=20)
        
        plt.tight_layout()
        return self._save_to_bytes(fig)
    
    def create_monthly_grouped_bars(self, monthly_df: pd.DataFrame) -> bytes:
        """
        Create grouped bar chart for reached vs not reached by month.
        
        Args:
            monthly_df: DataFrame with Month, Reached, Not Reached columns
        
        Returns:
            PNG image as bytes
        """
        fig, ax = plt.subplots(figsize=(CHART_WIDTH, CHART_HEIGHT))
        
        x = np.arange(len(monthly_df))
        width = 0.35
        
        # Grouped bars
        ax.bar(x - width/2, monthly_df['Reached'], width, label='Reached',
              color=IBM_GREEN_60)
        ax.bar(x + width/2, monthly_df['Not Reached'], width, label='Not Reached',
              color=IBM_RED_60)
        
        ax.set_xlabel('Month', fontsize=11, fontweight='bold')
        ax.set_ylabel('Number of Cases', fontsize=11, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(monthly_df['Month'], rotation=45, ha='right')
        ax.legend(loc='upper left', frameon=False)
        ax.grid(True, axis='y', alpha=0.3)
        
        plt.title('Monthly Reached vs Not Reached', fontsize=14,
                 fontweight='bold', color=IBM_GRAY_100, pad=20)
        
        plt.tight_layout()
        return self._save_to_bytes(fig)
    
    def create_wot_horizontal_bars(self, wot_df: pd.DataFrame) -> bytes:
        """
        Create horizontal bar chart for Work Order Type reach rates.
        
        Args:
            wot_df: DataFrame with WOT and reach rate columns
        
        Returns:
            PNG image as bytes
        """
        fig, ax = plt.subplots(figsize=(CHART_WIDTH, CHART_HEIGHT))
        
        # Sort by reach rate descending
        wot_df = wot_df.sort_values('Overall Reach Rate (%)', ascending=True)
        
        y = np.arange(len(wot_df))
        bars = ax.barh(y, wot_df['Overall Reach Rate (%)'], color=IBM_BLUE_60)
        
        # Add value labels
        for i, (bar, rate) in enumerate(zip(bars, wot_df['Overall Reach Rate (%)'])):
            ax.text(rate + 1, bar.get_y() + bar.get_height()/2,
                   f'{rate:.1f}%',
                   ha='left', va='center', fontsize=10, fontweight='bold')
        
        ax.set_yticks(y)
        ax.set_yticklabels(wot_df['Work Order Type'])
        ax.set_xlabel('Reach Rate %', fontsize=11, fontweight='bold')
        ax.set_xlim(0, 100)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{int(x)}%'))
        ax.grid(True, axis='x', alpha=0.3)
        
        plt.title('Reach Rate by Work Order Type', fontsize=14,
                 fontweight='bold', color=IBM_GRAY_100, pad=20)
        
        plt.tight_layout()
        return self._save_to_bytes(fig)
    
    def close_all(self):
        """Close all matplotlib figures to free memory."""
        plt.close('all')


# ── Convenience Functions ───────────────────────────────────────────────────────

def generate_all_charts(metrics: dict, pa: pd.DataFrame, col_date: str, 
                       col_wot: Optional[str] = None) -> Dict[str, bytes]:
    """
    Generate all charts for the Reach Rate Calculator report.
    
    Args:
        metrics: Dictionary of calculated metrics
        pa: Main PA Cases DataFrame
        col_date: Completion Date column name
        col_wot: Work Order Type column name (optional)
    
    Returns:
        Dictionary mapping chart names to PNG bytes
    """
    generator = ReachRateChartGenerator()
    charts = {}
    
    try:
        # Monthly Overview Chart (Page 3)
        monthly_df = metrics.get('monthly_chart_data')
        if monthly_df is not None and not monthly_df.empty:
            charts['monthly_overview'] = generator.create_monthly_overview_chart(monthly_df)
        
        # Resolution Status Chart (Page 4)
        if col_date and col_date in pa.columns:
            pa_copy = pa.copy()
            pa_copy["__month_period"] = pd.to_datetime(pa_copy[col_date], errors="coerce").dt.to_period("M")
            months = sorted(pa_copy["__month_period"].dropna().unique())
            
            if months:
                status_data = []
                for period in months:
                    m_mask = pa_copy["__month_period"] == period
                    m_sub = pa_copy[m_mask]
                    total = len(m_sub)
                    
                    if total > 0:
                        reached = int((m_sub["Reach Status"] == "Reached").sum())
                        not_reached = int((m_sub["Reach Status"] == "Not Reached").sum())
                        
                        status_data.append({
                            "Month": period.strftime("%B %Y"),
                            "Reached": round(reached / total * 100, 1),
                            "Not Reached": round(not_reached / total * 100, 1)
                        })
                
                if status_data:
                    status_df = pd.DataFrame(status_data)
                    charts['resolution_status'] = generator.create_resolution_status_chart(status_df)
        
        # SDT Analysis Charts (Pages 7-9)
        if col_wot and col_date:
            for sdt_type in ['Depot', 'Onsite', 'CRU']:
                sdt_mask = pa[col_wot].astype(str).str.lower().str.contains(sdt_type.lower(), case=False, na=False)
                sdt_df = pa[sdt_mask]
                
                if isinstance(sdt_df, pd.DataFrame) and len(sdt_df) > 0:
                    # Prepare monthly data for this SDT
                    sdt_monthly = _prepare_monthly_chart_data(sdt_df, col_date)
                    if not sdt_monthly.empty:
                        charts[f'sdt_{sdt_type.lower()}'] = generator.create_sdt_analysis_chart(
                            sdt_monthly, sdt_type
                        )
        
        # Final Action Pie Chart (Overall)
        fa_col = None
        for col in pa.columns:
            if 'final action' in col.lower():
                fa_col = col
                break
        
        if fa_col:
            fa_series = pa[fa_col].fillna("(blank)").apply(
                lambda v: "" if (isinstance(v, float) and pd.isna(v)) else str(v).strip()
            ).replace("", "(blank)")
            fa_counts = fa_series.value_counts()
            
            if len(fa_counts) > 0:
                charts['final_action_pie'] = generator.create_final_action_pie_chart(fa_counts)
            
            # Per-Channel Final Action Pie Charts
            if "Matching Channel" in pa.columns:
                channel_filters = {
                    'sms': ('SMS', 'sms'),
                    'email': ('Email', 'email'),
                    'confirmed_call': ('Confirmed Call', 'confirmed call'),
                    'expected_call': ('Expected Call', 'expected call')
                }
                
                for key, (label, pattern) in channel_filters.items():
                    ch_mask = pa["Matching Channel"].astype(str).str.contains(pattern, case=False, na=False)
                    ch_df = pa[ch_mask]
                    
                    if len(ch_df) > 0:
                        ch_fa_series = ch_df[fa_col].fillna("(blank)").apply(
                            lambda v: "" if (isinstance(v, float) and pd.isna(v)) else str(v).strip()
                        ).replace("", "(blank)")
                        ch_fa_counts = ch_fa_series.value_counts()
                        
                        if len(ch_fa_counts) > 0:
                            charts[f'{key}_fa_pie'] = generator.create_channel_final_action_pie(
                                ch_fa_counts, label
                            )
        
        # Channel Comparison Chart
        channel_summary = metrics.get('channel_summary')
        if channel_summary is not None and not channel_summary.empty:
            charts['channel_comparison'] = generator.create_channel_comparison_chart(channel_summary)
        
        # Monthly Total Numbers Chart (Stacked Column)
        monthly_total_df = metrics.get('monthly_total_numbers')
        if monthly_total_df is not None and not monthly_total_df.empty:
            if all(col in monthly_total_df.columns for col in ['Month', 'SMS', 'Emails', 'Calls']):
                charts['monthly_total_numbers'] = generator.create_monthly_stacked_column(monthly_total_df)
        
        # Monthly Reached vs Not Reached Chart (Grouped Bars)
        monthly_reached_df = metrics.get('monthly_reached_vs_not')
        if monthly_reached_df is not None and not monthly_reached_df.empty:
            if all(col in monthly_reached_df.columns for col in ['Month', 'Reached', 'Not Reached']):
                charts['monthly_reached_vs_not'] = generator.create_monthly_grouped_bars(monthly_reached_df)
        
        # Work Order Type Chart (Horizontal Bars)
        wot_summary = metrics.get('wot_summary')
        if wot_summary is not None and not wot_summary.empty:
            if 'Work Order Type' in wot_summary.columns and 'Overall Reach Rate (%)' in wot_summary.columns:
                charts['wot_reach_rate'] = generator.create_wot_horizontal_bars(wot_summary)
        
    finally:
        generator.close_all()
    
    return charts


def _prepare_monthly_chart_data(pa: pd.DataFrame, col_date: str) -> pd.DataFrame:
    """Helper function to prepare monthly aggregated data for charts."""
    if not col_date or col_date not in pa.columns:
        return pd.DataFrame()
    
    pa_copy = pa.copy()
    pa_copy["__month_period"] = pd.to_datetime(pa_copy[col_date], errors="coerce").dt.to_period("M")
    months = sorted(pa_copy["__month_period"].dropna().unique())
    
    monthly_data = []
    for period in months:
        m_mask = pa_copy["__month_period"] == period
        m_sub = pa_copy[m_mask]
        
        # Count by channel
        if "Matching Channel" in m_sub.columns:
            matching_channel_series = m_sub["Matching Channel"]
            if isinstance(matching_channel_series, pd.Series):
                sms_mask = matching_channel_series.astype(str).str.contains("SMS", case=False, na=False)
                email_mask = matching_channel_series.astype(str).str.contains("Email", case=False, na=False)
                calls_mask = matching_channel_series.astype(str).str.contains("Confirmed Call|Expected Call", case=False, na=False)
            else:
                # Fallback if not a Series
                sms_mask = pd.Series([False] * len(m_sub))
                email_mask = pd.Series([False] * len(m_sub))
                calls_mask = pd.Series([False] * len(m_sub))
        else:
            sms_mask = pd.Series([False] * len(m_sub))
            email_mask = pd.Series([False] * len(m_sub))
            calls_mask = pd.Series([False] * len(m_sub))
        
        sms_count = len(m_sub[sms_mask])
        email_count = len(m_sub[email_mask])
        calls_count = len(m_sub[calls_mask])
        
        # Calculate reach rates per channel
        total_cases = len(m_sub)
        sms_reached = int((m_sub[sms_mask]["Reach Status"] == "Reached").sum())
        email_reached = int((m_sub[email_mask]["Reach Status"] == "Reached").sum())
        calls_reached = int((m_sub[calls_mask]["Reach Status"] == "Reached").sum())
        
        sms_rate = round(sms_reached / sms_count * 100, 1) if sms_count > 0 else 0
        email_rate = round(email_reached / email_count * 100, 1) if email_count > 0 else 0
        calls_rate = round(calls_reached / calls_count * 100, 1) if calls_count > 0 else 0
        
        monthly_data.append({
            "Month": period.strftime("%B %Y"),
            "ART Cases": total_cases,
            "Emails": email_count,
            "Email Rate": email_rate,
            "SMS": sms_count,
            "SMS Rate": sms_rate,
            "Calls": calls_count,
            "Calls Rate": calls_rate,
        })
    
    return pd.DataFrame(monthly_data)

# Made with Bob
