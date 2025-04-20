import base64
import os
import sys
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

class EncryptionService:
    """Service to handle encryption and decryption of sensitive data"""
    
    def __init__(self, key_file_path="config/encryption.key", use_env_key=True):
        """
        Initialize Encryption Service
        
        Args:
            key_file_path: Path to store the encryption key
            use_env_key: Whether to use key from environment variable
        """
        self.key_file_path = key_file_path
        self.key = self._get_or_create_key(use_env_key)
        self.fernet = Fernet(self.key)
    
    def _get_or_create_key(self, use_env_key):
        """Get existing key or create a new one"""
        # Try to get key from environment
        if use_env_key:
            env_key = os.environ.get("SECRET_KEY")
            if env_key:
                try:
                    # Make sure the key is valid by creating a Fernet instance
                    Fernet(env_key)
                    logger.info("Using encryption key from environment variable")
                    return env_key
                except Exception as e:
                    logger.error(f"Invalid encryption key from environment: {str(e)}")
        
        # Try to load key from file
        key_dir = os.path.dirname(self.key_file_path)
        if not os.path.exists(key_dir):
            os.makedirs(key_dir)
            
        if os.path.exists(self.key_file_path):
            try:
                with open(self.key_file_path, 'rb') as f:
                    key = f.read()
                # Validate key by creating a Fernet instance
                Fernet(key)
                logger.info(f"Loaded encryption key from {self.key_file_path}")
                return key
            except Exception as e:
                logger.error(f"Error loading encryption key: {str(e)}")
        
        # Generate a new key
        logger.info("Generating new encryption key")
        key = Fernet.generate_key()
        
        # Save the key to file
        try:
            with open(self.key_file_path, 'wb') as f:
                f.write(key)
            logger.info(f"Saved encryption key to {self.key_file_path}")
        except Exception as e:
            logger.error(f"Error saving encryption key: {str(e)}")
        
        return key
    
    def encrypt(self, data):
        """
        Encrypt a string
        
        Args:
            data: String to encrypt
            
        Returns:
            Encrypted string in base64 format prefixed with 'encrypted:'
        """
        if not data:
            return data
            
        try:
            # Check if data is already encrypted
            if isinstance(data, str) and data.startswith('encrypted:'):
                return data
                
            # Convert to bytes if string
            if isinstance(data, str):
                data = data.encode('utf-8')
                
            # Encrypt the data
            encrypted_data = self.fernet.encrypt(data)
            
            # Return as base64 string with prefix
            return f"encrypted:{encrypted_data.decode('utf-8')}"
        except Exception as e:
            logger.error(f"Error encrypting data: {str(e)}")
            # Return original data on error
            return data
    
    def decrypt(self, data):
        """
        Decrypt a string
        
        Args:
            data: Encrypted string in base64 format with 'encrypted:' prefix
            
        Returns:
            Decrypted string
        """
        if not data:
            return data
            
        try:
            # Check if data is encrypted
            if not isinstance(data, str) or not data.startswith('encrypted:'):
                return data
                
            # Remove prefix
            encrypted_data = data[len('encrypted:'):]
            
            # Decrypt the data
            decrypted_data = self.fernet.decrypt(encrypted_data.encode('utf-8'))
            
            # Return as string
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Error decrypting data: {str(e)}")
            # Return original data on error (without prefix)
            if isinstance(data, str) and data.startswith('encrypted:'):
                return data[len('encrypted:'):]
            return data