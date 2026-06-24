# Reach Rate Calculator - Chart Specifications

**Document Version:** 1.0  
**Date:** June 2, 2026  
**Purpose:** Map ART Presentation charts to Excel output specifications

---

## Table of Contents

1. [Overview](#overview)
2. [Chart Inventory](#chart-inventory)
3. [Color Palette](#color-palette)
4. [Chart Specifications by Page](#chart-specifications-by-page)
5. [Excel Implementation Guide](#excel-implementation-guide)
6. [xlsxwriter Code Examples](#xlsxwriter-code-examples)

---

## Overview

This document provides exact specifications for replicating the charts from the **ART Presentation (Jan - April) 2026.pdf** in the Reach Rate Calculator Excel output. The presentation contains 19 pages with various chart types that visualize Project ART performance metrics.

### Presentation Structure
- **Pages 1-2:** Title and objectives (no charts)
- **Pages 3-16:** Data visualization charts
- **Pages 17-19:** Process documentation and closing

---

## Chart Inventory

| Page | Chart Type | Title | Data Source |
|------|-----------|-------|-------------|
| 3 | Combo (Bar + Line) | Overall Monthly Project ART Case Volume & Reach Attempt Performance | Monthly aggregated data |
| 4 | Stacked Bar | 35% of April ART Cases are Resolved | Monthly resolution status breakdown |
| 5 | Grouped Bar | Escalated Cases Breakdown | Monthly escalation by team (DRO vs LenCare) |
| 6 | 4x Grouped Bar | Project ART T3B vs. Non-Project ART T3B by SDT | Monthly comparison by service delivery type |
| 7 | Combo (Bar + Line) | How are Depot Customers Responding to Project ART Follow-ups? | Depot-specific reach attempts and outcomes |
| 8 | Combo (Bar + Line) | How are ONS Customers Responding to Project ART Follow-ups? | ONS-specific reach attempts and outcomes |
| 9 | Combo (Bar + Line) | How are CRU Customers Responding to Project ART Follow-ups? | CRU-specific reach attempts and outcomes |
| 10 | Horizontal Bar | Depot Machine Types 21BV & 21HH are Driving Issue Not Fixed | Machine type analysis with root cause tables |
| 11 | Horizontal Bar | Why Were Second Work Orders Required for Depot? | Second WO analysis with symptom breakdown |
| 12 | Horizontal Bar | ONS Machine Types 21AJ & 21HE are Driving Issue Not Fixed | Machine type analysis with root cause tables |
| 13 | Horizontal Bar | Why Were Second Work Orders Required for ONS? | Second WO analysis with symptom breakdown |
| 14 | Pie Chart | 11 Different CRU Machine Types Driving Issue Not Fixed | Machine type distribution with root cause tables |
| 15 | Horizontal Bar | Why Were Second Work Orders Required for CRU? | Second WO analysis |
| 16 | Simple Bar | Open Care Call Cases | Monthly comparison (Mar vs Apr) |

---

## Color Palette

### IBM Carbon Design System Colors

```python
# Primary Colors
IBM_BLUE_60 = "#0f62fe"      # Primary brand color
IBM_BLUE_70 = "#0043ce"      # Darker blue for emphasis
IBM_BLUE_10 = "#d0e2ff"      # Light blue backgrounds

# Status Colors
IBM_GREEN_60 = "#198038"     # Success/Reached/Positive
IBM_GREEN_10 = "#defbe6"     # Light green backgrounds
IBM_RED_60 = "#da1e28"       # Error/Not Reached/Negative
IBM_RED_10 = "#fff1f1"       # Light red backgrounds
IBM_ORANGE_60 = "#eb6200"    # Warning/SMS channel
IBM_PURPLE_60 = "#8a3ffc"    # Alternative/Escalation

# Neutral Colors
IBM_GRAY_10 = "#f4f4f4"      # Alternating row backgrounds
IBM_GRAY_50 = "#8d8d8d"      # Secondary text
IBM_GRAY_100 = "#161616"     # Primary text

# Chart-Specific Colors
DARK_GRAY = "#393939"        # Bar charts (ART Cases)
YELLOW_HIGHLIGHT = "#f1c21b" # Data labels on bars
```

### Channel-Specific Colors

```python
CHANNEL_COLORS = {
    "Emails": "#0f62fe",      # IBM Blue 60
    "SMS": "#da1e28",         # IBM Red 60 (warm contrast)
    "Calls": "#198038",       # IBM Green 60
    "Confirmed Call": "#005d5d",  # Teal
    "Expected Call": "#b45309",   # Orange-brown
}
```

---

## Chart Specifications by Page

### Page 3: Overall Monthly Case Volume & Reach Attempt Performance

**Chart Type:** Combination (Column + Multi-Line)

**Layout:**
- Primary Y-axis (left): Case volume (0-8000)
- Secondary Y-axis (right): Percentage (0%-50%)
- X-axis: Months (January 2026 - April 2026)

**Data Series:**
1. **ART Cases** (Column, Dark Gray #393939)
   - Values displayed on bars in yellow boxes
   - Data: [5378, 7003, 6534, 6252]

2. **Emails** (Line, Blue circle markers)
   - Reach rate percentages
   - Data: [41%, 45%, 47%, 44%]

3. **SMS** (Line, Orange circle markers)
   - Reach rate percentages
   - Data: [32%, 30%, 30%, 29%]

4. **Calls** (Line, Green circle markers)
   - Reach rate percentages
   - Data: [27%, 25%, 23%, 26%]

**Table Below Chart:**
| Month | Emails | % | SMS | % | Calls | % | ART Cases | Reach Rate |
|-------|--------|---|-----|---|-------|---|-----------|------------|
| January 2026 | 1204 | 41% | 951 | 32% | 800 | 27% | 5378 | 55% |
| February 2026 | 1696 | 45% | 1118 | 30% | 918 | 25% | 7003 | 53% |
| March 2026 | 1499 | 47% | 955 | 30% | 731 | 23% | 6534 | 49% |
| April 2026 | 1330 | 44% | 884 | 29% | 785 | 26% | 6252 | 48% |

**Excel Mapping:**
- Sheet: "Overall Summary" or new "Monthly Overview"
- Data source: `metrics["monthly_total_numbers"]` + reach rate calculations

**xlsxwriter Configuration:**
```python
chart = workbook.add_chart({'type': 'column'})
chart.add_series({
    'name': 'ART Cases',
    'categories': '=Sheet!$A$2:$A$5',
    'values': '=Sheet!$B$2:$B$5',
    'fill': {'color': '#393939'},
    'data_labels': {'value': True, 'position': 'inside_end',
                    'font': {'color': '#f1c21b', 'bold': True}}
})

# Add line series on secondary axis
chart.add_series({
    'name': 'Emails',
    'categories': '=Sheet!$A$2:$A$5',
    'values': '=Sheet!$C$2:$C$5',
    'y2_axis': True,
    'line': {'color': '#0f62fe', 'width': 2.5},
    'marker': {'type': 'circle', 'size': 8, 'fill': {'color': '#0f62fe'}}
})
```

---

### Page 4: Resolution Status Breakdown

**Chart Type:** Stacked Bar (Horizontal)

**Layout:**
- X-axis: Percentage (0%-50%)
- Y-axis: Months (January - April)
- 5 status categories stacked

**Data Series (Colors):**
1. **Issue Resolved** (IBM Blue #0f62fe) - Primary positive outcome
2. **DND** (Orange #eb6200) - Did Not Disturb
3. **Issue Not Fixed** (Green #198038) - Requires follow-up
4. **Not yet Tested** (Light Blue #8ab8ff) - Pending verification
5. **Escalated** (Purple #8a3ffc) - Escalated cases

**Data Table:**
| Month | No Reply | Issue Resolved | DND | Issue Not Fixed | Not yet Tested | Escalated | Total |
|-------|----------|----------------|-----|-----------------|----------------|-----------|-------|
| January | 2430 (45%) | 2180 (41%) | 336 (6%) | 266 (5%) | 152 (3%) | 14 (0.3%) | 5378 |
| February | 3252 (46%) | 2693 (38%) | 450 (6%) | 412 (6%) | 146 (2%) | 50 (0.7%) | 7003 |
| March | 3177 (49%) | 2477 (38%) | 496 (8%) | 238 (4%) | 121 (2%) | 25 (0.4%) | 6534 |
| April | 2917 (47%) | 2170 (35%) | 628 (10%) | 348 (6%) | 153 (2%) | 36 (0.6%) | 6252 |

**Excel Mapping:**
- Sheet: New "Resolution Status" or add to "Overall Summary"
- Data source: Derived from `pa["Final Action"]` grouped by month

---

### Page 5: Escalated Cases Breakdown

**Chart Type:** Grouped Bar (Vertical)

**Layout:**
- Y-axis: Percentage (0%-100%)
- X-axis: Months (January - April)
- 2 groups per month

**Data Series:**
1. **DRO Team** (Green #198038) - 75-82% of escalations
2. **LenCare Team** (Red #da1e28) - 18-25% of escalations

**Data Table:**
| Escalations/Month | January | | February | | March | | April | | Grand Total | |
|-------------------|---------|---|----------|---|-------|---|-------|---|-------------|---|
| DRO Team | 310 | 75% | 337 | 82% | 351 | 77% | 347 | 78% | 1345 | 78% |
| LenCare Team | 102 | 25% | 76 | 18% | 106 | 23% | 96 | 22% | 380 | 22% |
| Grand Total | 412 | 100% | 413 | 100% | 457 | 100% | 443 | 100% | 1725 | 100% |

**Excel Mapping:**
- Sheet: New "Escalations"
- Data source: Filter `pa[pa["Final Action"].str.lower() == "escalation"]`

---

### Page 6: T3B Comparison by Service Delivery Type

**Chart Type:** 4x Grouped Bar (Vertical) - Small Multiples

**Layout:** 2x2 grid of charts
- Overall
- DEPOT
- ONSITE
- CRU

Each chart shows:
- Y-axis: Percentage (0%-100%)
- X-axis: Months (January - April)
- 2 bars per month: NPA T3B (Blue) vs PA T3B (Orange)

**Color Scheme:**
- **NPA T3B** (Non-Project ART): IBM Blue #0f62fe
- **PA T3B** (Project ART): Orange #eb6200

**Key Insights:**
- Project ART consistently achieves 88-95% T3B rates
- Highest performance in DEPOT (86-100%) and April overall (95%)

**Excel Mapping:**
- Sheet: New "T3B Comparison"
- Data source: Requires T3B metric calculation from completion data

---

### Page 7-9: Channel-Specific Response Analysis

**Chart Type:** Combination (Column + Multi-Line + Stacked Bar)

**Common Structure for Depot/ONS/CRU:**

**Top Chart:**
- Primary Y-axis: Case volume (0-8000)
- Secondary Y-axis: Reach attempts (0-1400 for Depot, 0-1400 for ONS, 0-120 for CRU)
- Column: ART Cases (Dark Gray)
- Lines: Emails, SMS, Calls (Blue, Orange, Green)

**Bottom Chart:**
- Stacked horizontal bars showing response outcomes
- Categories: No Reply, Issue Resolved, DND, Issue Not Fixed, Not yet Tested, Escalated

**Excel Mapping:**
- Sheets: "Depot Analysis", "ONS Analysis", "CRU Analysis"
- Data source: Filter by service delivery type from main dataset

---

### Page 10, 12, 14: Machine Type Analysis

**Chart Type:** Horizontal Bar

**Layout:**
- Y-axis: Machine types (top 2-3 highlighted)
- X-axis: Percentage of "Issue Not Fixed" cases
- Accompanying root cause tables

**Color Scheme:**
- Highlighted machine types: Yellow #f1c21b
- Other types: Green #198038

**Root Cause Tables Include:**
- Parts Sent
- RR Reason (Repeat Repair Reason)
- New Issue
- Second Parts Sent

**Excel Mapping:**
- Sheets: "Depot Machine Analysis", "ONS Machine Analysis", "CRU Machine Analysis"
- Data source: Join machine type with Final Action = "Issue Not Fixed"

---

### Page 11, 13, 15: Second Work Order Analysis

**Chart Type:** Horizontal Bar

**Layout:**
- Y-axis: Categories (Resolved on WO2, Required WO2, Not Resolved on WO1)
- X-axis: Number of cases
- Accompanying symptom breakdown

**Color Scheme:**
- Depot: Yellow #f1c21b
- ONS: Green #198038
- CRU: Purple #8a3ffc

**Excel Mapping:**
- Sheets: Add to respective analysis sheets
- Data source: Requires work order sequence tracking

---

### Page 16: Open Care Call Cases

**Chart Type:** Simple Bar (Vertical)

**Layout:**
- Y-axis: Case count (0-80)
- X-axis: Months (Mar, Apr)
- Single series: Standard Commercial

**Data:**
- March: 68 cases
- April: 61 cases

**Color:** IBM Blue #0f62fe

**Excel Mapping:**
- Sheet: "Open Cases" or add to summary
- Data source: Filter for open/pending cases by month

---

## Excel Implementation Guide

### Recommended Sheet Structure

1. **Total Cases** (existing) - Raw data table
2. **Overall Summary** (existing) - High-level metrics
3. **Monthly Overview** (NEW) - Page 3 chart + table
4. **Resolution Status** (NEW) - Page 4 stacked bar data
5. **Escalations** (NEW) - Page 5 team comparison
6. **T3B Comparison** (NEW) - Page 6 four-chart grid
7. **Depot Analysis** (NEW) - Pages 7, 10, 11 combined
8. **ONS Analysis** (NEW) - Pages 8, 12, 13 combined
9. **CRU Analysis** (NEW) - Pages 9, 14, 15 combined
10. **Open Cases** (NEW) - Page 16 simple bar

### Chart Positioning Guidelines

```python
# Standard chart dimensions
CHART_WIDTH = 720   # pixels (10 inches at 72 DPI)
CHART_HEIGHT = 432  # pixels (6 inches at 72 DPI)

# Positioning
chart.set_size({'width': CHART_WIDTH, 'height': CHART_HEIGHT})
chart.set_x_offset(10)
chart.set_y_offset(10)

# For small multiples (2x2 grid)
SMALL_WIDTH = 350
SMALL_HEIGHT = 260
```

---

## xlsxwriter Code Examples

### Example 1: Combo Chart (Bar + Line)

```python
def create_monthly_overview_chart(workbook, worksheet, data_range):
    """
    Creates the Page 3 chart: Monthly Case Volume & Reach Attempts
    """
    # Create combination chart
    chart = workbook.add_chart({'type': 'column'})
    
    # Add ART Cases column series
    chart.add_series({
        'name': 'ART Cases',
        'categories': f'={worksheet.name}!$A$2:$A$5',
        'values': f'={worksheet.name}!$B$2:$B$5',
        'fill': {'color': '#393939'},
        'border': {'none': True},
        'data_labels': {
            'value': True,
            'position': 'inside_end',
            'font': {
                'name': 'IBM Plex Sans',
                'size': 11,
                'bold': True,
                'color': '#f1c21b'
            },
            'num_format': '#,##0'
        }
    })
    
    # Add Emails line series (secondary axis)
    chart.add_series({
        'name': 'Emails',
        'categories': f'={worksheet.name}!$A$2:$A$5',
        'values': f'={worksheet.name}!$C$2:$C$5',
        'y2_axis': True,
        'line': {
            'color': '#0f62fe',
            'width': 2.5
        },
        'marker': {
            'type': 'circle',
            'size': 8,
            'border': {'color': '#0f62fe', 'width': 2},
            'fill': {'color': '#0f62fe'}
        }
    })
    
    # Add SMS line series (secondary axis)
    chart.add_series({
        'name': 'SMS',
        'categories': f'={worksheet.name}!$A$2:$A$5',
        'values': f'={worksheet.name}!$D$2:$D$5',
        'y2_axis': True,
        'line': {
            'color': '#eb6200',
            'width': 2.5
        },
        'marker': {
            'type': 'circle',
            'size': 8,
            'border': {'color': '#eb6200', 'width': 2},
            'fill': {'color': '#eb6200'}
        }
    })
    
    # Add Calls line series (secondary axis)
    chart.add_series({
        'name': 'Calls',
        'categories': f'={worksheet.name}!$A$2:$A$5',
        'values': f'={worksheet.name}!$E$2:$E$5',
        'y2_axis': True,
        'line': {
            'color': '#198038',
            'width': 2.5
        },
        'marker': {
            'type': 'circle',
            'size': 8,
            'border': {'color': '#198038', 'width': 2},
            'fill': {'color': '#198038'}
        }
    })
    
    # Configure chart
    chart.set_title({
        'name': 'Overall Monthly Project ART Case Volume & Reach Attempt Performance',
        'name_font': {
            'name': 'IBM Plex Sans',
            'size': 14,
            'bold': True,
            'color': '#161616'
        }
    })
    
    chart.set_x_axis({
        'name': 'Month',
        'name_font': {'name': 'IBM Plex Sans', 'size': 11},
        'num_font': {'name': 'IBM Plex Sans', 'size': 10}
    })
    
    chart.set_y_axis({
        'name': 'ART Cases',
        'name_font': {'name': 'IBM Plex Sans', 'size': 11},
        'num_font': {'name': 'IBM Plex Sans', 'size': 10},
        'min': 0,
        'max': 8000,
        'major_gridlines': {'visible': True, 'line': {'color': '#e0e0e0'}}
    })
    
    chart.set_y2_axis({
        'name': 'Reach Rate %',
        'name_font': {'name': 'IBM Plex Sans', 'size': 11},
        'num_font': {'name': 'IBM Plex Sans', 'size': 10},
        'min': 0,
        'max': 50,
        'num_format': '0"%"'
    })
    
    chart.set_legend({
        'position': 'bottom',
        'font': {'name': 'IBM Plex Sans', 'size': 10}
    })
    
    chart.set_size({'width': 720, 'height': 432})
    chart.set_plotarea({
        'border': {'none': True},
        'fill': {'color': '#ffffff'}
    })
    
    return chart
```

### Example 2: Stacked Bar Chart

```python
def create_resolution_status_chart(workbook, worksheet):
    """
    Creates the Page 4 chart: Resolution Status Breakdown
    """
    chart = workbook.add_chart({'type': 'bar', 'subtype': 'percent_stacked'})
    
    # Define series with colors
    series_config = [
        ('Issue Resolved', '#0f62fe'),
        ('DND', '#eb6200'),
        ('Issue Not Fixed', '#198038'),
        ('Not yet Tested', '#8ab8ff'),
        ('Escalated', '#8a3ffc')
    ]
    
    for idx, (name, color) in enumerate(series_config):
        col_letter = chr(66 + idx)  # B, C, D, E, F
        chart.add_series({
            'name': name,
            'categories': f'={worksheet.name}!$A$2:$A$5',
            'values': f'={worksheet.name}!${col_letter}$2:${col_letter}$5',
            'fill': {'color': color},
            'border': {'none': True},
            'data_labels': {
                'value': True,
                'position': 'inside_end',
                'font': {'name': 'IBM Plex Sans', 'size': 9, 'bold': True},
                'num_format': '0.0"%"'
            }
        })
    
    chart.set_title({
        'name': '35% of April ART Cases are Resolved',
        'name_font': {'name': 'IBM Plex Sans', 'size': 14, 'bold': True}
    })
    
    chart.set_x_axis({
        'name': 'Percentage',
        'min': 0,
        'max': 100,
        'num_format': '0"%"'
    })
    
    chart.set_y_axis({
        'reverse': True  # Months from top to bottom
    })
    
    chart.set_legend({'position': 'bottom'})
    chart.set_size({'width': 720, 'height': 432})
    
    return chart
```

### Example 3: Grouped Bar Chart

```python
def create_escalation_chart(workbook, worksheet):
    """
    Creates the Page 5 chart: Escalated Cases by Team
    """
    chart = workbook.add_chart({'type': 'column'})
    
    # DRO Team series
    chart.add_series({
        'name': 'DRO Team',
        'categories': f'={worksheet.name}!$A$2:$A$5',
        'values': f'={worksheet.name}!$B$2:$B$5',
        'fill': {'color': '#198038'},
        'data_labels': {
            'value': True,
            'position': 'outside_end',
            'font': {'name': 'IBM Plex Sans', 'size': 10, 'bold': True},
            'num_format': '0"%"'
        }
    })
    
    # LenCare Team series
    chart.add_series({
        'name': 'LenCare Team',
        'categories': f'={worksheet.name}!$A$2:$A$5',
        'values': f'={worksheet.name}!$C$2:$C$5',
        'fill': {'color': '#da1e28'},
        'data_labels': {
            'value': True,
            'position': 'outside_end',
            'font': {'name': 'IBM Plex Sans', 'size': 10, 'bold': True},
            'num_format': '0"%"'
        }
    })
    
    chart.set_title({
        'name': 'Escalated Cases Breakdown',
        'name_font': {'name': 'IBM Plex Sans', 'size': 14, 'bold': True}
    })
    
    chart.set_y_axis({
        'name': 'Percentage',
        'min': 0,
        'max': 100,
        'num_format': '0"%"'
    })
    
    chart.set_legend({'position': 'bottom'})
    chart.set_size({'width': 720, 'height': 432})
    
    return chart
```

### Example 4: Pie Chart

```python
def create_machine_type_pie_chart(workbook, worksheet):
    """
    Creates the Page 14 chart: CRU Machine Types Distribution
    """
    chart = workbook.add_chart({'type': 'pie'})
    
    chart.add_series({
        'name': 'Machine Types',
        'categories': f'={worksheet.name}!$A$2:$A$12',  # 11 machine types
        'values': f'={worksheet.name}!$B$2:$B$12',
        'data_labels': {
            'percentage': True,
            'leader_lines': True,
            'font': {'name': 'IBM Plex Sans', 'size': 10}
        },
        'points': [
            {'fill': {'color': '#0f62fe'}},
            {'fill': {'color': '#eb6200'}},
            {'fill': {'color': '#198038'}},
            {'fill': {'color': '#8a3ffc'}},
            {'fill': {'color': '#f1c21b'}},
            {'fill': {'color': '#005d5d'}},
            {'fill': {'color': '#6929c4'}},
            {'fill': {'color': '#b45309'}},
            {'fill': {'color': '#8ab8ff'}},
            {'fill': {'color': '#da1e28'}},
            {'fill': {'color': '#525252'}}
        ]
    })
    
    chart.set_title({
        'name': '11 Different CRU Machine Types Driving Issue Not Fixed',
        'name_font': {'name': 'IBM Plex Sans', 'size': 14, 'bold': True}
    })
    
    chart.set_legend({'position': 'right'})
    chart.set_size({'width': 600, 'height': 450})
    
    return chart
```

---

## Implementation Checklist

### Phase 1: Data Preparation
- [ ] Add month extraction to PA Cases processing
- [ ] Calculate resolution status percentages by month
- [ ] Identify escalation cases and team assignment
- [ ] Extract T3B metrics from completion data
- [ ] Group machine types with "Issue Not Fixed" status
- [ ] Track work order sequences for second WO analysis

### Phase 2: Sheet Creation
- [ ] Create "Monthly Overview" sheet with Page 3 data
- [ ] Create "Resolution Status" sheet with Page 4 data
- [ ] Create "Escalations" sheet with Page 5 data
- [ ] Create "T3B Comparison" sheet with Page 6 data
- [ ] Create "Depot Analysis" sheet (Pages 7, 10, 11)
- [ ] Create "ONS Analysis" sheet (Pages 8, 12, 13)
- [ ] Create "CRU Analysis" sheet (Pages 9, 14, 15)
- [ ] Create "Open Cases" sheet with Page 16 data

### Phase 3: Chart Implementation
- [ ] Implement combo chart (bar + line) for monthly overview
- [ ] Implement stacked bar chart for resolution status
- [ ] Implement grouped bar chart for escalations
- [ ] Implement 2x2 small multiples for T3B comparison
- [ ] Implement channel-specific combo charts (Depot/ONS/CRU)
- [ ] Implement horizontal bar charts for machine types
- [ ] Implement pie chart for CRU machine distribution
- [ ] Implement simple bar chart for open cases

### Phase 4: Styling & Polish
- [ ] Apply IBM Plex Sans font throughout
- [ ] Use IBM Carbon color palette consistently
- [ ] Add data labels with proper formatting
- [ ] Configure chart legends and axes
- [ ] Set appropriate chart dimensions
- [ ] Add gridlines and borders where needed
- [ ] Test chart rendering in Excel

---

## Notes

1. **Font Consistency:** All charts must use IBM Plex Sans font family
2. **Color Accessibility:** Ensure sufficient contrast for colorblind users
3. **Data Labels:** Display values on bars/points where space permits
4. **Legend Position:** Bottom for horizontal charts, right for vertical
5. **Chart Spacing:** Leave 2-3 rows between charts on same sheet
6. **Table Integration:** Place data tables directly below corresponding charts

---

**Document End**