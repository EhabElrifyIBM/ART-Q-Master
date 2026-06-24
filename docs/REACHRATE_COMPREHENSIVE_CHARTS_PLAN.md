# Reach Rate Calculator - Comprehensive Charts Implementation Plan

## Objective
Add appropriate charts to ALL sheets that currently have only tables, and add tables to sheets that currently have only charts.

## Sheet-by-Sheet Analysis & Chart Recommendations

### 1. **Total Cases** ❌ No Chart
- **Content:** Raw case-by-case data
- **Recommendation:** No chart (too granular, thousands of rows)
- **Action:** Keep as-is

### 2. **Overall Summary** ✅ Has Charts
- **Current:** Tables + Monthly Overview + Resolution Status + Final Action Pie
- **Action:** Keep existing charts

### 3. **DEPOT SDT Analysis** ⚠️ Chart Only
- **Current:** Only PNG chart
- **Missing:** Data table showing monthly breakdown
- **Action:** Add table BEFORE chart showing Month, ART Cases, Emails, SMS, Calls with rates

### 4. **ONSITE SDT Analysis** ⚠️ Chart Only
- **Current:** Only PNG chart
- **Missing:** Data table
- **Action:** Add table BEFORE chart

### 5. **CRU SDT Analysis** ⚠️ Chart Only
- **Current:** Only PNG chart
- **Missing:** Data table
- **Action:** Add table BEFORE chart

### 6. **SMS Channel** ⚠️ Table Only
- **Current:** Final Action breakdown table + Reach Rate table
- **Missing:** Pie chart for Final Actions
- **Recommended Chart:** Pie chart showing Final Action distribution for SMS cases
- **Action:** Generate `sms_final_action_pie` chart

### 7. **Email Channel** ⚠️ Table Only
- **Current:** Final Action breakdown table + Reach Rate table
- **Missing:** Pie chart
- **Recommended Chart:** Pie chart showing Final Action distribution for Email cases
- **Action:** Generate `email_final_action_pie` chart

### 8. **Confirmed Call Channel** ⚠️ Table Only
- **Current:** Final Action breakdown table + Reach Rate table
- **Missing:** Pie chart
- **Recommended Chart:** Pie chart showing Final Action distribution
- **Action:** Generate `confirmed_call_final_action_pie` chart

### 9. **Expected Call Channel** ⚠️ Table Only
- **Current:** Final Action breakdown table + Reach Rate table
- **Missing:** Pie chart
- **Recommended Chart:** Pie chart showing Final Action distribution
- **Action:** Generate `expected_call_final_action_pie` chart

### 10. **Monthly Total Numbers** ⚠️ Table Only
- **Current:** Table with SMS, Emails, Calls counts by month
- **Missing:** Stacked bar chart
- **Recommended Chart:** Stacked column chart showing channel volumes by month
- **Action:** Generate `monthly_total_numbers_chart` - stacked column

### 11. **Monthly Reached vs Not** ⚠️ Table Only
- **Current:** Table with reached/not reached counts by channel and month
- **Missing:** Grouped bar chart
- **Recommended Chart:** Grouped bar chart comparing reached vs not reached
- **Action:** Generate `monthly_reached_vs_not_chart` - grouped bars

### 12. **Monthly Channel Reach** ⚠️ Table Only
- **Current:** Table with reached cases only by channel
- **Missing:** Column chart
- **Recommended Chart:** Grouped column chart showing reached cases by channel
- **Action:** Generate `monthly_channel_reach_chart` - grouped columns

### 13. **Monthly WOT Channel Reach** ⚠️ Table Only
- **Current:** Complex pivot table with WOT types and channels
- **Missing:** Heatmap or grouped bar
- **Recommended Chart:** Grouped bar chart by WOT type
- **Action:** Generate `monthly_wot_chart` - grouped bars

### 14. **Monthly Breakdown** ⚠️ Table Only
- **Current:** Pivot table with Count and Reach% for each channel
- **Missing:** Combo chart
- **Recommended Chart:** Combo chart (bars for counts, lines for reach%)
- **Action:** Generate `monthly_breakdown_chart` - combo

### 15. **By Work Order Type** ⚠️ Table Only
- **Current:** Table with reach rates by WOT and channel
- **Missing:** Horizontal bar chart
- **Recommended Chart:** Horizontal bar chart showing reach rates by WOT
- **Action:** Generate `wot_reach_rate_chart` - horizontal bars

## Implementation Steps

### Step 1: Add Chart Generation Functions to chart_generator.py
Add these new chart types:
1. `create_channel_pie_chart()` - For individual channel Final Action pies
2. `create_monthly_stacked_column()` - For Monthly Total Numbers
3. `create_monthly_grouped_bars()` - For Monthly Reached vs Not
4. `create_wot_horizontal_bars()` - For Work Order Type reach rates

### Step 2: Update generate_all_charts() Function
Add generation of all new chart types

### Step 3: Update ReachRateCalculator.py _write_excel()
For each sheet:
- SDT sheets: Add data tables BEFORE charts
- Channel sheets: Add pie charts AFTER tables
- Monthly sheets: Add appropriate charts AFTER tables
- WOT sheet: Add horizontal bar chart AFTER table

## Chart Type Selection Rationale

| Data Type | Best Chart | Reason |
|-----------|-----------|---------|
| Categorical distribution | Pie Chart | Shows proportions clearly |
| Time series volumes | Stacked Column | Shows composition over time |
| Comparisons | Grouped Bars | Easy to compare values |
| Rates over time | Line Chart | Shows trends |
| Multiple metrics | Combo Chart | Shows different scales |
| Rankings | Horizontal Bar | Easy to read labels |

## Expected Output

After implementation, EVERY sheet (except Total Cases) will have:
✅ Data table(s)
✅ Relevant visualization chart(s)
✅ Proper spacing and layout