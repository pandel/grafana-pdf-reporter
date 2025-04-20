import os
import sys
import json
import bcrypt
import logging
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

class AuthService:
    """Service to handle authentication and user management"""
    
    def __init__(self, users_dir: str = "config", users_file: str = "users.json"):
        """
        Initialize Auth Service
        
        Args:
            users_dir: Directory to store auth files
            users_file: Filename for user data
        """
        self.users_dir = users_dir
        self.users_file = users_file
        self.users_path = os.path.join(users_dir, users_file)

        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-me-in-production")
        
        # Create auth directory if it doesn't exist
        if not os.path.exists(users_dir):
            logger.info(f"Creating auth directory: {users_dir}")
            os.makedirs(users_dir, exist_ok=True)

    
    def is_first_time_setup(self) -> bool:
        """
        Check if this is the first time setup (no users exist)
        
        Returns:
            True if no users exist, False otherwise
        """
        try:
            # Prüfen, ob die Datei existiert
            if not os.path.exists(self.users_path):
                logger.info(f"Users file {self.users_path} does not exist, setup needed")
                return True
                
            # Prüfen, ob die Datei leer ist
            if os.path.getsize(self.users_path) == 0:
                logger.info(f"Users file {self.users_path} is empty, setup needed")
                return True
                
            # Prüfen, ob die Datei gültiges JSON enthält
            with open(self.users_path, 'r') as f:
                users = json.load(f)
                
            # Prüfen, ob Benutzer vorhanden sind
            if not users:
                logger.info("No users found in users file, setup needed")
                return True
                
            logger.debug(f"Found {len(users)} users, no setup needed")
            return False
        except json.JSONDecodeError:
            logger.warning(f"Users file {self.users_path} contains invalid JSON, setup needed")
            return True
        except Exception as e:
            logger.error(f"Error checking setup status: {str(e)}")
            # Bei anderen Fehlern (z.B. Berechtigungsproblemen) gehen wir davon aus, 
            # dass Setup benötigt wird
            return True
    
    def create_user(self, username: str, password: str, is_admin: bool = True, auth_type: str = "internal") -> bool:
        """
        Create a new user
        
        Args:
            username: Username
            password: Plain text password
            is_admin: Whether the user is an admin
            auth_type: Authentication type (internal, LDAP)
            
        Returns:
            True if successful, False otherwise
        """
        logger.debug(f"Creating user with auth_type: {auth_type}")
        try:
            # Hash the password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Load existing users or create empty dict
            users = {}
            if os.path.exists(self.users_path):
                try:
                    with open(self.users_path, 'r') as f:
                        file_content = f.read().strip()
                        if file_content:  # Only try to parse if file has content
                            users = json.loads(file_content)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in {self.users_path}, starting with empty user list")
                    # Continue with empty users dict
            
            # Check if this is the first user (empty users dict)
            is_first_user = len(users) == 0
            
            # Add new user
            users[username] = {
                "password": hashed_password,
                "is_admin": is_admin,
                "auth_type": auth_type,
                "created": datetime.now().isoformat()
            }
            
            # Set display_name to "ReportAdmin" for the first user
            if is_first_user:
                users[username]["display_name"] = "ReportAdmin"
            
            # Check if directory is writable
            if not os.access(os.path.dirname(self.users_path), os.W_OK):
                logger.error(f"No write permission for directory: {os.path.dirname(self.users_path)}")
                return False
            
            # Save users
            with open(self.users_path, 'w') as f:
                json.dump(users, f, indent=2)
                f.flush()  # Ensure data is written to disk
                os.fsync(f.fileno())  # Force write to physical media
            
            # Verify file was created
            if not os.path.exists(self.users_path):
                logger.error(f"Failed to create users file: {self.users_path}")
                return False
                
            logger.info(f"User {username} created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}", exc_info=True)  # Include traceback
            return False
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific user by username
        
        Args:
            username: Username to get
            
        Returns:
            User information (excluding password) or None if not found
        """
        if not os.path.exists(self.users_path):
            return None
        
        try:
            with open(self.users_path, 'r') as f:
                users = json.load(f)
            
            if username not in users:
                return None
            
            # Return user info without password
            user_info = {
                "username": username,
                "is_admin": users[username].get("is_admin", False),
                "created": users[username].get("created", ""),
                "display_name": users[username].get("display_name", username),
                "auth_type": users[username].get("auth_type", "internal")
            }
            return user_info
        except Exception as e:
            logger.error(f"Error getting user {username}: {str(e)}")
            return None

    def update_user(self, username: str, user_data: Dict[str, Any], admin_user: str) -> bool:
        """
        Update an existing user
        
        Args:
            username: Username to update
            user_data: New user data
            admin_user: Username of the admin making the change
            
        Returns:
            True if successful, False if user not found or not authorized
        """
        if not os.path.exists(self.users_path):
            return False
        
        try:
            with open(self.users_path, 'r') as f:
                users = json.load(f)
            
            if username not in users:
                return False
            
            # Check if this is the last admin
            if users[username].get("is_admin", False) and not user_data.get("is_admin", False):
                # Count admins
                admin_count = sum(1 for user in users.values() if user.get("is_admin", False))
                if admin_count <= 1:
                    logger.warning(f"Cannot remove admin status from last admin user: {username}")
                    return False
            
            # Update fields, preserving the password
            current_password = users[username]["password"]
            
            # Only update allowed fields
            users[username]["is_admin"] = user_data.get("is_admin", users[username].get("is_admin", False))
            users[username]["display_name"] = user_data.get("display_name", users[username].get("display_name", username))
            users[username]["auth_type"] = user_data.get("auth_type", users[username].get("auth_type", "internal"))

            # Password only changes if provided
            if "password" in user_data and user_data["password"]:
                users[username]["password"] = bcrypt.hashpw(
                    user_data["password"].encode('utf-8'), 
                    bcrypt.gensalt()
                ).decode('utf-8')
            else:
                users[username]["password"] = current_password
            
            # Add modification info
            users[username]["modified"] = datetime.now().isoformat()
            users[username]["modified_by"] = admin_user
            
            with open(self.users_path, 'w') as f:
                json.dump(users, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error updating user {username}: {str(e)}")
            return False

    def delete_user(self, username: str, admin_user: str) -> bool:
        """
        Delete a user
        
        Args:
            username: Username to delete
            admin_user: Username of the admin making the change
            
        Returns:
            True if successful, False if user not found or not authorized
        """
        if not os.path.exists(self.users_path):
            return False
        
        try:
            with open(self.users_path, 'r') as f:
                users = json.load(f)
            
            if username not in users:
                return False
            
            # Prevent deleting self
            if username == admin_user:
                logger.warning(f"User {admin_user} attempted to delete their own account")
                return False
            
            # Check if this is the last admin
            if users[username].get("is_admin", False):
                # Count admins
                admin_count = sum(1 for user in users.values() if user.get("is_admin", False))
                if admin_count <= 1:
                    logger.warning(f"Cannot delete last admin user: {username}")
                    return False
            
            # Delete the user
            del users[username]
            
            with open(self.users_path, 'w') as f:
                json.dump(users, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error deleting user {username}: {str(e)}")
            return False

    def is_user_admin(self, username: str) -> bool:
        """
        Check if a user is an admin
        
        Args:
            username: Username to check
            
        Returns:
            True if user is an admin, False otherwise
        """
        user_info = self.get_user(username)
        if not user_info:
            return False
        
        return user_info.get("is_admin", False)

    def count_admins(self) -> int:
        """
        Count the number of admin users
        
        Returns:
            Number of admin users
        """
        try:
            with open(self.users_path, 'r') as f:
                users = json.load(f)
            
            return sum(1 for user in users.values() if user.get("is_admin", False))
        except Exception as e:
            logger.error(f"Error counting admin users: {str(e)}")
            return 0

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            User info if successful, None otherwise
        """
        if not os.path.exists(self.users_path):
            logger.warning("No users file exists, authentication failed")
            return None
        
        try:
            # Load users
            with open(self.users_path, 'r') as f:
                users = json.load(f)
            
            # Check if user exists
            if username not in users:
                logger.warning(f"User {username} not found")
                return None
            
            user_data = users[username]
            auth_type = user_data.get("auth_type", "internal")
            
            # Check if user should authenticate via LDAP
            if auth_type.lower() == "ldap":
                # Import here to avoid circular imports
                from api.api_controller import settings_service
                
                # Get LDAP settings
                ldap_settings = settings_service.get_decrypted_settings().get("ldap", {})
                ldap_enabled = ldap_settings.get("enabled", False)
                
                if ldap_enabled:
                    # Try LDAP authentication first
                    try:
                        import ldap
                        
                        # Get LDAP connection settings
                        ldap_server = ldap_settings.get("server", "")
                        ldap_port = ldap_settings.get("port", 389)
                        bind_dn = ldap_settings.get("bindDN", "")
                        bind_password = ldap_settings.get("bindPassword", "")
                        search_base = ldap_settings.get("searchBase", "")
                        search_filter = ldap_settings.get("searchFilter", "(uid=%u)")
                        use_tls = ldap_settings.get("tlsEnabled", False)
                        use_ssl = ldap_settings.get("useSSL", False)
                        verify_cert = ldap_settings.get("verifyCertLDAP", False)
                        
                        if not ldap_server or not search_base:
                            logger.warning("LDAP is enabled but missing required settings")
                            # Fall back to regular password check
                        else:
                            # Replace placeholders in search filter
                            search_filter = search_filter.replace("%u", username)
                            
                            # Connect to LDAP server
                            server_uri = f"ldap{'s' if use_ssl else ''}://{ldap_server}:{ldap_port}"
                            logger.debug(f"Connecting to LDAP server: {server_uri}")

                            # Set connection options
                            # ldap.set_option(ldap.OPT_DEBUG_LEVEL, 255)
                            ldap.set_option(ldap.OPT_REFERRALS, 0)
                            ldap.set_option(ldap.OPT_PROTOCOL_VERSION, 3)

                            if not verify_cert:
                                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
                                ldap.set_option(ldap.OPT_X_TLS_NEWCTX, 0)

                            ldap_conn = ldap.initialize(server_uri)
                                                    
                            if use_tls:
                                ldap_conn.start_tls_s()
                            
                            # Bind with admin credentials to search for user
                            if bind_dn and bind_password:
                                logger.debug(f"Binding to LDAP server with DN: {bind_dn}")
                                ldap_conn.simple_bind_s(bind_dn, bind_password)
                                
                                # Search for user
                                logger.debug(f"Searching for user with filter: {search_filter}, base: {search_base}")
                                result = ldap_conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter, ['dn'])
                                
                                if result:
                                    user_dn = result[0][0]
                                    # Try to bind with user credentials
                                    try:
                                        ldap_conn.simple_bind_s(user_dn, password)
                                        logger.info(f"User {username} authenticated successfully via LDAP")
                                        
                                        # Return user info (excluding password)
                                        user_info = {
                                            "username": username,
                                            "is_admin": user_data.get("is_admin", False),
                                            "created": user_data.get("created", ""),
                                            "display_name": user_data.get("display_name", username)
                                        }
                                        return user_info
                                    except ldap.INVALID_CREDENTIALS:
                                        logger.warning(f"Invalid LDAP password for user {username}")
                                        return None
                                else:
                                    logger.warning(f"User {username} not found in LDAP")
                                    return None
                            else:
                                logger.warning("Missing bind credentials for LDAP")
                                # Fall back to regular password check
                    except (ImportError, Exception) as e:
                        if isinstance(e, ImportError):
                            logger.error("Python-LDAP module not installed")
                        else:
                            logger.error(f"LDAP authentication error: {str(e)}")
                        
                        # Only fall back to regular password check if LDAP server is unreachable
                        if isinstance(e, ldap.SERVER_DOWN):
                            logger.warning("LDAP server is unreachable, falling back to local authentication")
                        else:
                            # For other LDAP errors (invalid credentials, user not found), don't fall back
                            return None
                else:
                    logger.debug(f"LDAP authentication for user {username} requested but LDAP is not enabled")
                    # Fall back to regular password check
            
            # Regular password check (for non-LDAP users or as fallback if specified above)
            stored_password = user_data["password"]
            if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                # Return user info (excluding password)
                user_info = {
                    "username": username,
                    "is_admin": user_data.get("is_admin", False),
                    "created": user_data.get("created", ""),
                    "display_name": user_data.get("display_name", username)
                }
                logger.info(f"User {username} authenticated successfully")
                return user_info
            else:
                logger.warning(f"Invalid password for user {username}")
                return None
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            return None
    
    def generate_token(self, user_info: Dict[str, Any], expires_delta: timedelta = timedelta(hours=24)) -> str:
        """
        Generate JWT token for authenticated user
        
        Args:
            user_info: User information
            expires_delta: Token expiration time
            
        Returns:
            JWT token string
        """
        expire = datetime.utcnow() + expires_delta
        to_encode = {
            "sub": user_info["username"],
            "is_admin": user_info["is_admin"],
            "display_name": user_info["display_name"],
            "exp": expire
        }
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm="HS256")
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            User info if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            username = payload.get("sub")
            if username is None:
                logger.warning("Token missing username claim")
                return None
            
            # Return user info from token
            user_info = {
                "username": username,
                "is_admin": payload.get("is_admin", False),
                "display_name": payload.get("display_name", username)
            }
            return user_info
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return None
    
    def get_users(self) -> Dict[str, Any]:
        """
        Get all users (admin only)
        
        Returns:
            Dict of users (excluding passwords)
        """
        if not os.path.exists(self.users_path):
            return {}
        
        try:
            # Load users
            with open(self.users_path, 'r') as f:
                users = json.load(f)
            
            # Remove passwords
            sanitized_users = {}
            for username, user_data in users.items():
                sanitized_users[username] = {
                    "is_admin": user_data.get("is_admin", False),
                    "display_name": user_data.get("display_name", ""),
                    "created": user_data.get("created", ""),
                    "auth_type": user_data.get("auth_type", "internal")
                }
            
            return sanitized_users
        except Exception as e:
            logger.error(f"Error getting users: {str(e)}")
            return {}

    def change_password(self, username: str, new_password: str) -> bool:
        """
        Change the password of a user
        
        Args:
            username: Username of the user
            new_password: New password to set
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(self.users_path):
            logger.error(f"Users file not found: {self.users_path}")
            return False
        
        try:
            # Load users
            with open(self.users_path, 'r') as f:
                users = json.load(f)
            
            # Check if user exists
            if username not in users:
                logger.warning(f"User {username} not found")
                return False
            
            # Hash the new password
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Update password
            users[username]["password"] = hashed_password
            users[username]["modified"] = datetime.now().isoformat()
            
            # Save users
            with open(self.users_path, 'w') as f:
                json.dump(users, f, indent=2)
            
            logger.info(f"Password changed successfully for user: {username}")
            return True
        except Exception as e:
            logger.error(f"Error changing password for user {username}: {str(e)}")
            return False