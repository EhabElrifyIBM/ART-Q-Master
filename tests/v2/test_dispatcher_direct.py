"""Direct test of Dispatcher config loading"""
import sys
import os

# Setup paths
src_v2_dir = os.path.dirname(os.path.abspath(__file__))
artq_dir = os.path.join(src_v2_dir, 'ART Q Control')
sys.path.insert(0, src_v2_dir)
sys.path.insert(0, artq_dir)

# Change to ART Q Control directory
os.chdir(artq_dir)

print(f"Working directory: {os.getcwd()}")
print(f"Config exists: {os.path.exists('config.json')}")

# Now test config loading
from Dispatcher_v2 import _get_config_values, _ensure_app

_ensure_app()
config = _get_config_values()

print(f"\nConfig values:")
print(f"  Agent: {config['agent_name']}")
print(f"  User ID: {config['user_id']}")
print(f"  Sheet: {config['sheet_name']}")
print(f"  Config Manager: {type(config['config_manager']).__name__}")

if config['agent_name']:
    print("\n✓ Config loaded successfully!")
else:
    print("\n✗ Config values are None")

# Made with Bob
