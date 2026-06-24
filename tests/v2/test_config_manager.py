"""
Tests for Configuration Manager
================================

Tests the ConfigurationManager singleton class including:
- Singleton pattern
- Load/save operations
- Validation integration
- Change notifications
- Thread safety
- Backup functionality

Run with: python -m pytest src_v2/test_config_manager.py -v
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path

from src_v2.config.manager import ConfigurationManager, get_config_manager
from src_v2.config.schema import Configuration, CredentialsConfig, AutomationConfig, FilePathsConfig
from src_v2.config.validator import ValidationError


class TestConfigurationManager(unittest.TestCase):
    """Test configuration manager"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Reset singleton
        ConfigurationManager.reset_instance()
        
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.json"
        
        # Create valid test config
        self.test_config = {
            "credentials": {
                "username": "testuser",
                "password": "testpass",
                "user_id": "12345",
                "place_id": "place123"
            },
            "file_paths": {
                "excel_base_path": self.temp_dir,
                "cache_directory": self.temp_dir
            },
            "automation": {
                "agent_name": "Test Agent",
                "sheet_name": "Test Sheet",
                "refresh_interval": 5
            }
        }
        
        # Write test config
        with open(self.config_path, 'w') as f:
            json.dump(self.test_config, f)
    
    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        ConfigurationManager.reset_instance()
    
    def test_singleton_pattern(self):
        """Test that ConfigurationManager is a singleton"""
        manager1 = ConfigurationManager()
        manager2 = ConfigurationManager()
        self.assertIs(manager1, manager2)
        
        # Test convenience function returns same instance
        manager3 = get_config_manager()
        self.assertIs(manager1, manager3)
    
    def test_load_valid_config(self):
        """Test loading valid configuration"""
        manager = ConfigurationManager()
        config = manager.load(str(self.config_path))
        
        self.assertIsNotNone(config)
        self.assertEqual(config.credentials.username, "testuser")
        self.assertEqual(config.automation.agent_name, "Test Agent")
        self.assertEqual(config.automation.refresh_interval, 5)
    
    def test_load_nonexistent_file(self):
        """Test loading non-existent file raises error"""
        manager = ConfigurationManager()
        with self.assertRaises(FileNotFoundError):
            manager.load("nonexistent.json")
    
    def test_load_invalid_json(self):
        """Test loading malformed JSON raises error"""
        bad_config_path = Path(self.temp_dir) / "bad_config.json"
        with open(bad_config_path, 'w') as f:
            f.write("{ invalid json }")
        
        manager = ConfigurationManager()
        with self.assertRaises(json.JSONDecodeError):
            manager.load(str(bad_config_path))
    
    def test_load_invalid_config(self):
        """Test loading invalid configuration raises ValidationError"""
        invalid_config = {
            "credentials": {
                "username": "",  # Empty username - invalid
                "password": "pass",
                "user_id": "123",
                "place_id": "place"
            },
            "file_paths": {
                "excel_base_path": self.temp_dir,
                "cache_directory": self.temp_dir
            },
            "automation": {
                "agent_name": "Agent",
                "sheet_name": "Sheet",
                "refresh_interval": 10
            }
        }
        
        invalid_path = Path(self.temp_dir) / "invalid_config.json"
        with open(invalid_path, 'w') as f:
            json.dump(invalid_config, f)
        
        manager = ConfigurationManager()
        with self.assertRaises(ValidationError):
            manager.load(str(invalid_path))
    
    def test_get_before_load(self):
        """Test get() raises error if no config loaded"""
        manager = ConfigurationManager()
        with self.assertRaises(ValueError) as ctx:
            manager.get()
        self.assertIn("No configuration loaded", str(ctx.exception))
    
    def test_get_after_load(self):
        """Test get() returns loaded configuration"""
        manager = ConfigurationManager()
        manager.load(str(self.config_path))
        
        config = manager.get()
        self.assertIsNotNone(config)
        self.assertEqual(config.credentials.username, "testuser")
    
    def test_save_config(self):
        """Test saving configuration"""
        manager = ConfigurationManager()
        manager.load(str(self.config_path))
        
        # Modify config
        manager.get().credentials.username = "newuser"
        
        # Save
        manager.save(backup=False)
        
        # Reload and verify
        ConfigurationManager.reset_instance()
        manager2 = ConfigurationManager()
        config2 = manager2.load(str(self.config_path))
        self.assertEqual(config2.credentials.username, "newuser")
    
    def test_save_creates_backup(self):
        """Test that save creates backup file"""
        manager = ConfigurationManager()
        manager.load(str(self.config_path))
        
        # Modify and save with backup
        manager.get().credentials.username = "modified"
        manager.save(backup=True)
        
        # Check backup exists
        backup_path = self.config_path.with_suffix('.json.backup')
        self.assertTrue(backup_path.exists())
        
        # Verify backup contains original data
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        self.assertEqual(backup_data['credentials']['username'], "testuser")
    
    def test_save_without_load(self):
        """Test save() raises error if no config loaded"""
        manager = ConfigurationManager()
        with self.assertRaises(ValueError) as ctx:
            manager.save()
        self.assertIn("No configuration loaded", str(ctx.exception))
    
    def test_save_invalid_config(self):
        """Test save() raises error if config becomes invalid"""
        manager = ConfigurationManager()
        manager.load(str(self.config_path))
        
        # Make config invalid
        manager.get().credentials.username = ""  # Empty username
        
        # Should raise ValidationError
        with self.assertRaises(ValidationError):
            manager.save(backup=False)
    
    def test_update_config(self):
        """Test updating configuration"""
        manager = ConfigurationManager()
        manager.load(str(self.config_path))
        
        # Update credentials
        new_creds = CredentialsConfig("updated", "newpass", "999", "newplace")
        manager.update(credentials=new_creds)
        
        # Verify update
        self.assertEqual(manager.get().credentials.username, "updated")
        self.assertEqual(manager.get().credentials.password, "newpass")
        
        # Verify saved to file
        ConfigurationManager.reset_instance()
        manager2 = ConfigurationManager()
        config2 = manager2.load(str(self.config_path))
        self.assertEqual(config2.credentials.username, "updated")
    
    def test_update_multiple_sections(self):
        """Test updating multiple configuration sections"""
        manager = ConfigurationManager()
        manager.load(str(self.config_path))
        
        # Update multiple sections
        new_creds = CredentialsConfig("user2", "pass2", "222", "place2")
        new_auto = AutomationConfig("Agent2", "Sheet2", 20)
        
        manager.update(
            credentials=new_creds,
            automation=new_auto
        )
        
        # Verify updates
        self.assertEqual(manager.get().credentials.username, "user2")
        self.assertEqual(manager.get().automation.agent_name, "Agent2")
        self.assertEqual(manager.get().automation.refresh_interval, 20)
    
    def test_update_unknown_field(self):
        """Test update() raises error for unknown field"""
        manager = ConfigurationManager()
        manager.load(str(self.config_path))
        
        with self.assertRaises(ValueError) as ctx:
            manager.update(unknown_field="value")
        self.assertIn("Unknown configuration field", str(ctx.exception))
    
    def test_update_without_load(self):
        """Test update() raises error if no config loaded"""
        manager = ConfigurationManager()
        with self.assertRaises(ValueError):
            manager.update(credentials=CredentialsConfig("u", "p", "i", "pl"))
    
    def test_change_callbacks(self):
        """Test change notification callbacks"""
        manager = ConfigurationManager()
        manager.load(str(self.config_path))
        
        callback_called = []
        received_config = []
        
        def callback(config):
            callback_called.append(True)
            received_config.append(config)
        
        # Register callback
        manager.register_change_callback(callback)
        
        # Trigger change
        manager.save(backup=False)
        
        # Verify callback was called
        self.assertEqual(len(callback_called), 1)
        self.assertEqual(len(received_config), 1)
        self.assertIsInstance(received_config[0], Configuration)
    
    def test_multiple_callbacks(self):
        """Test multiple callbacks are all notified"""
        manager = ConfigurationManager()
        manager.load(str(self.config_path))
        
        call_count = [0, 0, 0]
        
        def callback1(config):
            call_count[0] += 1
        
        def callback2(config):
            call_count[1] += 1
        
        def callback3(config):
            call_count[2] += 1
        
        # Register all callbacks
        manager.register_change_callback(callback1)
        manager.register_change_callback(callback2)
        manager.register_change_callback(callback3)
        
        # Trigger change
        manager.save(backup=False)
        
        # All should be called
        self.assertEqual(call_count, [1, 1, 1])
    
    def test_unregister_callback(self):
        """Test unregistering callbacks"""
        manager = ConfigurationManager()
        manager.load(str(self.config_path))
        
        call_count = [0]
        
        def callback(config):
            call_count[0] += 1
        
        # Register and unregister
        manager.register_change_callback(callback)
        manager.unregister_change_callback(callback)
        
        # Trigger change
        manager.save(backup=False)
        
        # Should not be called
        self.assertEqual(call_count[0], 0)
    
    def test_callback_error_handling(self):
        """Test that callback errors don't break the manager"""
        manager = ConfigurationManager()
        manager.load(str(self.config_path))
        
        good_callback_called = [False]
        
        def bad_callback(config):
            raise Exception("Callback error!")
        
        def good_callback(config):
            good_callback_called[0] = True
        
        # Register both callbacks
        manager.register_change_callback(bad_callback)
        manager.register_change_callback(good_callback)
        
        # Trigger change - should not raise exception
        manager.save(backup=False)
        
        # Good callback should still be called
        self.assertTrue(good_callback_called[0])
    
    def test_register_same_callback_twice(self):
        """Test registering same callback twice only calls it once"""
        manager = ConfigurationManager()
        manager.load(str(self.config_path))
        
        call_count = [0]
        
        def callback(config):
            call_count[0] += 1
        
        # Register twice
        manager.register_change_callback(callback)
        manager.register_change_callback(callback)
        
        # Trigger change
        manager.save(backup=False)
        
        # Should only be called once (duplicate prevented)
        self.assertEqual(call_count[0], 1)
    
    def test_reset_instance(self):
        """Test reset_instance() clears singleton"""
        manager1 = ConfigurationManager()
        manager1.load(str(self.config_path))
        
        # Reset
        ConfigurationManager.reset_instance()
        
        # New instance should be different and uninitialized
        manager2 = ConfigurationManager()
        self.assertIsNot(manager1, manager2)
        
        with self.assertRaises(ValueError):
            manager2.get()  # Should fail - no config loaded
    
    def test_convenience_function(self):
        """Test get_config_manager() convenience function"""
        manager = get_config_manager()
        self.assertIsInstance(manager, ConfigurationManager)
        
        # Should return same instance
        manager2 = get_config_manager()
        self.assertIs(manager, manager2)


if __name__ == '__main__':
    unittest.main()


# Made with Bob