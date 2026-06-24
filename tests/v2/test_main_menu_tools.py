"""
Test script to verify main menu tools are registered and visible.
"""

import sys
from utils.tool_registry import get_shell_cards, get_tool_definitions

def test_tool_registry():
    """Test that all tools are registered correctly."""
    print("=" * 60)
    print("TOOL REGISTRY TEST")
    print("=" * 60)
    
    # Get all tool definitions
    tools = list(get_tool_definitions())
    print(f"\n[OK] Total tools registered: {len(tools)}")
    
    # Print each tool (skip emojis for Windows console)
    for tool in tools:
        print(f"\n  - {tool.display_name}")
        print(f"     ID: {tool.tool_id}")
        print(f"     Area: {tool.area}")
        print(f"     Status: {tool.status}")
    
    # Get shell cards format
    shell_cards = get_shell_cards()
    print(f"\n[OK] Shell cards generated: {len(shell_cards)}")
    
    print("\n" + "=" * 60)
    print("All tools should appear in the 'All Tools' section")
    print("=" * 60)
    
    return len(tools) == 5  # Expected: 5 tools

if __name__ == "__main__":
    success = test_tool_registry()
    sys.exit(0 if success else 1)

# Made with Bob
