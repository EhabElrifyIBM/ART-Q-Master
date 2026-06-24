"""
Configuration Security - Phase 7.6
Basic encryption for sensitive configuration data (credentials).
Uses base64 encoding for now - can be enhanced with proper encryption later.
"""

import base64
import json
from typing import Dict, Any, Optional


class ConfigSecurity:
    """
    Handles encryption/decryption of sensitive configuration data.
    Currently uses base64 encoding - can be upgraded to proper encryption.
    """
    
    # Simple obfuscation key (can be replaced with proper key management)
    _OBFUSCATION_KEY = b"ART_Q_MASTER_V2_CONFIG_KEY_2024"
    
    @staticmethod
    def _xor_bytes(data: bytes, key: bytes) -> bytes:
        """Simple XOR encryption/decryption."""
        key_len = len(key)
        return bytes(b ^ key[i % key_len] for i, b in enumerate(data))
    
    @staticmethod
    def encrypt_value(value: str) -> str:
        """
        Encrypt a string value.
        
        Args:
            value: Plain text value
            
        Returns:
            Encrypted value (base64 encoded)
        """
        try:
            if not value:
                return ""
            
            # Convert to bytes
            value_bytes = value.encode('utf-8')
            
            # XOR with key
            encrypted = ConfigSecurity._xor_bytes(value_bytes, ConfigSecurity._OBFUSCATION_KEY)
            
            # Base64 encode
            encoded = base64.b64encode(encrypted).decode('utf-8')
            
            # Add prefix to identify encrypted values
            return f"ENC:{encoded}"
            
        except Exception as e:
            print(f"Encryption error: {e}")
            return value
    
    @staticmethod
    def decrypt_value(encrypted_value: str) -> str:
        """
        Decrypt an encrypted value.
        
        Args:
            encrypted_value: Encrypted value (with ENC: prefix)
            
        Returns:
            Decrypted plain text value
        """
        try:
            if not encrypted_value:
                return ""
            
            # Check if value is encrypted
            if not encrypted_value.startswith("ENC:"):
                return encrypted_value  # Not encrypted, return as-is
            
            # Remove prefix
            encoded = encrypted_value[4:]
            
            # Base64 decode
            encrypted = base64.b64decode(encoded.encode('utf-8'))
            
            # XOR with key
            decrypted = ConfigSecurity._xor_bytes(encrypted, ConfigSecurity._OBFUSCATION_KEY)
            
            # Convert to string
            return decrypted.decode('utf-8')
            
        except Exception as e:
            print(f"Decryption error: {e}")
            return encrypted_value
    
    @staticmethod
    def is_encrypted(value: str) -> bool:
        """
        Check if a value is encrypted.
        
        Args:
            value: Value to check
            
        Returns:
            True if encrypted, False otherwise
        """
        return isinstance(value, str) and value.startswith("ENC:")
    
    @staticmethod
    def encrypt_credentials(credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt all credential fields.
        
        Args:
            credentials: Credentials dictionary
            
        Returns:
            Dictionary with encrypted values
        """
        encrypted = credentials.copy()
        
        # Fields to encrypt
        sensitive_fields = ['password', 'username', 'user_id', 'place_id']
        
        for field in sensitive_fields:
            if field in encrypted and encrypted[field]:
                if not ConfigSecurity.is_encrypted(encrypted[field]):
                    encrypted[field] = ConfigSecurity.encrypt_value(encrypted[field])
        
        return encrypted
    
    @staticmethod
    def decrypt_credentials(credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt all credential fields.
        
        Args:
            credentials: Credentials dictionary with encrypted values
            
        Returns:
            Dictionary with decrypted values
        """
        decrypted = credentials.copy()
        
        # Fields to decrypt
        sensitive_fields = ['password', 'username', 'user_id', 'place_id']
        
        for field in sensitive_fields:
            if field in decrypted and decrypted[field]:
                if ConfigSecurity.is_encrypted(decrypted[field]):
                    decrypted[field] = ConfigSecurity.decrypt_value(decrypted[field])
        
        return decrypted
    
    @staticmethod
    def secure_config_for_storage(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare configuration for secure storage (encrypt sensitive data).
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration with encrypted sensitive data
        """
        secured = config.copy()
        
        # Encrypt credentials section
        if 'credentials' in secured:
            secured['credentials'] = ConfigSecurity.encrypt_credentials(secured['credentials'])
        
        return secured
    
    @staticmethod
    def secure_config_for_use(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare configuration for use (decrypt sensitive data).
        
        Args:
            config: Configuration dictionary with encrypted data
            
        Returns:
            Configuration with decrypted sensitive data
        """
        usable = config.copy()
        
        # Decrypt credentials section
        if 'credentials' in usable:
            usable['credentials'] = ConfigSecurity.decrypt_credentials(usable['credentials'])
        
        return usable
    
    @staticmethod
    def mask_sensitive_value(value: str, show_chars: int = 3) -> str:
        """
        Mask a sensitive value for display.
        
        Args:
            value: Value to mask
            show_chars: Number of characters to show at start
            
        Returns:
            Masked value (e.g., "abc***")
        """
        if not value:
            return ""
        
        if len(value) <= show_chars:
            return "*" * len(value)
        
        return value[:show_chars] + "*" * (len(value) - show_chars)
    
    @staticmethod
    def get_safe_config_for_display(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get configuration safe for display (masked sensitive values).
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Configuration with masked sensitive values
        """
        safe = json.loads(json.dumps(config))  # Deep copy
        
        # Mask credentials
        if 'credentials' in safe:
            creds = safe['credentials']
            if 'password' in creds:
                creds['password'] = ConfigSecurity.mask_sensitive_value(creds['password'], 0)
            if 'username' in creds:
                creds['username'] = ConfigSecurity.mask_sensitive_value(creds['username'], 3)
            if 'user_id' in creds:
                creds['user_id'] = ConfigSecurity.mask_sensitive_value(creds['user_id'], 3)
            if 'place_id' in creds:
                creds['place_id'] = ConfigSecurity.mask_sensitive_value(creds['place_id'], 3)
        
        return safe


# Convenience functions
def encrypt_password(password: str) -> str:
    """Encrypt a password."""
    return ConfigSecurity.encrypt_value(password)


def decrypt_password(encrypted_password: str) -> str:
    """Decrypt a password."""
    return ConfigSecurity.decrypt_value(encrypted_password)


def is_password_encrypted(password: str) -> bool:
    """Check if password is encrypted."""
    return ConfigSecurity.is_encrypted(password)

# Made with Bob
