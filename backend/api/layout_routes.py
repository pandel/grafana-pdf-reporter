import os
import sys
import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from api.auth_routes import get_current_user

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


# Initialize router with prefix
router = APIRouter(prefix="/api", tags=["layouts"])

# Request model
class SavedLayoutRequest(BaseModel):
    name: str
    description: str = None
    organizationId: int
    rows: int
    columns: int
    panels: List[Dict[str, Any]]
    templateId: Optional[str] = None
    theme: Optional[str] = "light"
    timeRange: Optional[Dict[str, str]] = {"from": "now-6h", "to": "now"}
    server_id: Optional[str] = None

# Dependency to get Layout service
async def get_layout_service():
    # This will be imported from api_controller to avoid circular imports
    from api.api_controller import layout_service
    return layout_service

@router.get("/layouts")
async def get_layouts(layout_service=Depends(get_layout_service)):
    """Get all saved layouts"""
    logger.debug("Getting saved layouts")
    layouts = layout_service.get_all_layouts()
    return layouts

@router.get("/layouts/{layout_id}")
async def get_layout(layout_id: str, layout_service=Depends(get_layout_service)):
    """Get a specific saved layout by ID"""
    logger.debug(f"Getting layout {layout_id}")
    layout = layout_service.get_layout(layout_id)
    if not layout:
        logger.warning(f"Layout {layout_id} not found")
        raise HTTPException(status_code=404, detail="Layout not found")
    return layout

@router.post("/layouts")
async def create_layout(
    layout: SavedLayoutRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    layout_service=Depends(get_layout_service)
):
    """Create a new saved layout"""
    logger.info(f"API: Creating new layout with name: {layout.name}")
    logger.debug(f"Received layout data: {layout.dict()}")
    
    # Save layout data including server_id if provided
    try:
        layout_id = layout_service.create_layout(
            layout.dict(), 
            username=current_user.get("username")
        )
        logger.info(f"Layout created successfully with ID: {layout_id}")
        return {"id": layout_id}
    except Exception as e:
        logger.error(f"Failed to create layout: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create layout: {str(e)}")

@router.put("/layouts/{layout_id}")
async def update_layout(
    layout_id: str, 
    layout: SavedLayoutRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    layout_service=Depends(get_layout_service)
):
    """Update an existing saved layout"""
    logger.debug(f"Updating layout: {layout_id}")
    
    # For admins, always allow updates
    is_admin = current_user.get("is_admin", False)
    
    # For non-admins, check ownership
    if not is_admin:
        existing_layout = layout_service.get_layout(layout_id)
        if not existing_layout:
            logger.warning(f"Layout {layout_id} not found for update")
            raise HTTPException(status_code=404, detail="Layout not found")
            
        created_by = existing_layout.get("created_by")
        if created_by and created_by != current_user.get("username"):
            logger.warning(f"User {current_user.get('username')} attempted to update layout owned by {created_by}")
            raise HTTPException(status_code=403, detail="You don't have permission to update this layout")
    
    success = layout_service.update_layout(
        layout_id, 
        layout.dict(),
        username=current_user.get("username")
    )
    if not success:
        logger.warning(f"Layout {layout_id} not found for update")
        raise HTTPException(status_code=404, detail="Layout not found")
    return {"status": "updated"}

@router.delete("/layouts/{layout_id}")
async def delete_layout(
    layout_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    layout_service=Depends(get_layout_service)
):
    """Delete a saved layout"""
    logger.debug(f"Deleting layout: {layout_id}")
    
    # For admins, always allow deletion
    is_admin = current_user.get("is_admin", False)
    
    # For non-admins, check ownership
    if not is_admin:
        existing_layout = layout_service.get_layout(layout_id)
        if not existing_layout:
            logger.warning(f"Layout {layout_id} not found for deletion")
            raise HTTPException(status_code=404, detail="Layout not found")
            
        created_by = existing_layout.get("created_by")
        if created_by and created_by != current_user.get("username"):
            logger.warning(f"User {current_user.get('username')} attempted to delete layout owned by {created_by}")
            raise HTTPException(status_code=403, detail="You don't have permission to delete this layout")
    
    success = layout_service.delete_layout(layout_id)
    if not success:
        logger.warning(f"Layout {layout_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Layout not found")
    return {"status": "deleted"}