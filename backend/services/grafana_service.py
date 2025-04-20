import os
import sys
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
from grafana_client import GrafanaApi

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

class GrafanaService:
    """Service to interact with Grafana API using python-grafana library"""
    
    def __init__(self, base_url: str = None, grafana_username: str = None, grafana_password: str = None):
        """
        Initialize Grafana service
        
        Args:
            base_url: Grafana server URL
            grafana_username: Grafana Username with admin privileges
            grafana_password: Grafana Password
        """
        # Instance variables for managing multiple connections
        self.connections = {}
        self.current_server_id = None
        self.grafana_url = base_url
        self.grafana_username = grafana_username
        self.grafana_password = grafana_password
        
        logger.debug(f"Initializing Grafana service")
        
        # If credentials are provided, create a default connection
        if base_url and grafana_username and grafana_password:
            self.add_connection("default", base_url, grafana_username, grafana_password)
            self.current_server_id = "default"
    
    def add_connection(self, server_id: str, base_url: str, username: str, password: str) -> bool:
        """
        Add a new Grafana server connection
        
        Args:
            server_id: Unique identifier for the server
            base_url: Grafana server URL
            username: Grafana username
            password: Grafana password
            
        Returns:
            True if connection was successfully added, False otherwise
        """
        logger.debug(f"Adding Grafana connection for server '{server_id}' at {base_url}")
        
        try:
            # Initialize according to documentation
            # https://github.com/grafana-toolbox/grafana-client
            client = GrafanaApi.from_url(
                url=base_url+'?verify=false',
                credential=(username, password)
            )
            
            # Store connection info
            self.connections[server_id] = {
                "client": client,
                "url": base_url,
                "username": username,
                "password": password
            }
            
            # Test the connection
            try:
                health = client.health.check()
                logger.info(f"Successfully connected to Grafana server '{server_id}'. Database status: {health.get('database', 'unknown')}")
                
                # Try to get the version
                try:
                    version = client.version
                    logger.debug(f"Grafana server '{server_id}' version: {version}")
                except Exception as version_error:
                    logger.warning(f"Could not retrieve Grafana version for server '{server_id}': {str(version_error)}")
                
                return True
            except Exception as test_error:
                logger.error(f"Failed to connect to Grafana server '{server_id}': {str(test_error)}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize Grafana client for server '{server_id}': {str(e)}")
            return False
    
    def get_connection_info(self, server_id: str = None):
        """
        Get connection information for a specific server
        
        Args:
            server_id: Server ID, or None to use the current server
            
        Returns:
            Connection info dictionary or None if not found
        """
        # If no server_id specified, use current
        if server_id is None:
            server_id = self.current_server_id
        
        # If no current server, return None
        if server_id is None:
            logger.error("No server ID specified and no current server set")
            return None
        
        # Return the connection info if it exists
        if server_id in self.connections:
            return self.connections[server_id]
        
        logger.error(f"No connection found for server ID: {server_id}")
        return None
    
    def get_connection(self, server_id: str = None):
        """
        Get Grafana client connection for a specific server
        
        Args:
            server_id: Server ID, or None to use the current server
            
        Returns:
            GrafanaApi client instance or None if not found
        """
        # If no server_id specified, use current
        if server_id is None:
            server_id = self.current_server_id
        
        # If no current server, return None
        if server_id is None:
            logger.error("No server ID specified and no current server set")
            return None
        
        # Return the connection if it exists
        if server_id in self.connections:
            return self.connections[server_id]["client"]
        
        logger.error(f"No connection found for server ID: {server_id}")
        return None
    
    def set_current_server(self, server_id: str) -> bool:
        """
        Set the current server for subsequent operations
        
        Args:
            server_id: Server ID to set as current
            
        Returns:
            True if successful, False if server_id not found
        """
        if server_id in self.connections:
            self.current_server_id = server_id
            logger.debug(f"Current Grafana server set to '{server_id}'")
            return True
        
        logger.error(f"Cannot set current server to '{server_id}': Server not found")
        return False
    
    def get_current_server_id(self) -> str:
        """
        Get the current server ID
        
        Returns:
            Current server ID or None if no server is set
        """
        return self.current_server_id
    
    def remove_connection(self, server_id: str) -> bool:
        """
        Remove a Grafana server connection
        
        Args:
            server_id: Server ID to remove
            
        Returns:
            True if successful, False if server_id not found
        """
        if server_id in self.connections:
            del self.connections[server_id]
            logger.info(f"Removed Grafana server connection '{server_id}'")
            
            # If we removed the current server, reset current_server_id
            if self.current_server_id == server_id:
                self.current_server_id = next(iter(self.connections)) if self.connections else None
                if self.current_server_id:
                    logger.info(f"Current server is now '{self.current_server_id}'")
                else:
                    logger.warning("No more Grafana servers configured")
            
            return True
        
        logger.warning(f"Cannot remove Grafana server '{server_id}': Server not found")
        return False
    
    def get_organizations(self, server_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all organizations from a specific Grafana server
        
        Args:
            server_id: Server ID, or None to use the current server
            
        Returns:
            List of organizations with id and name
        """
        client = self.get_connection(server_id)
        if not client:
            return []
        
        logger.debug(f"Fetching organizations from Grafana server '{server_id or self.current_server_id}'")
        try:
            # Correct API call according to documentation
            orgs = client.organizations.list_organization()
            logger.debug(f"Successfully fetched {len(orgs)} organizations")
            return [{"id": org["id"], "name": org["name"]} for org in orgs]
        except Exception as e:
            logger.error(f"Error fetching organizations: {str(e)}")
            # Try a simpler API call for debugging
            try:
                health = client.health.check()
                logger.info(f"Grafana is accessible (Health check OK), but organization fetch failed. Database: {health.get('database', 'unknown')}")
                
                # Check if the current user is an admin
                try:
                    current_user = client.user.get_user()
                    logger.info(f"Current user: {current_user.get('login', 'unknown')}, isGrafanaAdmin: {current_user.get('isGrafanaAdmin', False)}")
                    
                    if not current_user.get('isGrafanaAdmin', False):
                        logger.warning("User is not a Grafana Admin. This is required to list organizations.")
                except Exception as user_error:
                    logger.error(f"Could not get current user info: {str(user_error)}")
                
            except Exception as health_error:
                logger.error(f"Grafana health check also failed: {str(health_error)}")
            
            # Return empty list to avoid breaking the application
            logger.info("Returning empty organization list")
            return []
    
    def switch_organization(self, org_id: int, server_id: str = None) -> bool:
        """
        Switch to a different organization context
        
        Args:
            org_id: Organization ID to switch to
            server_id: Server ID, or None to use the current server
            
        Returns:
            True if successful, False otherwise
        """
        client = self.get_connection(server_id)
        if not client:
            return False
        
        logger.debug(f"Switching to organization ID: {org_id} on server '{server_id or self.current_server_id}'")
        try:
            # Correct API call according to documentation
            client.organizations.switch_organization(org_id)
            logger.debug(f"Successfully switched to organization ID: {org_id}")
            return True
        except Exception as e:
            logger.error(f"Error switching organization: {str(e)}")
            return False
    
    # Update the other methods similarly to accept server_id parameter and use get_connection
    
    def get_dashboards(self, org_id: Optional[int] = None, server_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all dashboards for an organization
        
        Args:
            org_id: Optional organization ID. If provided, switches to that org first
            server_id: Server ID, or None to use the current server
            
        Returns:
            List of dashboards with id, uid, title
        """
        client = self.get_connection(server_id)
        if not client:
            return []
        
        logger.debug(f"Fetching dashboards for organization ID: {org_id if org_id else 'current'} on server '{server_id or self.current_server_id}'")
        try:
            if org_id:
                switched = self.switch_organization(org_id, server_id)
                if not switched:
                    logger.warning(f"Could not switch to organization {org_id}")
                
            # Correct API call according to documentation
            search_results = client.search.search_dashboards(type_="dash-db")
            
            dashboards = []
            for result in search_results:
                if result["type"] == "dash-db":  # Only include actual dashboards
                    dashboards.append({
                        "id": result["id"],
                        "uid": result["uid"],
                        "title": result["title"],
                        "url": result.get("url", ""),
                        "folderTitle": result.get("folderTitle", "General")
                    })
            
            logger.info(f"tched {len(dashboards)} dashboards")
            return dashboards
        except Exception as e:
            logger.error(f"Error fetching dashboards: {str(e)}")
            return []
   
    def get_dashboard_by_uid(self, uid: str, server_id: str = None) -> Dict[str, Any]:
        """
        Get dashboard details by UID
        
        Args:
            uid: Dashboard UID
            server_id: Server ID, or None to use the current server
            
        Returns:
            Dashboard details including panels
        """
        client = self.get_connection(server_id)
        if not client:
            return {}
        
        logger.debug(f"Fetching dashboard by UID: {uid} from server '{server_id or self.current_server_id}'")
        try:
            # Correct API call according to documentation
            dashboard = client.dashboard.get_dashboard(uid)
            logger.debug(f"Successfully fetched dashboard: {uid}")
            return dashboard
        except Exception as e:
            logger.error(f"Error fetching dashboard {uid}: {str(e)}")
            return {}

    def get_panels(self, dashboard_uid: str, server_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all panels from a dashboard
        
        Args:
            dashboard_uid: Dashboard UID
            server_id: Server ID, or None to use the current server
            
        Returns:
            List of panels with id, title, type
        """
        logger.debug(f"Fetching panels for dashboard: {dashboard_uid} from server '{server_id or self.current_server_id}'")
        try:
            dashboard = self.get_dashboard_by_uid(dashboard_uid, server_id)
            if not dashboard or "dashboard" not in dashboard:
                logger.warning(f"Dashboard {dashboard_uid} not found or has no 'dashboard' key")
                return []
            
            dashboard_data = dashboard["dashboard"]
            panels = []
            
            # Process panels (could be nested in rows for older dashboards)
            for panel in dashboard_data.get("panels", []):
                if panel.get("type") == "row":
                    # Extract panels from rows (for older dashboard formats)
                    for row_panel in panel.get("panels", []):
                        panels.append({
                            "id": row_panel["id"],
                            "title": row_panel["title"],
                            "type": row_panel["type"],
                            "description": row_panel.get("description", ""),
                            "datasource": row_panel.get("datasource", {}).get("type", "unknown")
                        })
                else:
                    panels.append({
                        "id": panel["id"],
                        "title": panel["title"],
                        "type": panel["type"],
                        "description": panel.get("description", ""),
                        "datasource": panel.get("datasource", {}).get("type", "unknown")
                    })
            
            logger.debug(f"Successfully fetched {len(panels)} panels from dashboard {dashboard_uid}")
            return panels
        except Exception as e:
            logger.error(f"Error fetching panels for dashboard {dashboard_uid}: {str(e)}")
            return []

    def get_panel_url(self, dashboard_uid: str, panel_id: int, 
                    width: int = 800, height: int = 400, 
                    theme: str = "dark", time_from: str = "now-6h",
                    time_to: str = "now", server_id: str = None) -> str:
        """
        Generate panel image URL for Playwright to capture
        
        Args:
            dashboard_uid: Dashboard UID
            panel_id: Panel ID
            width: Image width
            height: Image height
            theme: Panel theme (light/dark)
            time_from: Time range from
            time_to: Time range to
            server_id: Server ID, or None to use the current server
            
        Returns:
            Panel URL for Playwright to capture
        """
        # If no server_id specified, use current
        if server_id is None:
            server_id = self.current_server_id
        
        # Get the base URL for the specified server
        base_url = None
        if server_id in self.connections:
            base_url = self.connections[server_id]["url"].rstrip('/')
        else:
            logger.error(f"No connection found for server ID: {server_id}")
            # Fallback to the instance's grafana_url if available
            base_url = self.grafana_url.rstrip('/') if self.grafana_url else None
            if not base_url:
                logger.error("No Grafana URL available to generate panel URL")
                return ""
        
        # URLencode panel URL params
        params = {'panelId': panel_id,
                  'width': width,
                  'height': height,
                  'theme': theme,
                  'from': time_from,
                  'to': time_to,
                  'render': 'image'}
        panel_params = urlencode(params)

        panel_base = (f"{base_url}/d-solo/{dashboard_uid}?")
        panel_url = panel_base + panel_params
        logger.debug(f"Generated panel URL: {panel_url}")

        return panel_url

    def update_configuration(self, server_id: str = None, base_url: str = None, username: str = None, password: str = None) -> bool:
        """
        Update server configuration
        
        Args:
            server_id: Server ID to update, or None to update the current server
            base_url: New Grafana URL or None to keep current
            username: New Grafana username or None to keep current
            password: New Grafana password or None to keep current
            
        Returns:
            True if successful, False otherwise
        """
        # If no server_id specified, use current
        if server_id is None:
            server_id = self.current_server_id
        
        # If we still don't have a server_id, we can't update
        if server_id is None:
            logger.error("Cannot update configuration: No server ID specified and no current server")
            return False
        
        # If server exists, update its configuration
        if server_id in self.connections:
            connection = self.connections[server_id]
            
            # Update only provided parameters
            if base_url is not None:
                connection["url"] = base_url
            if username is not None:
                connection["username"] = username
            if password is not None:
                connection["password"] = password
            
            # Recreate the client with new settings
            try:
                connection["client"] = GrafanaApi.from_url(
                    url=connection["url"]+'?verify=false',
                    credential=(connection["username"], connection["password"])
                )
                logger.info(f"Grafana client for server '{server_id}' reinitialized with new settings")
                
                # Test connection with new settings
                health = connection["client"].health.check()
                logger.info(f"Successfully reconnected to Grafana server '{server_id}'. Database status: {health.get('database', 'unknown')}")
                return True
            except Exception as e:
                logger.error(f"Failed to reinitialize Grafana client for server '{server_id}': {str(e)}")
                return False
        else:
            # If server doesn't exist, create a new connection
            logger.info(f"Server '{server_id}' doesn't exist, creating new connection")
            return self.add_connection(server_id, base_url, username, password)
    
    def initialize_from_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Initialize multiple Grafana connections from settings
        
        Args:
            settings: Application settings containing grafana_servers list
            
        Returns:
            True if at least one server was initialized successfully
        """
        if "grafana_servers" not in settings or not settings["grafana_servers"]:
            logger.warning("No Grafana servers found in settings")
            return False
        
        success = False
        default_server_id = settings.get("general", {}).get("defaultServerId")
        
        # Clear existing connections
        self.connections = {}
        self.current_server_id = None
        
        # Add each server from settings
        for server in settings["grafana_servers"]:
            server_id = server.get("id")
            if not server_id:
                logger.warning("Skipping Grafana server with no ID")
                continue
            
            added = self.add_connection(
                server_id,
                server.get("url", ""),
                server.get("username", ""),
                server.get("password", "")
            )
            
            if added:
                success = True
                
                # Set as current if it's the default or the first successful one
                if server_id == default_server_id or server.get("is_default", False) or self.current_server_id is None:
                    self.current_server_id = server_id
                    logger.debug(f"Set '{server_id}' as current Grafana server")
        
        return success

    def get_grafana_version(self, server_id: str = None) -> str:
        """
        Get Grafana version for a specific server
        
        Args:
            server_id: Server ID, or None to use the current server
            
        Returns:
            Grafana version as string or "unknown" if not available
        """
        client = self.get_connection(server_id)
        if not client:
            return "unknown"
        
        try:
            version = client.version
            return version
        except Exception as e:
            logger.warning(f"Could not retrieve Grafana version for server '{server_id or self.current_server_id}': {str(e)}")
            return "unknown"
