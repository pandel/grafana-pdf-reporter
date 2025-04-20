import os
import sys
import logging
from fastapi import APIRouter, Request
from datetime import datetime


# Import application version
from version import VERSION, VERSION_INFO

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


# Initialize router
router = APIRouter(prefix="/api", tags=["health"])

# Add a simple health check endpoint
@router.get("/health")
async def health_check():
    """Basic health check endpoint that returns API version and status"""
    logger.debug("Health check called")
    return {
        "status": "ok", 
        "timestamp": datetime.now().isoformat(),
        "version": VERSION,
        "app_info": VERSION_INFO
    }

@router.get("/health/queue")
async def queue_status():
    """Get the status of the job queue"""
    from api.api_controller import scheduler_service
    
    if scheduler_service:
        return {
            "status": "ok",
            "queue_size": len(scheduler_service.job_queue),
            "current_job": scheduler_service.currently_running_job
        }
    else:
        return {
            "status": "error",
            "message": "Scheduler service not initialized"
        }