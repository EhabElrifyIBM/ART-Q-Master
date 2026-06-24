# -*- coding: utf-8 -*-
"""
Complete Configuration System Tests - Phase 7
Tests all components: Schema, Validator, Manager, Migrator, Backup, Security
"""

import sys
import os
import io

# Set UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import sys
import os
import json
import tempfile
from pathlib import Path

# Add src_v2 to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src_v2.config import (
    ConfigManager,
    ConfigMigrator,
    ConfigBackup,
    AutoBackup,
    ConfigSecurity,
    config_manager,
)


def test_config_manager():
    """Test Phase 7.2: Configuration Manager"""
    print("\n=== Testing Configuration Manager ===")
    
    # Create temp config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_config = {
            "agent_name": "Test Agent",
            "cache_directory": "./test_cache",
            "ui_settings": {
                "theme": "dark",
                "font_size": 18,
                "animations_enabled": True,
                "compact_mode": False
            },
            "automation": {
                "refresh_interval": 10,
                "auto_screenshot": True,
                "max_retries": 3
            },
            "accessibility": {
                "high_contrast": False,
                "keyboard_navigation": True,
                "focus_indicators": True,
                "reduced_motion": False,
                "screen_reader_support": False
            },
            "advanced": {
                "debug_mode": False,
                "log_level": "INFO",
                "backup_enabled": True,
                "backup_count": 5
            },
            "credentials": {
                "username": "testuser",
                "password": "testpass"
            }
        }
        json.dump(test_config, f)
        temp_path = f.name
    
    try:
        # Test loading
        manager = ConfigManager()
        assert manager.load(temp_path), "Failed to load config"
        print("✓ Config loaded successfully")
        
        # Test get
        theme = manager.get('ui_settings.theme')
        assert theme == 'dark', f"Expected 'dark', got '{theme}'"
        print(f"✓ Get value: theme = {theme}")
        
        # Test set
        manager.set('ui_settings.theme', 'light', save_immediately=False)
        new_theme = manager.get('ui_settings.theme')
        assert new_theme == 'light', f"Expected 'light', got '{new_theme}'"
        print(f"✓ Set value: theme changed to {new_theme}")
        
        # Test get_section
        ui_section = manager.get_section('ui_settings')
        assert isinstance(ui_section, dict), "Section should be a dict"
        assert 'theme' in ui_section, "Section should contain 'theme'"
        print(f"✓ Get section: ui_settings has {len(ui_section)} keys")
        
        # Test callbacks
        callback_called = []
        def test_callback(key, old_val, new_val):
            callback_called.append((key, old_val, new_val))
        
        manager.register_callback(test_callback)
        manager.set('ui_settings.font_size', 20, save_immediately=False)
        assert len(callback_called) > 0, "Callback should have been called"
        print(f"✓ Callback system working: {len(callback_called)} calls")
        
        # Test save
        assert manager.save(backup=False), "Failed to save config"
        print("✓ Config saved successfully")
        
        print("✅ Configuration Manager: ALL TESTS PASSED")
        return True
        
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_migrator():
    """Test Phase 7.3: Migration System"""
    print("\n=== Testing Migration System ===")
    
    # Create V1 config
    v1_config = {
        "agent_name": "Old Agent",
        "cache_directory": "./old_cache",
        "username": "olduser",
        "password": "oldpass",
        "user_id": "user123",
        "place_id": "place456",
        "excel_base_path": "./excel",
        "sheet_name": "Sheet1",
        "refresh_interval": 5,
        "font_size": 16,
        "high_contrast": True,
        "debug_mode": False,
        "log_level": "DEBUG"
    }
    
    # Test version detection
    version = ConfigMigrator.detect_version(v1_config)
    assert version == 'v1', f"Expected 'v1', got '{version}'"
    print(f"✓ Version detected: {version}")
    
    # Test migration
    v2_config = ConfigMigrator.migrate_v1_to_v2(v1_config)
    assert 'credentials' in v2_config, "V2 config should have 'credentials'"
    assert 'automation' in v2_config, "V2 config should have 'automation'"
    assert 'ui' in v2_config, "V2 config should have 'ui'"
    assert v2_config['credentials']['username'] == 'olduser', "Username should be migrated"
    assert v2_config['automation']['agent_name'] == 'Old Agent', "Agent name should be migrated"
    print("✓ V1 to V2 migration successful")
    
    # Test V2 detection
    v2_version = ConfigMigrator.detect_version(v2_config)
    assert v2_version == 'v2', f"Expected 'v2', got '{v2_version}'"
    print(f"✓ V2 config detected correctly: {v2_version}")
    
    # Test migration report
    report = ConfigMigrator.create_migration_report(v1_config, v2_config)
    assert 'Migrated from: v1' in report, "Report should show source version"
    assert 'Migrated to: v2' in report, "Report should show target version"
    print("✓ Migration report generated")
    
    print("✅ Migration System: ALL TESTS PASSED")
    return True


def test_backup():
    """Test Phase 7.4: Backup System"""
    print("\n=== Testing Backup System ===")
    
    # Create temp config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_config = {
            "agent_name": "Backup Test",
            "cache_directory": "./cache"
        }
        json.dump(test_config, f)
        temp_path = f.name
    
    try:
        backup_manager = ConfigBackup(temp_path, max_backups=3)
        
        # Test backup creation
        success, result = backup_manager.create_backup(label="test")
        assert success, f"Backup creation failed: {result}"
        print(f"✓ Backup created: {Path(result).name}")
        
        # Test backup listing
        backups = backup_manager.list_backups()
        assert len(backups) > 0, "Should have at least one backup"
        print(f"✓ Backups listed: {len(backups)} found")
        
        # Test backup info
        backup_name = backups[0][0]
        info = backup_manager.get_backup_info(backup_name)
        assert info is not None, "Should get backup info"
        assert 'name' in info, "Info should contain 'name'"
        assert 'size' in info, "Info should contain 'size'"
        print(f"✓ Backup info retrieved: {info['name']}")
        
        # Test restore
        success, message = backup_manager.restore_backup(backup_name, create_backup_before=False)
        assert success, f"Restore failed: {message}"
        print(f"✓ Backup restored: {message}")
        
        # Test auto backup
        auto_backup = AutoBackup(temp_path, interval_minutes=0)
        assert auto_backup.should_backup(), "Should need backup initially"
        success = auto_backup.backup_if_needed()
        assert success, "Auto backup should succeed"
        print("✓ Auto backup working")
        
        print("✅ Backup System: ALL TESTS PASSED")
        return True
        
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        # Cleanup backup directory
        backup_dir = Path(temp_path).parent / ".config_backups"
        if backup_dir.exists():
            import shutil
            shutil.rmtree(backup_dir)


def test_security():
    """Test Phase 7.6: Security"""
    print("\n=== Testing Security System ===")
    
    # Test encryption/decryption
    original = "my_secret_password"
    encrypted = ConfigSecurity.encrypt_value(original)
    assert encrypted.startswith("ENC:"), "Encrypted value should have ENC: prefix"
    print(f"✓ Encryption: {original} -> {encrypted[:20]}...")
    
    decrypted = ConfigSecurity.decrypt_value(encrypted)
    assert decrypted == original, f"Decryption failed: expected '{original}', got '{decrypted}'"
    print(f"✓ Decryption: {encrypted[:20]}... -> {decrypted}")
    
    # Test is_encrypted
    assert ConfigSecurity.is_encrypted(encrypted), "Should detect encrypted value"
    assert not ConfigSecurity.is_encrypted(original), "Should not detect plain value as encrypted"
    print("✓ Encryption detection working")
    
    # Test credential encryption
    creds = {
        'username': 'testuser',
        'password': 'testpass',
        'user_id': 'user123',
        'place_id': 'place456'
    }
    
    encrypted_creds = ConfigSecurity.encrypt_credentials(creds)
    assert ConfigSecurity.is_encrypted(encrypted_creds['password']), "Password should be encrypted"
    assert ConfigSecurity.is_encrypted(encrypted_creds['username']), "Username should be encrypted"
    print("✓ Credential encryption working")
    
    decrypted_creds = ConfigSecurity.decrypt_credentials(encrypted_creds)
    assert decrypted_creds['password'] == 'testpass', "Password should decrypt correctly"
    assert decrypted_creds['username'] == 'testuser', "Username should decrypt correctly"
    print("✓ Credential decryption working")
    
    # Test masking
    masked = ConfigSecurity.mask_sensitive_value("password123", show_chars=3)
    assert masked == "pas********", f"Expected 'pas********', got '{masked}'"
    print(f"✓ Value masking: password123 -> {masked}")
    
    # Test safe config for display
    config = {
        'credentials': {
            'username': 'testuser',
            'password': 'secret123',
            'user_id': 'user123',
            'place_id': 'place456'
        }
    }
    
    safe_config = ConfigSecurity.get_safe_config_for_display(config)
    assert '*' in safe_config['credentials']['password'], "Password should be masked"
    print("✓ Safe config for display working")
    
    print("✅ Security System: ALL TESTS PASSED")
    return True


def test_integration():
    """Test full integration of all components"""
    print("\n=== Testing Full Integration ===")
    
    # Create temp config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_config = {
            "agent_name": "Integration Test",
            "cache_directory": "./test_cache",
            "ui_settings": {"theme": "auto", "font_size": 20},
            "automation": {"refresh_interval": 5},
            "accessibility": {"high_contrast": False},
            "advanced": {"debug_mode": False, "log_level": "INFO"},
            "credentials": {"username": "user", "password": "pass"}
        }
        json.dump(test_config, f)
        temp_path = f.name
    
    try:
        # 1. Load with manager
        manager = ConfigManager()
        assert manager.load(temp_path), "Manager should load config"
        print("✓ Manager loaded config")
        
        # 2. Create backup
        backup = ConfigBackup(temp_path)
        success, _ = backup.create_backup(label="integration")
        assert success, "Should create backup"
        print("✓ Backup created")
        
        # 3. Modify config
        manager.set('ui_settings.theme', 'dark', save_immediately=True)
        print("✓ Config modified and saved")
        
        # 4. Encrypt credentials
        creds = manager.get_section('credentials')
        encrypted_creds = ConfigSecurity.encrypt_credentials(creds)
        manager.update_section('credentials', encrypted_creds, save_immediately=True)
        print("✓ Credentials encrypted")
        
        # 5. Verify encrypted storage
        with open(temp_path, 'r') as f:
            stored_config = json.load(f)
        assert ConfigSecurity.is_encrypted(stored_config['credentials']['password']), \
            "Password should be encrypted in storage"
        print("✓ Verified encrypted storage")
        
        # 6. Decrypt and verify
        decrypted_creds = ConfigSecurity.decrypt_credentials(
            manager.get_section('credentials')
        )
        assert decrypted_creds['password'] == 'pass', "Password should decrypt correctly"
        print("✓ Decryption verified")
        
        print("✅ Full Integration: ALL TESTS PASSED")
        return True
        
    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        backup_dir = Path(temp_path).parent / ".config_backups"
        if backup_dir.exists():
            import shutil
            shutil.rmtree(backup_dir)


def run_all_tests():
    """Run all Phase 7 tests"""
    print("=" * 60)
    print("PHASE 7 CONFIGURATION SYSTEM - COMPLETE TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Configuration Manager", test_config_manager),
        ("Migration System", test_migrator),
        ("Backup System", test_backup),
        ("Security System", test_security),
        ("Full Integration", test_integration),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ {name}: FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {name}: EXCEPTION - {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 ALL PHASE 7 TESTS PASSED! 🎉")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

# Made with Bob
