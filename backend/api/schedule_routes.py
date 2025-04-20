import os
import sys
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from fastapi.responses import FileResponse

from api.auth_routes import get_current_user

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Initialize router with prefix
router = APIRouter(prefix="/api", tags=["schedules"])

# Request model
class ScheduleRequest(BaseModel):
    name: str
    layoutId: str
    reportLayout: Optional[Dict[str, Any]] = None
    schedule: Dict[str, Any]
    status: Optional[str] = "active"
    server_id: Optional[str] = None

# Dependency to get Scheduler service
async def get_scheduler_service():
    # This will be imported from api_controller to avoid circular imports
    from api.api_controller import scheduler_service
    return scheduler_service

@router.get("/schedules")
async def get_schedules(scheduler_service=Depends(get_scheduler_service)):
    """Get all scheduled reports"""
    logger.debug("Getting schedules")
    schedules = scheduler_service.get_all_schedules()
    return schedules

@router.post("/schedules")
async def create_schedule(
    schedule: ScheduleRequest, 
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    scheduler_service=Depends(get_scheduler_service)
):
    """Create a new scheduled report"""
    logger.debug(f"Creating schedule: {schedule.name}")
    schedule_id = scheduler_service.create_schedule(
        schedule.dict(),
        username=current_user.get("username")
    )
    background_tasks.add_task(scheduler_service.activate_schedule, schedule_id)
    return {"id": schedule_id}

@router.put("/schedules/{schedule_id}")
async def update_schedule(
    schedule_id: str, 
    schedule: ScheduleRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    scheduler_service=Depends(get_scheduler_service)
):
    """Update an existing scheduled report"""
    logger.debug(f"Updating schedule: {schedule_id}")
    
    # For admins, always allow updates
    is_admin = current_user.get("is_admin", False)
    
    # For non-admins, check ownership
    if not is_admin:
        existing_schedule = scheduler_service.get_schedule(schedule_id)
        if not existing_schedule:
            logger.warning(f"Schedule {schedule_id} not found for update")
            raise HTTPException(status_code=404, detail="Schedule not found")
            
        created_by = existing_schedule.get("created_by")
        if created_by and created_by != current_user.get("username"):
            logger.warning(f"User {current_user.get('username')} attempted to update schedule owned by {created_by}")
            raise HTTPException(status_code=403, detail="You don't have permission to update this schedule")
    
    success = scheduler_service.update_schedule(
        schedule_id, 
        schedule.dict(),
        username=current_user.get("username")
    )
    if not success:
        logger.warning(f"Schedule {schedule_id} not found")
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"status": "updated"}

@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    scheduler_service=Depends(get_scheduler_service)
):
    """Delete a scheduled report"""
    logger.debug(f"Deleting schedule: {schedule_id}")
    
    # For admins, always allow deletion
    is_admin = current_user.get("is_admin", False)
    
    # For non-admins, check ownership
    if not is_admin:
        existing_schedule = scheduler_service.get_schedule(schedule_id)
        if not existing_schedule:
            logger.warning(f"Schedule {schedule_id} not found for deletion")
            raise HTTPException(status_code=404, detail="Schedule not found")
            
        created_by = existing_schedule.get("created_by")
        if created_by and created_by != current_user.get("username"):
            logger.warning(f"User {current_user.get('username')} attempted to delete schedule owned by {created_by}")
            raise HTTPException(status_code=403, detail="You don't have permission to delete this schedule")
    
    success = scheduler_service.delete_schedule(schedule_id)
    if not success:
        logger.warning(f"Schedule {schedule_id} not found")
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"status": "deleted"}

@router.get("/schedules/{schedule_id}/history")
async def get_schedule_history(
    schedule_id: str,
    scheduler_service=Depends(get_scheduler_service)
):
    """Get history for a specific scheduled report"""
    logger.debug(f"Getting history for schedule {schedule_id}")
    schedule = scheduler_service.get_schedule(schedule_id)
    
    if not schedule:
        logger.warning(f"Schedule {schedule_id} not found")
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    history = schedule.get("history", [])
    return history

@router.get("/schedules/history/{file_name}")
async def download_history_report(
    file_name: str,
    scheduler_service=Depends(get_scheduler_service)
):
    """Download a historical report"""
    logger.debug(f"Downloading history report {file_name}")
    
    file_path = os.path.join(scheduler_service.schedules_dir, "history", file_name)
    
    if not os.path.exists(file_path):
        logger.warning(f"History report file {file_path} not found")
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=f"grafana-report-{file_name}"
    )