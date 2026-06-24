"""Test config loading fix"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ART Q Control'))

from config_loader import init_config

print("Testing config loading...")
cm = init_config()
print(f"Agent: {cm.get_value('agent_settings', 'agent_name')}")
print(f"User ID: {cm.get_value('agent_settings', 'user_id')}")
print(f"Sheet: {cm.get_value('crm_settings', 'excel_sheet_name')}")
print("Config loaded successfully!")

# Made with Bob
