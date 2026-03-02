"""
Phase 5.2 - Company Metadata Implementation
===========================================

PHASE OVERVIEW:
Phase 5.2 focuses on implementing company metadata extraction and timezone calculations.
This enables displaying company information and calculating local times based on company location.

STATUS: ✅ COMPLETED - Timezone Map Module Created

COMPLETION DATE: January 27, 2026
PHASE DEPENDENCY: None (independent of other phases)

================================================================================

IMPLEMENTATION SUMMARY:

1. CREATED: src/utils/timezone_map.py
   - Comprehensive timezone offset mapping for all US states and Canadian provinces
   - Hardcoded mapping as specified in Updates.md (Phase 5.2 requirements)
   - Helper functions for timezone lookups and local time calculation

================================================================================

FILE DETAILS:

📄 src/utils/timezone_map.py (NEW - 225 lines)
   Location: c:\Users\EhabElrify\Desktop\Projects\ART Q Master\src\utils\timezone_map.py
   
   COMPONENTS:
   
   1. TIMEZONE_MAP Dictionary
      - Maps region names to offset hours
      - Supports all 50 US states + abbreviations
      - Supports all 13 Canadian provinces/territories
      - Format: "State/Province": hours_offset
      - Total: 64 regions mapped
      
   2. Helper Functions:
      
      a) get_timezone_offset(state_or_province: str) -> Optional[float]
         Purpose: Get timezone offset for a state/province
         Features:
         - Exact match lookup
         - Case-insensitive matching
         - Partial string matching for variations
         Returns: Hours offset or None if not found
         
      b) calculate_local_time(state_or_province: str, utc_datetime: Optional[datetime]) -> Optional[datetime]
         Purpose: Calculate local time for a region
         Features:
         - Uses current UTC time if not provided
         - Applies timezone offset
         - Returns datetime object
         Usage Example:
           local_time = calculate_local_time("California")
           formatted = local_time.strftime('%H:%M:%S')
         
      c) get_all_regions() -> list
         Purpose: Get list of all supported regions
         Returns: Sorted list of all region names
         Usage: For populating dropdowns/selectors
         
      d) is_valid_region(state_or_province: str) -> bool
         Purpose: Validate if region is supported
         Returns: True if region exists, False otherwise
         
   3. Built-in Test Suite (__main__ section)
      - 5 test examples demonstrating all functions
      - Can be run with: python src/utils/timezone_map.py

================================================================================

TIMEZONE DATA SOURCE:

All timezone offsets extracted from Updates.md specification:
- Reference time: NOW() - 3:00 (Eastern Time)
- Formula: Local Time = NOW() - offset_hours - 3 hours
- Covers all time zones:
  - Eastern Time (ET): offset 4-5 hours
  - Central Time (CT): offset 5-6 hours  
  - Mountain Time (MT): offset 6-7 hours
  - Pacific Time (PT): offset 5-6 hours
  - Alaska/Hawaii: offset 4-6 hours
  - Canadian zones: offset 3.5-6 hours

US States Supported (50):
Alabama, Alaska, Arizona, Arkansas, California, Colorado, Connecticut, Delaware,
Florida, Georgia, Hawaii, Idaho, Illinois, Indiana, Iowa, Kansas, Kentucky,
Louisiana, Maine, Maryland, Massachusetts, Michigan, Minnesota, Mississippi,
Missouri, Montana, Nebraska, Nevada, New Hampshire, New Jersey, New Mexico,
New York, North Carolina, North Dakota, Ohio, Oklahoma, Oregon, Pennsylvania,
Rhode Island, South Carolina, South Dakota, Tennessee, Texas, Utah, Vermont,
Virginia, Washington, West Virginia, Wisconsin, Wyoming

Canadian Provinces/Territories (13):
Alberta, British Columbia, Manitoba, New Brunswick, Newfoundland and Labrador,
Northwest Territories, Nova Scotia, Nunavut, Ontario, Prince Edward Island,
Quebec, Saskatchewan, Yukon

================================================================================

INTEGRATION POINTS (For Future Implementation):

1. CompaniesProcess_v2.py
   Location: src/ART Q Control/CompaniesProcess_v2.py
   Future Update: Import timezone_map to add local time calculation
   
   Code Pattern:
   ```python
   from src.utils.timezone_map import calculate_local_time
   
   # In CompaniesProcess where company metadata is displayed:
   company_state = company_row['State/Province']
   local_time = calculate_local_time(company_state)
   metadata_display = f"Local Time: {local_time.strftime('%H:%M:%S')}"
   ```

2. Company Email Template Dialog
   Future Use: Display company timezone and local time in email preview
   
3. Case Reviewer Dialog
   Future Use: Show local time context for companies

4. Excel Data Processing
   Location: src/file_processing/processor.py
   Future Use: Extract company state/province and lookup timezone

================================================================================

USAGE EXAMPLES:

# Example 1: Get timezone offset
from src.utils.timezone_map import get_timezone_offset
offset = get_timezone_offset("California")  # Returns: 5.0

# Example 2: Calculate local time
from src.utils.timezone_map import calculate_local_time
local = calculate_local_time("Texas")
print(f"Texas local time: {local.strftime('%H:%M:%S')}")

# Example 3: Validate region
from src.utils.timezone_map import is_valid_region
if is_valid_region("New York"):
    print("Valid region for timezone lookup")

# Example 4: Get all regions (for dropdowns)
from src.utils.timezone_map import get_all_regions
regions = get_all_regions()  # Returns sorted list of all 64 regions

# Example 5: Case-insensitive lookup
offset = get_timezone_offset("FLORIDA")  # Works: returns 4.0
offset = get_timezone_offset("florida")  # Works: returns 4.0
offset = get_timezone_offset("Florida")  # Works: returns 4.0

================================================================================

TESTING:

Run the module's built-in tests:
cd c:\Users\EhabElrify\Desktop\Projects\ART Q Master
python src/utils/timezone_map.py

Expected Output:
============================================================
Timezone Map Module - Test Examples
============================================================

[Test 1] Get timezone offset for California:
  Offset: 5.0 hours

[Test 2] Calculate local time for Texas:
  Current UTC: 2026-01-27 XX:XX:XX
  Local Time: 2026-01-27 XX:XX:XX

[Test 3] Case-insensitive lookup (NEW YORK):
  Offset: 4.0 hours

[Test 4] Total supported regions:
  Total: 64
  US States: 50
  First 5: ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California']
  Last 5: ['West Virginia', 'Wisconsin', 'Wyoming', 'Yukon']

[Test 5] Invalid region lookup:
  Result: None

================================================================================

DEPENDENCIES:

- Python 3.6+ (for datetime.timedelta and type hints)
- No external dependencies required
- Uses only Python standard library: datetime, typing

================================================================================

NEXT PHASE:

Phase 5.3 - Previous Case Feature Fix & Navigation Breadcrumb
- Fix current non-functional Previous Case navigation
- Improve navigation breadcrumb display
- Better visual indication of current position in case list

Files to Modify:
- src/ART Q Control/CaseReviewer_v2.py
- src/ui/components/

================================================================================

NOTES:

- Timezone data is hardcoded as specified in requirements
- No internet/API calls needed for timezone lookups
- Module is self-contained and testable
- Can be easily extended with additional regions if needed
- All lookups are case-insensitive for user-friendliness
- Partial string matching provides flexibility for abbreviations

================================================================================

Documentation: Phase_5_2_COMPANY_METADATA.md
Created: January 27, 2026
Next Review: After Phase 5.3 completion
"""
