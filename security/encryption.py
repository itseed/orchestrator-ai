"""
Data Encryption
TLS/SSL and data encryption utilities
"""

from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
from monitoring import get_logger
from config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class DataEncryption:
    """Data encryption at rest"""
    
    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize data encryption
        
        Args:
            key: Optional encryption key (generates new if not provided)
        """
        if key:
            self.key = key
        else:
            # Generate key from secret or create new
            secret_key = settings.SECRET_KEY or "default-secret-key-change-in-production"
            self.key = self._derive_key(secret_key)
        
        self.cipher = Fernet(self.key)
        logger.info("DataEncryption initialized")
    
    def _derive_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """Derive encryption key from password"""
        if salt is None:
            salt = b'orchestrator_salt_'  # Should be stored securely in production
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt string data
        
        Args:
            data: String data to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt string data
        
        Args:
            encrypted_data: Encrypted string (base64 encoded)
            
        Returns:
            Decrypted string
        """
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error("Decryption failed", error=str(e))
            raise ValueError("Failed to decrypt data") from e
    
    def encrypt_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt dictionary values
        
        Args:
            data: Dictionary to encrypt
            
        Returns:
            Dictionary with encrypted values
        """
        import json
        json_str = json.dumps(data)
        encrypted = self.encrypt(json_str)
        return {'encrypted': True, 'data': encrypted}
    
    def decrypt_dict(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt dictionary
        
        Args:
            encrypted_data: Encrypted dictionary
            
        Returns:
            Decrypted dictionary
        """
        import json
        if not encrypted_data.get('encrypted'):
            return encrypted_data
        
        decrypted_str = self.decrypt(encrypted_data['data'])
        return json.loads(decrypted_str)


class MessageEncryption:
    """Message encryption for inter-agent communication"""
    
    def __init__(self, encryption: Optional[DataEncryption] = None):
        """
        Initialize message encryption
        
        Args:
            encryption: Optional DataEncryption instance
        """
        self.encryption = encryption or DataEncryption()
        logger.info("MessageEncryption initialized")
    
    def encrypt_message(self, message: Dict[str, Any], fields: Optional[list] = None) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in message
        
        Args:
            message: Message dictionary
            fields: Optional list of fields to encrypt (encrypts all if not provided)
            
        Returns:
            Message with encrypted fields
        """
        if fields:
            encrypted_message = message.copy()
            for field in fields:
                if field in encrypted_message and isinstance(encrypted_message[field], str):
                    encrypted_message[field] = self.encryption.encrypt(encrypted_message[field])
            return encrypted_message
        else:
            # Encrypt entire payload
            return self.encryption.encrypt_dict(message)
    
    def decrypt_message(self, message: Dict[str, Any], fields: Optional[list] = None) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in message
        
        Args:
            message: Encrypted message dictionary
            fields: Optional list of fields to decrypt
            
        Returns:
            Decrypted message
        """
        if fields:
            decrypted_message = message.copy()
            for field in fields:
                if field in decrypted_message and isinstance(decrypted_message[field], str):
                    try:
                        decrypted_message[field] = self.encryption.decrypt(decrypted_message[field])
                    except Exception as e:
                        logger.warning("Failed to decrypt field", field=field, error=str(e))
            return decrypted_message
        else:
            # Decrypt entire payload
            if message.get('encrypted'):
                return self.encryption.decrypt_dict(message)
            return message

