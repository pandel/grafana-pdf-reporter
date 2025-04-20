#!/usr/bin/env python3

import secrets
import base64
import os
import argparse
from pathlib import Path

def generate_secret_key(length=32):
    """
    Generate a cryptographically secure random key.
    
    Args:
        length: Length of the key in bytes
        
    Returns:
        Base64 encoded random key
    """
    random_bytes = secrets.token_bytes(length)
    return base64.urlsafe_b64encode(random_bytes).decode('utf-8')

def update_env_file(key, env_file='.env'):
    """
    Update or create .env file with the new secret key.
    
    Args:
        key: The generated secret key
        env_file: Path to the .env file
    """
    env_path = Path(env_file)
    
    if env_path.exists():
        # Read existing content
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Check if SECRET_KEY is already defined
        secret_key_exists = False
        new_lines = []
        
        for line in lines:
            if line.startswith('SECRET_KEY='):
                new_lines.append(f'SECRET_KEY={key}\n')
                secret_key_exists = True
            else:
                new_lines.append(line)
        
        # Add SECRET_KEY if it doesn't exist
        if not secret_key_exists:
            new_lines.append(f'SECRET_KEY={key}\n')
        
        # Write back to file
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
    else:
        # Create new .env file
        with open(env_path, 'w') as f:
            f.write(f'SECRET_KEY={key}\n')

def main():
    parser = argparse.ArgumentParser(description='Generate a secure secret key for Grafana PDF Reporter')
    parser.add_argument('--length', type=int, default=32, help='Length of the key in bytes')
    parser.add_argument('--env-file', default='.env', help='Path to the .env file')
    parser.add_argument('--update-env', action='store_true', help='Update the .env file with the key')
    args = parser.parse_args()
    
    try:
        key = generate_secret_key(args.length)
        print(f"\nGenerated new secret key: {key}\n")
        
        if args.update_env:
            update_env_file(key, args.env_file)
            print(f"Updated {args.env_file} with the new secret key.")
            print("Please restart the application for the changes to take effect.")
        else:
            print("To use this key, add it to your environment variables or .env file:")
            print(f"SECRET_KEY={key}")
            
        print("\nNote: Changing the secret key will invalidate all existing:")
        print(" - JWT tokens (users will need to log in again)")
        print(" - Encrypted data (passwords in settings will need to be reset)")
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())