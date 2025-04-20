import os
import sys
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Initialize router with prefix
router = APIRouter(prefix="/api", tags=["settings"])

# Dependency to get Settings service
async def get_settings_service():
    # This will be imported from api_controller to avoid circular imports
    from api.api_controller import settings_service
    return settings_service

@router.get("/settings")
async def get_settings(settings_service=Depends(get_settings_service)):
    """Get all application settings"""
    logger.debug("Getting application settings")
    settings = settings_service.get_decrypted_settings()
    return settings

@router.post("/settings")
async def update_settings(
    settings: Dict[str, Any],
    settings_service=Depends(get_settings_service)
):
    """Update application settings"""
    logger.debug("Updating application settings")
    success = settings_service.update_settings(settings)
    if not success:
        logger.warning("Failed to update settings")
        raise HTTPException(status_code=500, detail="Failed to update settings")
    
    # Automatically apply settings after saving
    try:
        # Rufe apply_settings auf, welches die Einstellungen auf alle laufenden Services anwendet
        result = await apply_settings()
        logger.info("Settings updated and applied successfully")
        return {"status": "updated and applied", "apply_result": result}
    except Exception as e:
        # Wenn apply_settings fehlschlägt, trotzdem Erfolg für das Update zurückgeben
        logger.warning(f"Settings were saved but could not be applied: {str(e)}")
        return {"status": "updated", "warning": "Settings were saved but could not be applied"}

@router.post("/settings/test/grafana")
async def test_grafana_connection(
    settings: Dict[str, Any],
    settings_service=Depends(get_settings_service)
):
    """Test Grafana connection with provided settings"""
    logger.debug("Testing Grafana connection")
    result = settings_service.test_grafana_connection(settings)
    return result

@router.post("/settings/test/email")
async def test_email_settings(
    settings: Dict[str, Any],
    settings_service=Depends(get_settings_service)
):
    """Test email settings with provided configuration"""
    logger.debug("Testing email settings")
    result = settings_service.test_email_settings(settings)
    return result

@router.post("/settings/apply")
async def apply_settings():
    """Apply settings to running services without restart"""
    logger.debug("Applying settings to running services")
    try:
        # Import here to avoid circular imports
        from api.api_controller import grafana_service, scheduler_service, settings_service
        
        # Load current settings
        app_settings = settings_service.get_decrypted_settings()  # Use decrypted settings
        
        # Apply multi-server configuration
        if "grafana_servers" in app_settings and grafana_service:
            grafana_service.initialize_from_settings(app_settings)
            logger.info("Applied multi-server settings to Grafana service")
        elif "grafana" in app_settings and grafana_service:
            # Backward compatibility for single server
            grafana_settings = app_settings.get("grafana", {})
            success = grafana_service.update_configuration(
                base_url=grafana_settings.get("url"),
                username=grafana_settings.get("username"),
                password=grafana_settings.get("password")
            )
            if not success:
                logger.warning("Failed to update Grafana configuration")
        
        # Apply email settings if Scheduler service is initialized
        if scheduler_service:
            email_settings = app_settings.get("email", {})
            scheduler_service.update_email_settings(email_settings)
        
        return {"status": "settings applied"}
    except Exception as e:
        logger.error(f"Error applying settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error applying settings: {str(e)}")

@router.get("/settings/initialized")
async def check_settings_initialized(settings_service=Depends(get_settings_service)):
    """Check if settings file exists and is initialized"""
    logger.debug("Checking if settings are initialized")
    
    # Check if settings file exists
    settings_exist = os.path.exists(settings_service.settings_path)
    
    # If it doesn't exist, create default settings
    if not settings_exist:
        logger.info("Settings file does not exist, will create default settings")
        settings_service._create_default_settings()
        settings_exist = True  # Now it exists with defaults
        
    # Check if defaults include required Grafana settings
    settings = settings_service.get_settings()
        
    # Check if Grafana URL and credentials are set
    if settings["status"] == "init":            
        # Settings exist but aren't fully configured
        logger.info("Settings exist but aren't fully configured yet")
        return {"initialized": False, "reason": "default_settings"}
    
    return {"initialized": settings_exist}

@router.post("/settings/test/ldap")
async def test_ldap_connection(
    settings: Dict[str, Any],
    settings_service=Depends(get_settings_service)
):
    """Test LDAP connection with provided settings"""
    logger.debug("Testing LDAP connection")
    result = settings_service.test_ldap_connection(settings)
    return result

@router.get("/servers")
async def get_grafana_servers(settings_service=Depends(get_settings_service)):
    """Get all configured Grafana servers"""
    logger.debug("Getting Grafana servers from settings")
    
    settings = settings_service.get_decrypted_settings()
    if not settings or "grafana_servers" not in settings:
        return []
    
    # Return servers without passwords
    servers = []
    for server in settings["grafana_servers"]:
        # Create a copy of the server without the password
        #server_copy = {k: v for k, v in server.items() if k != "password"}
        server_copy = {k: v for k, v in server.items()}
        servers.append(server_copy)
    
    return servers

@router.post("/servers")
async def add_grafana_server(
    server: Dict[str, Any],
    settings_service=Depends(get_settings_service)
):
    """Add a new Grafana server"""
    logger.debug(f"Adding new Grafana server: {server.get('name')}")
    
    # Get current settings
    settings = settings_service.get_decrypted_settings()
    if not settings:
        raise HTTPException(status_code=500, detail="Failed to load settings")
    
    # Ensure grafana_servers exists
    if "grafana_servers" not in settings:
        settings["grafana_servers"] = []
    
    # Generate server ID
    server["id"] = str(uuid.uuid4())
    
    # Add server to the list
    settings["grafana_servers"].append(server)
    
    # If this is the first server or marked as default, set it as default
    if len(settings["grafana_servers"]) == 1 or server.get("is_default", False):
        # Set as default in general settings
        if "general" not in settings:
            settings["general"] = {}
        settings["general"]["defaultServerId"] = server["id"]
        
        # Make sure only one server is set as default
        for s in settings["grafana_servers"]:
            s["is_default"] = (s["id"] == server["id"])
    
    # Save settings
    if settings_service.update_settings(settings):
        # Return without password
        #server_copy = {k: v for k, v in server.items() if k != "password"}
        server_copy = {k: v for k, v in server.items()}
        return server_copy
    else:
        raise HTTPException(status_code=500, detail="Failed to save server settings")

@router.put("/servers/{server_id}")
async def update_grafana_server(
    server_id: str,
    server: Dict[str, Any],
    settings_service=Depends(get_settings_service)
):
    """Update a Grafana server"""
    logger.debug(f"Updating Grafana server: {server_id}")
    
    # Get current settings
    settings = settings_service.get_decrypted_settings()
    if not settings or "grafana_servers" not in settings:
        raise HTTPException(status_code=404, detail="Grafana servers not found in settings")
    
    # Find server by ID
    server_index = None
    for i, s in enumerate(settings["grafana_servers"]):
        if s.get("id") == server_id:
            server_index = i
            break
    
    if server_index is None:
        raise HTTPException(status_code=404, detail=f"Grafana server {server_id} not found")
    
    # If this is a default server update, update the default in general settings
    was_default = settings["grafana_servers"][server_index].get("is_default", False)
    will_be_default = server.get("is_default", was_default)
    
    # Ensure server ID doesn't change
    server["id"] = server_id
    
    # Update server
    settings["grafana_servers"][server_index] = server
    
    # If this server is now default but wasn't before, update default in general settings
    # and make sure only one server is marked as default
    if will_be_default and not was_default:
        if "general" not in settings:
            settings["general"] = {}
        settings["general"]["defaultServerId"] = server_id
        
        # Update all other servers to not be default
        for s in settings["grafana_servers"]:
            if s["id"] != server_id:
                s["is_default"] = False
    
    # Save settings
    if settings_service.update_settings(settings):
        # Return without password
        server_copy = {k: v for k, v in server.items() if k != "password"}
        return server_copy
    else:
        raise HTTPException(status_code=500, detail="Failed to save server settings")

@router.delete("/servers/{server_id}")
async def delete_grafana_server(
    server_id: str,
    settings_service=Depends(get_settings_service)
):
    """Delete a Grafana server"""
    logger.debug(f"Deleting Grafana server: {server_id}")
    
    # Get current settings
    settings = settings_service.get_decrypted_settings()
    if not settings or "grafana_servers" not in settings:
        raise HTTPException(status_code=404, detail="Grafana servers not found in settings")
    
    # Find server by ID
    server_index = None
    for i, s in enumerate(settings["grafana_servers"]):
        if s.get("id") == server_id:
            server_index = i
            break
    
    if server_index is None:
        raise HTTPException(status_code=404, detail=f"Grafana server {server_id} not found")
    
    # Check if this is the default server
    is_default = settings["grafana_servers"][server_index].get("is_default", False)
    is_default_in_general = settings.get("general", {}).get("defaultServerId") == server_id
    
    # Don't allow deleting the last server
    if len(settings["grafana_servers"]) <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the last Grafana server")
    
    # Remove the server
    removed_server = settings["grafana_servers"].pop(server_index)
    
    # If this was the default server, set a new default
    if is_default or is_default_in_general:
        if settings["grafana_servers"]:
            new_default_server = settings["grafana_servers"][0]
            new_default_server["is_default"] = True
            
            if "general" not in settings:
                settings["general"] = {}
            settings["general"]["defaultServerId"] = new_default_server["id"]
    
    # Save settings
    if settings_service.update_settings(settings):
        return {"id": server_id, "status": "deleted"}
    else:
        # Put the server back if settings couldn't be saved
        settings["grafana_servers"].insert(server_index, removed_server)
        raise HTTPException(status_code=500, detail="Failed to save server settings")

@router.post("/servers/{server_id}/test")
async def test_grafana_server_connection(
    server_id: str,
    settings: Dict[str, Any],
    settings_service=Depends(get_settings_service)
):
    """Test connection to a specific Grafana server"""
    logger.debug(f"Testing connection to Grafana server: {server_id}")
    
    # Create a temporary Grafana service instance
    from services.grafana_service import GrafanaService
    temp_service = GrafanaService()
    
    # Add the server connection
    server_name=settings.get("name")
    success = temp_service.add_connection(
        server_id,
        settings.get("url"),
        settings.get("username"),
        settings.get("password")
    )
    
    if success:
        return {
            "success": True,
            "message": f"Successfully connected to Grafana server '{server_name}'"
        }
    else:
        return {
            "success": False,
            "message": "Failed to connect to Grafana server"
        }