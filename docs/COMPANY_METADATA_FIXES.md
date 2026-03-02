# Company Metadata Display Fixes - Summary

## Issues Fixed

### 1. Company Name - "Unknown Company" Instead of Actual Name
**Problem:** Company name was showing as "Unknown Company" because it wasn't being extracted from the Excel cache file.

**Solution:** Updated `load_companies_for_handler()` in SharedFunctions.py to:
- Search for "Company Name" column in the cache file
- Extract and include company_name in each case record
- Handle missing/NaN values gracefully

**Result:** Dialog now displays actual company names from the cache file.

---

### 2. Missing State/Province Data
**Problem:** State/Province was showing as empty, preventing local time calculation.

**Solution:** Updated `load_companies_for_handler()` to:
- Search for "State/Province" column in the cache file
- Extract state_province for each case
- Include it in the case data passed to the dialog

**Result:** State/Province now displays correctly and local time is calculated.

---

### 3. Missing Phone Information
**Problem:** Phone number wasn't being extracted from the cache file.

**Solution:** Updated `load_companies_for_handler()` to:
- Search for "Phone" column in the cache file
- Extract phone for each case
- Pass it to the metadata dialog

**Result:** Phone number now displays when available.

---

### 4. Font Not Being Applied to Dialogs
**Problem:** Dialog wasn't using theme font settings, resulting in inconsistent UI styling.

**Solution:**
1. Updated CompaniesProcess_v2.py to extract and pass font_settings:
   ```python
   font_settings = theme_manager.get_font_settings()
   company_metadata['font_settings'] = font_settings
   ```

2. Updated CompanyMetadataDialog to:
   - Accept font_settings in company_data dict
   - Create a `get_font()` helper function that uses theme settings if available
   - Apply consistent fonts throughout the dialog

**Result:** Dialog now respects theme font settings for consistent UI appearance.

---

## Files Modified

### 1. [SharedFunctions.py](SharedFunctions.py#L1548-L1602)
- Enhanced `load_companies_for_handler()` function
- Added extraction of: Company Name, State/Province, Phone
- Added safe handling for NaN and missing values

**Changes:**
```python
# New column searches
company_name_col = find_column_case_insensitive(df, 'Company Name')
state_province_col = find_column_case_insensitive(df, 'State/Province')
phone_col = find_column_case_insensitive(df, 'Phone')

# Added to case data
'company_name': company_name if company_name != 'nan' else 'Unknown Company',
'state_province': state_province if state_province != 'nan' else '',
'phone': phone if phone != 'nan' else '',
```

### 2. [CompaniesProcess_v2.py](CompaniesProcess_v2.py#L377-L408)
- Updated metadata extraction to use cached company data
- Added font_settings extraction from theme manager
- Passed font_settings to metadata dialog

**Changes:**
```python
# Get font settings from theme manager
font_settings = theme_manager.get_font_settings()

# Include in metadata dict
company_metadata = {
    'company_name': first_case_row.get('company_name', 'Unknown Company'),
    'font_settings': font_settings,
    ...
}
```

### 3. [company_metadata_display.py](company_metadata_display.py)
- Updated dialog to accept and use font_settings
- Created `get_font()` helper function
- Applied consistent fonts throughout UI

**Changes:**
```python
# Accept font_settings in __init__
self.font_settings = company_data.get('font_settings', None)

# Helper function to apply fonts
def get_font(size=12, bold=False):
    if self.font_settings:
        font = QFont(self.font_settings.get('font_family', 'Segoe UI'))
    else:
        font = QFont()
    font.setPointSize(size)
    if bold:
        font.setBold(True)
    return font

# Applied to all UI elements
title.setFont(get_font(17, bold=True))
email_label.setFont(get_font(13, bold=True))
```

---

## Dialog Display Improvements

### Before
- Company name: "Unknown Company"
- State/Province: Empty
- Phone: Missing
- Fonts: Default system fonts
- Local time: Not calculated

### After
- Company name: Actual company from cache (e.g., "ACOA-APECA")
- State/Province: Correctly displayed (e.g., "Ontario")
- Phone: Shown when available
- Fonts: Applied from theme manager
- Local time: Calculated and displayed for the company location

---

## Data Flow

```
Excel Cache File
    ↓
load_companies_for_handler()
    ├─ Extract Company Name column
    ├─ Extract State/Province column
    ├─ Extract Phone column
    └─ Add to case records
    ↓
CompaniesProcess_v2.run_companies_process()
    ├─ Get theme font_settings
    └─ Build company_metadata with all data
    ↓
CompanyMetadataDialog
    ├─ Display company name (from cache)
    ├─ Display email (grouped key)
    ├─ Display phone (from cache)
    ├─ Display state/province (from cache)
    ├─ Calculate & display local time (from state)
    └─ Apply theme fonts throughout
```

---

## Testing Checklist

- [ ] Company name displays correctly (not "Unknown Company")
- [ ] State/Province shows the correct location
- [ ] Phone number displays when available
- [ ] Dialog fonts match theme settings
- [ ] Local time is calculated and displayed
- [ ] Dialog appears before case processing starts
- [ ] "Understood - Continue" button works and closes dialog
