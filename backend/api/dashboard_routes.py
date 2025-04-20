import os
import sys
import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


# Initialize router with prefix
router = APIRouter(prefix="/api", tags=["dashboards"])

# Dependency to get Grafana service
async def get_grafana_service():
    # This will be imported from api_controller to avoid circular imports
    from api.api_controller import grafana_service
    return grafana_service

# Add a route to switch the current server
@router.post("/servers/{server_id}/select")
async def select_server(server_id: str, grafana_service=Depends(get_grafana_service)):
    """Set a server as the current active server"""
    logger.debug(f"Setting server {server_id} as current")
    
    if grafana_service.set_current_server(server_id):
        return {"success": True, "message": f"Server {server_id} is now the active server"}
    else:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")

# Update the existing endpoints to work with server IDs
@router.get("/organizations")
async def get_organizations(
    server_id: Optional[str] = None,
    grafana_service=Depends(get_grafana_service)
):
    """Get all Grafana organizations"""
    logger.debug(f"Getting organizations for server {server_id or 'current'}")
    orgs = grafana_service.get_organizations(server_id)
    return orgs

@router.get("/servers/{server_id}/organizations")
async def get_server_organizations(
    server_id: str,
    grafana_service=Depends(get_grafana_service)
):
    """Get all organizations for a specific server"""
    logger.debug(f"Getting organizations for server {server_id}")
    orgs = grafana_service.get_organizations(server_id)
    return orgs

# Update the other endpoints similarly...
@router.get("/organizations/{org_id}/dashboards")
async def get_dashboards(
    org_id: int, 
    server_id: Optional[str] = None,
    grafana_service=Depends(get_grafana_service)
):
    """Get all dashboards for an organization"""
    logger.debug(f"Getting dashboards for organization {org_id} on server {server_id or 'current'}")
    dashboards = grafana_service.get_dashboards(org_id, server_id)
    return dashboards

@router.get("/servers/{server_id}/organizations/{org_id}/dashboards")
async def get_server_dashboards(
    server_id: str,
    org_id: int,
    grafana_service=Depends(get_grafana_service)
):
    """Get all dashboards for a specific organization on a specific server"""
    logger.debug(f"Getting dashboards for organization {org_id} on server {server_id}")
    dashboards = grafana_service.get_dashboards(org_id, server_id)
    return dashboards

@router.get("/dashboards/{dashboard_uid}/panels")
async def get_panels(
    dashboard_uid: str, 
    server_id: Optional[str] = None,
    grafana_service=Depends(get_grafana_service)
):
    """Get all panels for a dashboard"""
    logger.debug(f"Getting panels for dashboard {dashboard_uid} on server {server_id or 'current'}")
    panels = grafana_service.get_panels(dashboard_uid, server_id)
    return panels

@router.get("/servers/{server_id}/dashboards/{dashboard_uid}/panels")
async def get_server_panels(
    server_id: str,
    dashboard_uid: str,
    grafana_service=Depends(get_grafana_service)
):
    """Get all panels for a specific dashboard on a specific server"""
    logger.debug(f"Getting panels for dashboard {dashboard_uid} on server {server_id}")
    panels = grafana_service.get_panels(dashboard_uid, server_id)
    return panels