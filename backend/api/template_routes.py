import os
import sys
import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Initialize router with prefix
router = APIRouter(prefix="/api", tags=["templates"])

# Request model
class TemplateRequest(BaseModel):
    name: str
    header: Dict[str, Any]
    footer: Dict[str, Any]
    page: Dict[str, Any]

# Dependency to get Template service
async def get_template_service():
    # This will be imported from api_controller to avoid circular imports
    from api.api_controller import template_service
    return template_service

@router.get("/templates")
async def get_templates(template_service=Depends(get_template_service)):
    """Get all available templates"""
    logger.debug("Getting templates")
    templates = template_service.get_all_templates()
    return templates

@router.get("/templates/{template_id}")
async def get_template(template_id: str, template_service=Depends(get_template_service)):
    """Get a specific template by ID"""
    logger.debug(f"Getting template {template_id}")
    template = template_service.get_template(template_id)
    if not template:
        logger.warning(f"Template {template_id} not found")
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.post("/templates")
async def create_template(template: TemplateRequest, template_service=Depends(get_template_service)):
    """Create a new template"""
    logger.debug(f"Creating new template: {template.name}")
    template_id = template_service.create_template(template.dict())
    return {"id": template_id}

@router.put("/templates/{template_id}")
async def update_template(template_id: str, template: TemplateRequest, template_service=Depends(get_template_service)):
    """Update an existing template"""
    logger.debug(f"Updating template: {template_id}")
    success = template_service.update_template(template_id, template.dict())
    if not success:
        logger.warning(f"Template {template_id} not found for update")
        raise HTTPException(status_code=404, detail="Template not found")
    return {"status": "updated"}

@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, template_service=Depends(get_template_service)):
    """Delete a template"""
    logger.debug(f"Deleting template: {template_id}")
    success = template_service.delete_template(template_id)
    if not success:
        logger.warning(f"Template {template_id} not found for deletion")
        raise HTTPException(status_code=404, detail="Template not found")
    return {"status": "deleted"}