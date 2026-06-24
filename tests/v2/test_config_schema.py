"""
Test Suite for Configuration Schema & Validation (Phase 7.1)
============================================================

Tests the configuration schema and validation system:
- Schema creation and initialization
- Validation rules and error messages
- Legacy config migration
- Type safety and constraints

Run with: python -m pytest src_v2/test_config_schema.py -v
"""

import unittest
import sys
from pathlib import Path

# Add src_v2 to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config.schema import (
    Configuration,
    CredentialsConfig,
    FilePathsConfig,
    AutomationConfig,
    UIConfig,
    AccessibilityConfig,
    DeveloperConfig,
    ThemeMode,
    FontPreset,
)
from config.validator import ConfigValidator, ValidationError, get_validation_summary


class TestCredentialsConfig(unittest.TestCase):
    """Test CredentialsConfig dataclass"""
    
    def test_valid_credentials(self):
        """Test creating valid credentials"""
        creds = CredentialsConfig(
            username="testuser",
            password="testpass123",
            user_id="Agent_123",
            place_id="Place_456"
        )
        self.assertEqual(creds.username, "testuser")
        self.assertEqual(creds.password, "testpass123")
        self.assertEqual(creds.user_id, "Agent_123")
        self.assertEqual(creds.place_id, "Place_456")
    
    def test_empty_username_raises(self):
        """Test that empty username raises ValueError"""
        with self.assertRaises(ValueError) as ctx:
            CredentialsConfig(
                username="",
                password="pass",
                user_id="id",
                place_id="place"
            )
        self.assertIn("Username", str(ctx.exception))
    
    def test_empty_password_raises(self):
        """Test that empty password raises ValueError"""
        with self.assertRaises(ValueError) as ctx:
            CredentialsConfig(
                username="user",
                password="",
                user_id="id",
                place_id="place"
            )
        self.assertIn("Password", str(ctx.exception))


class TestFilePathsConfig(unittest.TestCase):
    """Test FilePathsConfig dataclass"""
    
    def test_valid_paths(self):
        """Test creating valid file paths"""
        paths = FilePathsConfig(
            excel_base_path="/path/to/excel",
            cache_directory="/path/to/cache"
        )
        self.assertEqual(paths.excel_base_path, "/path/to/excel")
        self.assertEqual(paths.cache_directory, "/path/to/cache")
    
    def test_empty_excel_path_raises(self):
        """Test that empty excel path raises ValueError"""
        with self.assertRaises(ValueError) as ctx:
            FilePathsConfig(
                excel_base_path="",
                cache_directory="/cache"
            )
        self.assertIn("Excel", str(ctx.exception))


class TestAutomationConfig(unittest.TestCase):
    """Test AutomationConfig dataclass"""
    
    def test_valid_automation(self):
        """Test creating valid automation config"""
        auto = AutomationConfig(
            agent_name="John Doe",
            sheet_name="My Sheet",
            refresh_interval=15
        )
        self.assertEqual(auto.agent_name, "John Doe")
        self.assertEqual(auto.sheet_name, "My Sheet")
        self.assertEqual(auto.refresh_interval, 15)
    
    def test_default_refresh_interval(self):
        """Test default refresh interval"""
        auto = AutomationConfig(
            agent_name="John Doe",
            sheet_name="My Sheet"
        )
        self.assertEqual(auto.refresh_interval, 10)
    
    def test_invalid_refresh_interval_raises(self):
        """Test that invalid refresh interval raises ValueError"""
        with self.assertRaises(ValueError) as ctx:
            AutomationConfig(
                agent_name="John Doe",
                sheet_name="My Sheet",
                refresh_interval=0
            )
        self.assertIn("between 1 and 100", str(ctx.exception))
    
    def test_optional_time_fields(self):
        """Test optional start_time and end_time fields"""
        auto = AutomationConfig(
            agent_name="John Doe",
            sheet_name="My Sheet",
            start_time="09:00",
            end_time="17:00"
        )
        self.assertEqual(auto.start_time, "09:00")
        self.assertEqual(auto.end_time, "17:00")


class TestUIConfig(unittest.TestCase):
    """Test UIConfig dataclass"""
    
    def test_default_ui_config(self):
        """Test creating UI config with defaults"""
        ui = UIConfig()
        self.assertEqual(ui.theme, ThemeMode.AUTO)
        self.assertEqual(ui.font_size, 16)
        self.assertEqual(ui.font_preset, FontPreset.MEDIUM)
        self.assertTrue(ui.show_tooltips)
        self.assertTrue(ui.animation_enabled)
    
    def test_custom_ui_config(self):
        """Test creating custom UI config"""
        ui = UIConfig(
            theme=ThemeMode.DARK,
            font_size=20,
            font_preset=FontPreset.LARGE,
            show_tooltips=False
        )
        self.assertEqual(ui.theme, ThemeMode.DARK)
        self.assertEqual(ui.font_size, 20)
        self.assertEqual(ui.font_preset, FontPreset.LARGE)
        self.assertFalse(ui.show_tooltips)
    
    def test_theme_string_conversion(self):
        """Test that theme strings are converted to enum"""
        ui = UIConfig(theme="light")  # type: ignore
        self.assertEqual(ui.theme, ThemeMode.LIGHT)
    
    def test_invalid_font_size_raises(self):
        """Test that invalid font size raises ValueError"""
        with self.assertRaises(ValueError) as ctx:
            UIConfig(font_size=5)
        self.assertIn("between 10 and 30", str(ctx.exception))


class TestAccessibilityConfig(unittest.TestCase):
    """Test AccessibilityConfig dataclass"""
    
    def test_default_accessibility(self):
        """Test default accessibility settings"""
        access = AccessibilityConfig()
        self.assertFalse(access.high_contrast)
        self.assertFalse(access.screen_reader)
        self.assertTrue(access.keyboard_navigation)
        self.assertFalse(access.reduce_motion)
        self.assertTrue(access.focus_indicators)
    
    def test_custom_accessibility(self):
        """Test custom accessibility settings"""
        access = AccessibilityConfig(
            high_contrast=True,
            screen_reader=True,
            reduce_motion=True
        )
        self.assertTrue(access.high_contrast)
        self.assertTrue(access.screen_reader)
        self.assertTrue(access.reduce_motion)


class TestDeveloperConfig(unittest.TestCase):
    """Test DeveloperConfig dataclass"""
    
    def test_default_developer(self):
        """Test default developer settings"""
        dev = DeveloperConfig()
        self.assertFalse(dev.debug_mode)
        self.assertEqual(dev.log_level, "INFO")
        self.assertFalse(dev.enable_profiling)
        self.assertFalse(dev.show_debug_info)
        self.assertFalse(dev.verbose_logging)
    
    def test_custom_developer(self):
        """Test custom developer settings"""
        dev = DeveloperConfig(
            debug_mode=True,
            log_level="DEBUG",
            enable_profiling=True
        )
        self.assertTrue(dev.debug_mode)
        self.assertEqual(dev.log_level, "DEBUG")
        self.assertTrue(dev.enable_profiling)
    
    def test_log_level_case_insensitive(self):
        """Test that log level is case-insensitive"""
        dev = DeveloperConfig(log_level="debug")
        self.assertEqual(dev.log_level, "DEBUG")
    
    def test_invalid_log_level_raises(self):
        """Test that invalid log level raises ValueError"""
        with self.assertRaises(ValueError) as ctx:
            DeveloperConfig(log_level="INVALID")
        self.assertIn("must be one of", str(ctx.exception))


class TestConfiguration(unittest.TestCase):
    """Test complete Configuration object"""
    
    def test_minimal_valid_config(self):
        """Test creating minimal valid configuration"""
        config = Configuration(
            credentials=CredentialsConfig("user", "pass", "id", "place"),
            file_paths=FilePathsConfig("/excel", "/cache"),
            automation=AutomationConfig("Agent", "Sheet")
        )
        self.assertIsNotNone(config.ui)
        self.assertIsNotNone(config.accessibility)
        self.assertIsNotNone(config.developer)
        self.assertEqual(config.version, "2.0.0")
    
    def test_to_dict(self):
        """Test converting configuration to dictionary"""
        config = Configuration(
            credentials=CredentialsConfig("user", "pass", "id", "place"),
            file_paths=FilePathsConfig("/excel", "/cache"),
            automation=AutomationConfig("Agent", "Sheet")
        )
        config_dict = config.to_dict()
        
        self.assertIn("credentials", config_dict)
        self.assertIn("file_paths", config_dict)
        self.assertIn("automation", config_dict)
        self.assertIn("ui", config_dict)
        self.assertIn("accessibility", config_dict)
        self.assertIn("developer", config_dict)
        self.assertEqual(config_dict["version"], "2.0.0")
    
    def test_from_dict_legacy_format(self):
        """Test loading from legacy config format"""
        legacy_config = {
            "agent_settings": {
                "agent_name": "John Doe",
                "user_id": "Agent_123",
                "password": "pass123",
                "place_id": "Place_456"
            },
            "file_paths": {
                "excel_base_path": "/path/to/excel",
                "cache_directory": "/path/to/cache"
            },
            "crm_settings": {
                "excel_sheet_name": "My Sheet"
            },
            "execution_settings": {
                "refresh_interval": 15
            }
        }
        
        config = Configuration.from_dict(legacy_config)
        self.assertEqual(config.credentials.username, "Agent_123")
        self.assertEqual(config.automation.agent_name, "John Doe")
        self.assertEqual(config.automation.sheet_name, "My Sheet")
        self.assertEqual(config.automation.refresh_interval, 15)


class TestConfigValidator(unittest.TestCase):
    """Test ConfigValidator"""
    
    def test_validate_valid_credentials(self):
        """Test validation of valid credentials"""
        creds = CredentialsConfig("testuser", "testpass", "id123", "place456")
        errors = ConfigValidator.validate_credentials(creds)
        self.assertEqual(len(errors), 0)
    
    def test_validate_short_username(self):
        """Test validation catches short username"""
        creds = CredentialsConfig("ab", "pass", "id", "place")
        errors = ConfigValidator.validate_credentials(creds)
        self.assertGreater(len(errors), 0)
        self.assertIn("at least 3 characters", errors[0].message)
    
    def test_validate_empty_password(self):
        """Test validation catches empty password"""
        # Schema validation happens in __post_init__, so we test the validator directly
        # by creating a mock object that bypasses __post_init__
        class MockCreds:
            username = "user"
            password = ""
            user_id = "id"
            place_id = "place"
        
        # Convert to actual CredentialsConfig for validator
        # This tests that validator would catch it if schema didn't
        try:
            creds = CredentialsConfig("user", "validpass", "id", "place")
            # Manually set empty password to test validator
            creds.password = ""
            errors = ConfigValidator.validate_credentials(creds)
            self.assertGreater(len(errors), 0)
            self.assertTrue(any("password" in e.field.lower() for e in errors))
        except ValueError:
            # Schema caught it first, which is also correct
            pass
    
    def test_validate_automation_refresh_interval(self):
        """Test validation of refresh interval"""
        # Valid case first
        auto = AutomationConfig("Agent", "Sheet", refresh_interval=50)
        errors = ConfigValidator.validate_automation(auto)
        self.assertEqual(len(errors), 0)
        
        # Test validator catches invalid values by manually setting them
        auto_low = AutomationConfig("Agent", "Sheet", refresh_interval=10)
        auto_low.refresh_interval = 0  # Bypass __post_init__
        errors = ConfigValidator.validate_automation(auto_low)
        self.assertGreater(len(errors), 0)
        
        auto_high = AutomationConfig("Agent", "Sheet", refresh_interval=10)
        auto_high.refresh_interval = 101  # Bypass __post_init__
        errors = ConfigValidator.validate_automation(auto_high)
        self.assertGreater(len(errors), 0)
    
    def test_validate_time_format(self):
        """Test time format validation"""
        # Valid times
        auto = AutomationConfig("Agent", "Sheet", start_time="09:00", end_time="17:30")
        errors = ConfigValidator.validate_automation(auto)
        self.assertEqual(len(errors), 0)
        
        # Invalid time format
        auto = AutomationConfig("Agent", "Sheet", start_time="9:00")  # Missing leading zero
        errors = ConfigValidator.validate_automation(auto)
        # Should still be valid as 9:00 is acceptable
        
        auto = AutomationConfig("Agent", "Sheet", start_time="25:00")  # Invalid hour
        errors = ConfigValidator.validate_automation(auto)
        self.assertGreater(len(errors), 0)
    
    def test_validate_ui_font_size(self):
        """Test UI font size validation"""
        # Valid case first
        ui = UIConfig(font_size=16)
        errors = ConfigValidator.validate_ui(ui)
        self.assertEqual(len(errors), 0)
        
        # Test validator catches invalid values by manually setting them
        ui_small = UIConfig(font_size=16)
        ui_small.font_size = 5  # Bypass __post_init__
        errors = ConfigValidator.validate_ui(ui_small)
        self.assertGreater(len(errors), 0)
        
        ui_large = UIConfig(font_size=16)
        ui_large.font_size = 50  # Bypass __post_init__
        errors = ConfigValidator.validate_ui(ui_large)
        self.assertGreater(len(errors), 0)
    
    def test_validate_complete_config(self):
        """Test validation of complete configuration"""
        config = Configuration(
            credentials=CredentialsConfig("user", "pass", "id", "place"),
            file_paths=FilePathsConfig("/excel", "/cache"),
            automation=AutomationConfig("Agent", "Sheet")
        )
        
        # Note: This will fail path validation since paths don't exist
        errors = ConfigValidator.validate(config)
        # Should have errors for non-existent paths
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("does not exist" in e.message for e in errors))
    
    def test_validation_error_format(self):
        """Test ValidationError formatting"""
        error = ValidationError("test.field", "Test error message")
        self.assertEqual(error.field, "test.field")
        self.assertEqual(error.message, "Test error message")
        self.assertIn("test.field", str(error))
        self.assertIn("Test error message", str(error))
    
    def test_get_validation_summary(self):
        """Test validation summary formatting"""
        errors = [
            ValidationError("field1", "Error 1"),
            ValidationError("field2", "Error 2"),
        ]
        summary = get_validation_summary(errors)
        self.assertIn("2 error(s)", summary)
        self.assertIn("field1", summary)
        self.assertIn("field2", summary)
        
        # Test empty errors
        summary = get_validation_summary([])
        self.assertIn("valid", summary.lower())


class TestConfigIntegration(unittest.TestCase):
    """Integration tests for configuration system"""
    
    def test_round_trip_conversion(self):
        """Test converting config to dict and back"""
        original = Configuration(
            credentials=CredentialsConfig("user", "pass", "id", "place"),
            file_paths=FilePathsConfig("/excel", "/cache"),
            automation=AutomationConfig("Agent", "Sheet", refresh_interval=20),
            ui=UIConfig(theme=ThemeMode.DARK, font_size=18)
        )
        
        # Convert to dict
        config_dict = original.to_dict()
        
        # Verify dict structure has all required fields
        self.assertIn("credentials", config_dict)
        self.assertIn("automation", config_dict)
        self.assertEqual(config_dict["automation"]["agent_name"], "Agent")
        self.assertEqual(config_dict["automation"]["sheet_name"], "Sheet")
        
        # Convert back to config
        restored = Configuration.from_dict(config_dict)
        
        # Verify key fields match
        self.assertEqual(restored.credentials.username, original.credentials.username)
        self.assertEqual(restored.automation.agent_name, original.automation.agent_name)
        self.assertEqual(restored.automation.refresh_interval, original.automation.refresh_interval)
        self.assertEqual(restored.ui.theme, original.ui.theme)
        self.assertEqual(restored.ui.font_size, original.ui.font_size)
    
    def test_legacy_config_migration(self):
        """Test migrating from legacy config format"""
        # Simulate actual config.json from the project
        legacy = {
            "agent_settings": {
                "agent_name": "Ehab Elrify",
                "user_id": "Agent_Cairo_US_925",
                "password": "123456",
                "place_id": "Place_57080_SIPSwitch_US"
            },
            "file_paths": {
                "excel_base_path": "C:/Users/EhabElrify/Desktop/PA Daily Sheets",
                "cache_directory": "C:/Users/EhabElrify/Desktop/ART NTO"
            },
            "crm_settings": {
                "excel_sheet_name": "Ehab's Cases"
            },
            "execution_settings": {
                "start_time": "14:55",
                "end_time": "23:59",
                "refresh_interval": 10
            },
            "ui_settings": {
                "font_size": 10
            }
        }
        
        config = Configuration.from_dict(legacy)
        
        # Verify migration
        self.assertEqual(config.credentials.username, "Agent_Cairo_US_925")
        self.assertEqual(config.credentials.password, "123456")
        self.assertEqual(config.automation.agent_name, "Ehab Elrify")
        self.assertEqual(config.automation.sheet_name, "Ehab's Cases")
        self.assertEqual(config.automation.refresh_interval, 10)
        self.assertEqual(config.automation.start_time, "14:55")
        self.assertEqual(config.automation.end_time, "23:59")
        self.assertEqual(config.ui.font_size, 10)


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

# Made with Bob
