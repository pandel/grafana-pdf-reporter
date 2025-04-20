import os
import sys
import json
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from services.encryption_service import EncryptionService

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

class SettingsService:
    """Service to manage application settings"""
    
    def __init__(self, settings_dir: str = "config", settings_file: str = "settings.json"):
        """
        Initialize Settings Service
        
        Args:
            settings_dir: Directory to store settings file
            settings_file: Filename for settings storage
        """
        self.settings_dir = settings_dir
        self.settings_file = settings_file
        self.settings_path = os.path.join(settings_dir, settings_file)
        
        # Create encryption service
        self.encryption_service = EncryptionService()
        
        # Create settings directory if it doesn't exist
        if not os.path.exists(settings_dir):
            logger.info(f"Creating settings directory: {settings_dir}")
            os.makedirs(settings_dir)
            
    def get_settings(self) -> Dict[str, Any]:
        """
        Get current application settings
        
        Returns:
            Dict with all settings, with passwords still encrypted
        """
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r') as f:
                    return json.load(f)
            else:
                # If file doesn't exist, create and return defaults
                logger.error(f"Settings file does not exit. First start.")
                return False
        except Exception as e:
            logger.error(f"Error reading settings: {str(e)}")
            return False

    def get_decrypted_settings(self) -> Dict[str, Any]:
        """
        Get current application settings with passwords decrypted
        
        Returns:
            Dict with all settings, with passwords decrypted
        """
        settings = self.get_settings()
        if not settings:
            logger.error(f"Could not get settings. First start?")
            return False
        
        # Decrypt passwords
        if "grafana" in settings and "password" in settings["grafana"]:
            settings["grafana"]["password"] = self.encryption_service.decrypt(settings["grafana"]["password"])
        
        # Decrypt passwords for all Grafana servers
        if "grafana_servers" in settings:
            for server in settings["grafana_servers"]:
                if "password" in server:
                    server["password"] = self.encryption_service.decrypt(server["password"])
        
        # Rest of the method remains unchanged for email and LDAP passwords
        if "email" in settings:
            if "password" in settings["email"]:
                settings["email"]["password"] = self.encryption_service.decrypt(settings["email"]["password"])
            if "clientSecret" in settings["email"]:
                settings["email"]["clientSecret"] = self.encryption_service.decrypt(settings["email"]["clientSecret"])
            if "proxyPassword" in settings["email"]:
                settings["email"]["proxyPassword"] = self.encryption_service.decrypt(settings["email"]["proxyPassword"])
        
        # Decrypt LDAP bind password
        if "ldap" in settings and "bindPassword" in settings["ldap"]:
            settings["ldap"]["bindPassword"] = self.encryption_service.decrypt(settings["ldap"]["bindPassword"])
        
        return settings

    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Update application settings
        
        Args:
            settings: New settings to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure settings directory exists
            if not os.path.exists(self.settings_dir):
                os.makedirs(self.settings_dir)
            
            # Merge with existing settings to preserve any missing fields
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r') as f:
                    existing_settings = json.load(f)
                
                # Merge new settings with existing ones (deep merge)
                self._deep_merge(existing_settings, settings)
                settings_to_save = existing_settings
            else:
                settings_to_save = settings
            
        # Add last updated timestamp
            settings_to_save["last_updated"] = datetime.now().isoformat()

            # First save after creation of default
            if settings_to_save["status"] == "init":
                settings_to_save["status"] = "runcfg"
            
            # Encrypt passwords
            if "grafana" in settings_to_save and "password" in settings_to_save["grafana"]:
                settings_to_save["grafana"]["password"] = self.encryption_service.encrypt(
                    settings_to_save["grafana"]["password"]
                )
            
            # Encrypt passwords for all Grafana servers
            if "grafana_servers" in settings_to_save:
                for server in settings_to_save["grafana_servers"]:
                    if "password" in server:
                        server["password"] = self.encryption_service.encrypt(
                            server["password"]
                        )
            
            if "email" in settings_to_save:
                if "password" in settings_to_save["email"]:
                    settings_to_save["email"]["password"] = self.encryption_service.encrypt(
                        settings_to_save["email"]["password"]
                    )
                if "clientSecret" in settings_to_save["email"]:
                    settings_to_save["email"]["clientSecret"] = self.encryption_service.encrypt(
                        settings_to_save["email"]["clientSecret"]
                    )
                if "proxyPassword" in settings_to_save["email"]:
                    settings_to_save["email"]["proxyPassword"] = self.encryption_service.encrypt(
                        settings_to_save["email"]["proxyPassword"]
                    )
            
            # Encrypt LDAP bind password
            if "ldap" in settings_to_save and "bindPassword" in settings_to_save["ldap"]:
                settings_to_save["ldap"]["bindPassword"] = self.encryption_service.encrypt(
                    settings_to_save["ldap"]["bindPassword"]
                )
            
            # Save to file
            with open(self.settings_path, 'w') as f:
                json.dump(settings_to_save, f, indent=2)
            
            logger.info("Settings updated successfully")
            return True
        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            return False
    
    def _create_default_settings(self) -> Dict[str, Any]:
        """
        Create default settings file and return default settings
        
        Returns:
            Dict with default settings
        """
        if "GRAFANA_URL" not in os.environ or "GRAFANA_USERNAME" not in os.environ or "GRAFANA_PASSWORD" not in os.environ:
            stat = "init"
        else:
            stat = "runcfg"

        # Create a unique ID for the default server
        default_server_id = str(uuid.uuid4())

        default_settings = {
            "general": {
                "defaultLanguage": "de",
                "defaultTheme": "dark",
                "defaultTemplate": "default",
                "defaultServerId": default_server_id  # Add reference to default server
            },
            "grafana_servers": [
                {
                    "id": default_server_id,
                    "name": "Default Server",
                    "url": "http://localhost:3000",
                    "username": "admin",
                    "password": self.encryption_service.encrypt("admin"),
                    "is_default": True
                }
            ],
            "grafana_selectors": [
                {
                    "version": "9.",
                    "selector": "data-testid Panel header"
                },
                {
                    "version": "11.",
                    "selector": "data-testid panel content"
                }
            ],
            # Keep the legacy "grafana" field for backward compatibility
            "grafana": {
                "url": "LEGACY - NOT IN USE",
                "username": "LEGACY - NOT IN USE",
                "password": "LEGACY - NOT IN USE"
            },
            "email": {
                "server": os.getenv("SMTP_SERVER", ""),
                "port": int(os.getenv("SMTP_PORT", "587")),
                "username": os.getenv("SMTP_USER", ""),
                "password": self.encryption_service.encrypt(os.getenv("SMTP_PASSWORD", "")),
                "sender": os.getenv("SMTP_SENDER", ""),
                "useTLS": os.getenv("SMTP_USE_TLS", "True").lower() in ("true", "1", "t"),
                # Graph API settings
                "useGraphAPI": False,
                "clientId": "",
                "clientSecret": self.encryption_service.encrypt(""),
                "tenantId": "",
                "userEmail": "",
                "useProxy": False,
                "proxyUrl": "",
                "proxyPort": 8080,
                "proxyUser": "",
                "proxyPassword": self.encryption_service.encrypt("")
            },
            "ldap": {
                "enabled": False,
                "server": "",
                "port": 389,
                "bindDN": "",
                "bindPassword": self.encryption_service.encrypt(""),
                "searchBase": "",
                "searchFilter": "(uid=%u)",
                "tlsEnabled": False,
                "useSSL": False,
                "verifyCertLDAP": True,
                "groupSearchBase": "",
                "groupSearchFilter": "(member=%D)",
                "groupRoleAttribute": "cn",
                "adminGroupName": "grafana-admins"
            },
            "last_updated": datetime.now().isoformat(),
            "status": stat
        }
        
        try:
            with open(self.settings_path, 'w') as f:
                json.dump(default_settings, f, indent=2)
            logger.info(f"Default settings created at {self.settings_path}")
        except Exception as e:
            logger.error(f"Error creating default settings: {str(e)}")
        
        # Return decrypted version
        decrypted_settings = default_settings.copy()
        if "grafana" in decrypted_settings and "password" in decrypted_settings["grafana"]:
            decrypted_settings["grafana"]["password"] = self.encryption_service.decrypt(decrypted_settings["grafana"]["password"])
        
        if "email" in decrypted_settings:
            if "password" in decrypted_settings["email"]:
                decrypted_settings["email"]["password"] = self.encryption_service.decrypt(decrypted_settings["email"]["password"])
            if "clientSecret" in decrypted_settings["email"]:
                decrypted_settings["email"]["clientSecret"] = self.encryption_service.decrypt(decrypted_settings["email"]["clientSecret"])
            if "proxyPassword" in decrypted_settings["email"]:
                decrypted_settings["email"]["proxyPassword"] = self.encryption_service.decrypt(decrypted_settings["email"]["proxyPassword"])
        
        # Decrypt LDAP bind password in returned settings
        if "ldap" in decrypted_settings and "bindPassword" in decrypted_settings["ldap"]:
            decrypted_settings["ldap"]["bindPassword"] = self.encryption_service.decrypt(decrypted_settings["ldap"]["bindPassword"])
        
        return decrypted_settings
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Deep merge source dictionary into target dictionary
        
        Args:
            target: Target dictionary that will be modified
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target:
                if isinstance(target[key], dict) and isinstance(value, dict):
                    self._deep_merge(target[key], value)
                elif isinstance(target[key], list) and isinstance(value, list):
                    # For lists, replace the entire list
                    target[key] = value
                else:
                    target[key] = value
            else:
                target[key] = value
    
    def test_grafana_connection(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test Grafana connection with provided settings
        
        Args:
            settings: Grafana connection settings
            
        Returns:
            Dict with success status and message
        """
        from services.grafana_service import GrafanaService
        
        try:
            # Create temporary Grafana service instance with provided settings
            password = settings.get("password")
            
            # No need to decrypt, as input is coming directly from the frontend
            # and hasn't been encrypted yet
            
            temp_grafana_service = GrafanaService(
                base_url=settings.get("url"),
                grafana_username=settings.get("username"),
                grafana_password=password
            )
            
            # Test connection using the update_configuration method
            connection_success = temp_grafana_service.update_configuration(
                base_url=settings.get("url"),
                username=settings.get("username"),
                password=password
            )
            
            if connection_success:
                return {
                    "success": True,
                    "message": "Connection to Grafana successful"
                }
            else:
                return {
                    "success": False,
                    "message": "Could not connect to Grafana"
                }
        except Exception as e:
            logger.error(f"Error testing Grafana connection: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def test_email_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test email settings with provided configuration
        
        Args:
            settings: Email settings to test
            
        Returns:
            Dict with success status and message
        """
        # Check if using Graph API
        use_graph_api = settings.get("useGraphAPI", False)
        
        if use_graph_api:
            # Test Microsoft Graph API connection
            try:
                import requests
                import msal
                
                tenant_id = settings.get("tenantId", "")
                client_id = settings.get("clientId", "")
                client_secret = settings.get("clientSecret", "")
                user_email = settings.get("userEmail", "")

                # Get proxy settings
                use_proxy = settings.get("useProxy", False)
                proxy_url = settings.get("proxyUrl", "")
                proxy_port = settings.get("proxyPort", 8080)
                proxy_user = settings.get("proxyUser", "")
                proxy_password = settings.get("proxyPassword", "")
                verify_cert = settings.get("verifyCertGraphAPI", True)

                # Decrypt proxy password if it's encrypted
                if proxy_password and isinstance(proxy_password, str) and proxy_password.startswith("encrypted:"):
                    # Import here to avoid circular import
                    from services.encryption_service import EncryptionService
                    encryption_service = EncryptionService()
                    proxy_password = encryption_service.decrypt(proxy_password)

                if not tenant_id or not client_id or not client_secret or not user_email:
                    return {
                        "success": False,
                        "message": "Missing required Graph API settings"
                    }

                # Setup proxy configuration for MSAL
                # MSAL uses requests internally, so we need to prepare a proxies dict
                proxies = None
                if use_proxy and proxy_url:
                    proxy_auth = ""
                    if proxy_user and proxy_password:
                        proxy_auth = f"{proxy_user}:{proxy_password}@"
                    
                    proxy_scheme = "http"
                    if proxy_url.startswith("http://") or proxy_url.startswith("https://"):
                        proxy_scheme = proxy_url.split("://")[0]
                        proxy_url = proxy_url.split("://")[1]
                    
                    proxy_string = f"{proxy_scheme}://{proxy_auth}{proxy_url}:{proxy_port}"
                    proxies = {
                        "http": proxy_string,
                        "https": proxy_string
                    }
                    logger.info(f"Using proxy for Graph API: {proxy_scheme}://{proxy_url}:{proxy_port}")
                
                # Create MSAL app with proxy configuration
                # If using proxies and http_client is set, configure the session
                session=requests.Session()
                if not verify_cert:
                    logger.debug(" Do not verify certificate")
                    session.verify = False

                if proxies:
                    logger.debug("Proxy assigned to MSAL Client")
                    session.proxies = proxies
                                
                # Create MSAL app
                app = msal.ConfidentialClientApplication(
                    client_id=client_id,
                    client_credential=client_secret,
                    authority=f"https://login.microsoftonline.com/{tenant_id}",
                    http_client=session if proxies else None
                )
                
                # Get token
                scopes = ['https://graph.microsoft.com/.default']
                result = app.acquire_token_for_client(scopes=scopes)
                
                if "access_token" not in result:
                    return {
                        "success": False,
                        "message": f"Error getting token: {result.get('error_description', 'Unknown error')}"
                    }
                
                # Test Graph API access
                token = result["access_token"]
                headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                # Just check if we can access user info to verify permissions
                response = requests.get(
                    f'https://graph.microsoft.com/v1.0/users/{user_email}',
                    headers=headers
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "message": f"Error connecting to Graph API: {response.status_code} - {response.text}"
                    }
                
                return {
                    "success": True,
                    "message": "Microsoft Graph API connection successful"
                }
            except Exception as e:
                logger.error(f"Error testing Graph API settings: {str(e)}")
                return {
                    "success": False,
                    "message": str(e)
                }
        else:
            import smtplib
            from email.mime.text import MIMEText
            
            try:
                server = settings.get("server")
                port = int(settings.get("port", 587))
                username = settings.get("username")
                # No need to decrypt, as input is coming directly from the frontend
                # and hasn't been encrypted yet
                password = settings.get("password")
                sender = settings.get("sender") or username
                use_tls = settings.get("useTLS", True)
                
                if not server:
                    return {
                        "success": False,
                        "message": "SMTP server is required"
                    }
                
                # Create test connection
                with smtplib.SMTP(server, port) as smtp:
                    # Start TLS if required
                    if use_tls:
                        smtp.starttls()
                    
                    # Login if credentials provided
                    if username and password:
                        smtp.login(username, password)
                    
                    # Try to send test email to self (optional)
                    # Uncomment if you want to actually send a test email
                    # msg = MIMEText("This is a test email from Grafana PDF Reporter")
                    # msg['Subject'] = "Test Email"
                    # msg['From'] = sender
                    # msg['To'] = sender
                    # smtp.send_message(msg)
                    
                    # If we got here without errors, it's working
                    return {
                        "success": True,
                        "message": "Email settings test successful"
                    }
            except Exception as e:
                logger.error(f"Error testing email settings: {str(e)}")
                return {
                    "success": False,
                    "message": str(e)
                }

    def test_ldap_connection(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test LDAP connection with provided settings
        
        Args:
            settings: LDAP connection settings
            
        Returns:
            Dict with success status and message
        """
        try:
            import ldap
            
            # Extract LDAP settings
            server = settings.get("server", "")
            port = int(settings.get("port", 389))
            bind_dn = settings.get("bindDN", "")
            bind_password = settings.get("bindPassword", "")
            use_tls = settings.get("tlsEnabled", False)
            use_ssl = settings.get("useSSL", False)
            verify_cert = settings.get("verifyCertLDAP", False)
            
            if not server:
                return {
                    "success": False,
                    "message": "LDAP server is required"
                }
            
            # Connect to LDAP server
            server_uri = f"ldap{'s' if use_ssl else ''}://{server}:{port}"
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
            
            # Try binding with provided credentials
            if bind_dn and bind_password:
                ldap_conn.simple_bind_s(bind_dn, bind_password)
            else:
                # Anonymous bind if no credentials provided
                ldap_conn.simple_bind_s("", "")
            
            return {
                "success": True,
                "message": "Successfully connected to LDAP server"
            }
        except ImportError:
            logger.error("Python-LDAP module not installed")
            return {
                "success": False,
                "message": "LDAP module not installed on the server"
            }
        except ldap.SERVER_DOWN:
            logger.error(f"LDAP server is not reachable: {server}:{port}")
            return {
                "success": False,
                "message": f"Could not connect to LDAP server: {server}:{port}"
            }
        except ldap.INVALID_CREDENTIALS:
            logger.error("Invalid LDAP credentials")
            return {
                "success": False,
                "message": "Invalid LDAP credentials"
            }
        except Exception as e:
            logger.error(f"Error testing LDAP connection: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }
        
    def migrate_legacy_settings(self) -> bool:
        """
        Migrate legacy settings to new multi-server format
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current settings
            settings = self.get_settings()
            if not settings:
                logger.error("No settings to migrate")
                return False
            
            # Check if migration is needed
            if "grafana_servers" in settings:
                logger.info("Settings already in multi-server format, no migration needed")
                return True
            
            # Check if we have legacy Grafana settings
            if "grafana" not in settings:
                logger.error("No Grafana settings found for migration")
                return False
            
            # Create server ID for the legacy server
            server_id = str(uuid.uuid4())
            
            # Add it as default server ID to general settings
            if "general" not in settings:
                settings["general"] = {}
            settings["general"]["defaultServerId"] = server_id
            
            # Create server entry from legacy settings
            legacy_server = {
                "id": server_id,
                "name": "Default Server",
                "url": settings["grafana"].get("url", ""),
                "username": settings["grafana"].get("username", ""),
                "password": settings["grafana"].get("password", ""),
                "is_default": True
            }
            
            # Add to grafana_servers list
            settings["grafana_servers"] = [legacy_server]
            
            # Keep legacy grafana section for backward compatibility
            
            # Save migrated settings
            return self.update_settings(settings)
        
        except Exception as e:
            logger.error(f"Error migrating settings: {str(e)}")
            return False