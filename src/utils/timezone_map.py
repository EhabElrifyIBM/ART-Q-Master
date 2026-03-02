"""
Timezone Mapping Module for ART Q Master
=========================================

This module provides timezone offset mappings for all US states and Canadian provinces.
Used to calculate local time for companies based on their location.

Reference UTC: NOW() - 3:00 (Eastern Time with 3-hour offset reference)

Each offset represents the hours behind the reference time to calculate local time.
Formula: Local Time = NOW() - offset_hours - 3 hours

Author: ART Q Master Development
Version: 1.0
Phase: 5.2 - Company Metadata Implementation
"""

from datetime import datetime, timedelta
from typing import Dict, Optional


# Timezone offset mapping in hours
# Format: "State/Province Name": hours_offset_from_reference
# Reference: NOW() - 3:00 (Eastern Time)
# To calculate local time: datetime.now() - timedelta(hours=offset)

TIMEZONE_MAP: Dict[str, float] = {
    # US States
    "Alabama": 5.0,
    "Alaska": 4.0,
    "Arizona": 8.0,
    "Arkansas": 6.0,
    "California": 5.0,
    "Colorado": 7.0,
    "Connecticut": 6.0,
    "Delaware": 4.0,
    "Florida": 4.0,
    "Georgia": 4.0,
    "Hawaii": 6.0,
    "Idaho": 4.0,
    "Illinois": 5.0,
    "Indiana": 6.0,
    "Iowa": 4.0,
    "Kansas": 4.0,
    "Kentucky": 5.0,
    "Louisiana": 5.0,
    "Maine": 5.0,
    "Maryland": 5.0,
    "Massachusetts": 6.0,
    "Michigan": 4.0,
    "Minnesota": 5.0,
    "Mississippi": 6.0,
    "Missouri": 4.0,
    "Montana": 6.0,
    "Nebraska": 4.0,
    "Nevada": 5.0,
    "New Hampshire": 5.0,
    "New Jersey": 6.0,
    "New Mexico": 4.0,
    "New York": 4.0,
    "North Carolina": 4.0,
    "North Dakota": 5.0,
    "Ohio": 5.0,
    "Oklahoma": 6.0,
    "Oregon": 4.0,
    "Pennsylvania": 5.0,
    "Rhode Island": 6.0,
    "South Carolina": 4.0,
    "South Dakota": 4.0,
    "Tennessee": 4.0,
    "Texas": 5.0,
    "Utah": 6.0,
    "Vermont": 4.0,
    "Virginia": 4.0,
    "Washington": 5.0,
    "West Virginia": 6.0,
    "Wisconsin": 4.0,
    "Wyoming": 4.0,
    
    # Canadian Provinces
    "Alberta": 5.0,
    "British Columbia": 6.0,
    "Manitoba": 4.0,
    "New Brunswick": 4.0,
    "Newfoundland and Labrador": 3.5,
    "Northwest Territories": 5.0,
    "Nova Scotia": 4.0,
    "Nunavut": 4.0,
    "Ontario": 5.0,
    "Prince Edward Island": 4.0,
    "Quebec": 5.0,
    "Saskatchewan": 4.0,
    "Yukon": 6.0,
}


def get_timezone_offset(state_or_province: str) -> Optional[float]:
    """
    Get timezone offset for a given state or province.
    
    Args:
        state_or_province (str): Name of US state or Canadian province
        
    Returns:
        float: Offset in hours, or None if state/province not found
        
    Example:
        >>> get_timezone_offset("California")
        5.0
        >>> get_timezone_offset("British Columbia")
        6.0
    """
    # Try exact match first
    if state_or_province in TIMEZONE_MAP:
        return TIMEZONE_MAP[state_or_province]
    
    # Try case-insensitive match
    state_lower = state_or_province.lower().strip()
    for region, offset in TIMEZONE_MAP.items():
        if region.lower() == state_lower:
            return offset
    
    # Try partial match (for abbreviations or variations)
    for region, offset in TIMEZONE_MAP.items():
        if state_lower in region.lower() or region.lower() in state_lower:
            return offset
    
    return None


def calculate_local_time(state_or_province: str, utc_datetime: Optional[datetime] = None) -> Optional[datetime]:
    """
    Calculate local time for a given state or province.
    
    Args:
        state_or_province (str): Name of US state or Canadian province
        utc_datetime (datetime, optional): UTC datetime to convert. Defaults to current UTC time.
        
    Returns:
        datetime: Local time for the state/province, or None if state/province not found
        
    Example:
        >>> local_time = calculate_local_time("California")
        >>> print(f"Local time in California: {local_time.strftime('%H:%M:%S')}")
    """
    offset = get_timezone_offset(state_or_province)
    
    if offset is None:
        return None
    
    if utc_datetime is None:
        utc_datetime = datetime.utcnow()
    
    # Apply offset: subtract hours to get local time
    local_time = utc_datetime - timedelta(hours=offset)
    
    return local_time


def get_all_regions() -> list:
    """
    Get list of all supported regions (states and provinces).
    
    Returns:
        list: Sorted list of all region names
    """
    return sorted(TIMEZONE_MAP.keys())


def is_valid_region(state_or_province: str) -> bool:
    """
    Check if a state or province is in the timezone map.
    
    Args:
        state_or_province (str): Name of state or province to check
        
    Returns:
        bool: True if region exists in map, False otherwise
    """
    return get_timezone_offset(state_or_province) is not None


# Example usage and reference data structure
if __name__ == "__main__":
    # Test the timezone functions
    print("=" * 60)
    print("Timezone Map Module - Test Examples")
    print("=" * 60)
    
    # Test 1: Get specific timezone offset
    print("\n[Test 1] Get timezone offset for California:")
    offset = get_timezone_offset("California")
    print(f"  Offset: {offset} hours")
    
    # Test 2: Calculate local time
    print("\n[Test 2] Calculate local time for Texas:")
    local = calculate_local_time("Texas")
    print(f"  Current UTC: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Local Time: {local.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 3: Case-insensitive lookup
    print("\n[Test 3] Case-insensitive lookup (NEW YORK):")
    offset = get_timezone_offset("NEW YORK")
    print(f"  Offset: {offset} hours")
    
    # Test 4: List all regions
    print("\n[Test 4] Total supported regions:")
    regions = get_all_regions()
    print(f"  Total: {len(regions)}")
    print(f"  US States: {len([r for r in regions if r not in TIMEZONE_MAP or TIMEZONE_MAP.get(r)])}")
    print(f"  First 5: {regions[:5]}")
    print(f"  Last 5: {regions[-5:]}")
    
    # Test 5: Invalid region
    print("\n[Test 5] Invalid region lookup:")
    offset = get_timezone_offset("Invalid State")
    print(f"  Result: {offset}")
