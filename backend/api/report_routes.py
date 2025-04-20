import os
import sys
import uuid
import logging
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, Body, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
from io import BytesIO

# Create PDF generator directly instead of using the factory
from services.pdf_generator import PDFGenerator

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


# Initialize router with prefix
router = APIRouter(prefix="/api", tags=["reports"])

# Dependencies from api_controller
def get_progress_data():
    from api.api_controller import progress_data
    return progress_data

def update_progress(job_id, percentage, message=None):
    from api.api_controller import update_progress
    return update_progress(job_id, percentage, message)
        
# Dependency to get Grafana service
async def get_grafana_service():
    from api.api_controller import grafana_service
    return grafana_service

# Dependency to get Template service
async def get_template_service():
    from api.api_controller import template_service
    return template_service

@router.post("/preview")
async def generate_preview(
    request_data: dict = Body(...),
    grafana_service = Depends(get_grafana_service),
    template_service = Depends(get_template_service)
):
    """Generate a preview of the report"""
    logger.debug(f"Generating preview for layout with {len(request_data.get('panels', []))} panels")
    progress_data = get_progress_data()
    
    # Get server ID from request data if provided
    server_id = request_data.get('server_id')
    if server_id:
        logger.debug(f"Using server {server_id} for preview generation")
    
    # Verwende client_job_id, wenn vorhanden, sonst generiere eine neue
    job_id = request_data.get('client_job_id')
    if not job_id:
        job_id = f"preview_{uuid.uuid4()}"
    
    logger.debug(f"Using job ID: {job_id}")
    
    # Initialisiere die Fortschrittsdaten SOFORT
    if job_id not in progress_data:
        progress_data[job_id] = {
            "percentage": 0,
            "message": "Starting report generation",
            "timestamp": datetime.now().isoformat(),
            "history": [],  # Für die Speicherung aller Updates
            "server_id": server_id  # Store the server ID for reference
        }
    
    # Get template if specified
    template_config = {}
    if request_data.get('templateId'):
        template_config = template_service.get_template(request_data.get('templateId'))
        if not template_config:
            logger.warning(f"Template {request_data.get('templateId')} not found")
            raise HTTPException(status_code=404, detail="Template not found")
    else:
        # Use default template
        template_config = template_service.get_default_template()
    
    # Switch to correct organization with the specified server if provided
    grafana_service.switch_organization(request_data.get('organizationId'), server_id)
    
    # Check if job has been cancelled before PDF generation
    if job_id in progress_data and progress_data[job_id].get("cancelled", False):
        logger.info(f"Job {job_id} was cancelled before starting PDF generation")
        if progress_callback:
            progress_callback(job_id, -1, "Report generation cancelled")
        raise HTTPException(status_code=400, detail="Report generation cancelled by user")
    
    # Grafana version
    grafana_version = grafana_service.get_grafana_version(server_id)

    # Set the original server to restore later if needed
    original_server = None
    if server_id:
        original_server = grafana_service.get_current_server_id()
        grafana_service.set_current_server(server_id)
        grafana_conn = grafana_service.get_connection_info()
    
    try:
        # Get URLs for grafana connection from the current server context
        grafana_url = grafana_conn.get("url")
        grafana_username = grafana_conn.get("username")
        grafana_password = grafana_conn.get("password")
        
        logger.info(f"Creating PDF Generator with Grafana URL: {grafana_url}")
        
        # Create PDF generator directly
        pdf_generator = PDFGenerator(grafana_url, grafana_username, grafana_password)
        await pdf_generator.initialize()
        
        try:
            # Hier wird die Job-ID, die progress_callback-Funktion und server_id übergeben
            pdf_data = await pdf_generator.generate_report(
                layout_config=request_data,
                template_config=template_config,
                grafana_service=grafana_service,
                job_id=job_id,
                progress_callback=update_progress,
                server_id=server_id,
                grafana_version=grafana_version
            )
            
            # Save PDF data for later download
            progress_data[job_id]["pdf_data"] = pdf_data
            progress_data[job_id]["percentage"] = 100
            progress_data[job_id]["message"] = "PDF generation complete"
            progress_data[job_id]["server_id"] = server_id
            
            # Add 100% to history
            progress_data[job_id]["history"].append({
                "percentage": 100,
                "message": "PDF generation complete",
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            })
            
            # Return PDF as response
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            server_suffix = f"_{server_id}" if server_id else ""
            filename = f"grafana-report-preview{server_suffix}-{timestamp}.pdf"
            logger.debug(f"Preview generated successfully: {filename}")
            
            return {
                "job_id": job_id,
                "status": "completed",
                "download_url": f"/api/download/{job_id}",
                "server_id": server_id
            }
        finally:
            # Make sure to close the PDF generator
            await pdf_generator.close()
    
    except Exception as e:
        logger.error(f"Error generating preview: {str(e)}")
        # Fehler im progress_data speichern
        if job_id in progress_data:
            progress_data[job_id]["error"] = str(e)
            progress_data[job_id]["status"] = "error"
        else:
            progress_data[job_id] = {
                "percentage": 0,
                "message": "Error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "error",
                "server_id": server_id,
                "history": [{
                    "percentage": 0,
                    "message": "Error",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "status": "error"
                }]
            }
        raise HTTPException(status_code=500, detail=f"Error generating preview: {str(e)}")
    finally:
        # Restore the original server if we changed it
        if server_id and original_server:
            grafana_service.set_current_server(original_server)

@router.get("/download/{job_id}")
async def download_pdf(job_id: str):
    """Download a generated PDF file"""
    logger.info(f"Download requested for job {job_id}")
    progress_data = get_progress_data()
    
    # Prüfen, ob das PDF im progress_data verfügbar ist
    if job_id in progress_data and "pdf_data" in progress_data[job_id]:
        pdf_data = progress_data[job_id]["pdf_data"]
        filename = f"grafana-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf"
        
        logger.info(f"Serving PDF for job {job_id} with filename {filename}")
        return StreamingResponse(
            pdf_data, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        logger.warning(f"PDF not found for job {job_id}")
        # Versuche zu debuggen was im progress_data ist
        if job_id in progress_data:
            logger.info(f"Job {job_id} exists in progress_data, keys: {progress_data[job_id].keys()}")
        else:
            logger.info(f"Job {job_id} not found in progress_data")
            logger.info(f"Current jobs in progress_data: {list(progress_data.keys())}")
        
        raise HTTPException(status_code=404, detail=f"PDF for job {job_id} not found or generation not completed")

@router.post("/export")
async def export_report(
    request_data: dict = Body(...),
    grafana_service = Depends(get_grafana_service),
    template_service = Depends(get_template_service)
):
    """Generate and export a PDF report"""
    logger.debug(f"Exporting report for layout with {len(request_data.get('panels', []))} panels")
    progress_data = get_progress_data()
    
    # Get server ID from request data if provided
    server_id = request_data.get('server_id')
    if server_id:
        logger.info(f"Using server {server_id} for PDF export")
    
    # Verwende client_job_id, wenn vorhanden, sonst generiere eine neue
    job_id = request_data.get('client_job_id') or f"export_{uuid.uuid4()}"
    
    # Similar to preview but potentially with higher quality settings
    template_config = {}
    if request_data.get('templateId'):
        template_config = template_service.get_template(request_data.get('templateId'))
        if not template_config:
            logger.warning(f"Template {request_data.get('templateId')} not found")
            raise HTTPException(status_code=404, detail="Template not found")
    else:
        template_config = template_service.get_default_template()
    
    # Switch to correct organization with the specified server if provided
    grafana_service.switch_organization(request_data.get('organizationId'), server_id)
    
    # Set the original server to restore later if needed
    original_server = None
    if server_id:
        original_server = grafana_service.get_current_server_id()
        grafana_service.set_current_server(server_id)
        grafana_conn = grafana_service.get_connection_info()
        
    try:
        # Initialisiere den Fortschrittsdatensatz, falls noch nicht vorhanden
        if job_id not in progress_data:
            progress_data[job_id] = {
                "percentage": 0,
                "message": "Starting report export",
                "timestamp": datetime.now().isoformat(),
                "history": []  # Für die Speicherung aller Updates
            }
        
        # Check if job has been cancelled before PDF generation
        if job_id in progress_data and progress_data[job_id].get("cancelled", False):
            logger.info(f"Job {job_id} was cancelled before starting PDF generation")
            raise HTTPException(status_code=400, detail="Report generation cancelled by user")
        
        # Get URLs for grafana connection from the current server context
        grafana_url = grafana_conn.get("url")
        grafana_username = grafana_conn.get("username")
        grafana_password = grafana_conn.get("password")
        
        logger.info(f"Creating PDF Generator with Grafana URL: {grafana_url}")
        
        # Create PDF generator directly
        pdf_generator = PDFGenerator(grafana_url, grafana_username, grafana_password)
        await pdf_generator.initialize()
        
        try:
            # Grafana version
            grafana_version = grafana_service.get_grafana_version(server_id)

            # Generate report with the specified server if provided
            pdf_data = await pdf_generator.generate_report(
                layout_config=request_data,
                template_config=template_config,
                grafana_service=grafana_service,
                job_id=job_id,
                progress_callback=update_progress,
                server_id=server_id,
                grafana_version=grafana_version
            )
            
            # Save PDF data for later download
            if job_id not in progress_data:
                progress_data[job_id] = {
                    "percentage": 100,
                    "message": "PDF export complete",
                    "timestamp": datetime.now().isoformat(),
                    "history": [{
                        "percentage": 100,
                        "message": "PDF export complete",
                        "timestamp": datetime.now().isoformat()
                    }],
                    "server_id": server_id  # Store the server ID for reference
                }
            else:
                progress_data[job_id]["server_id"] = server_id
            
            progress_data[job_id]["pdf_data"] = pdf_data
            progress_data[job_id]["percentage"] = 100
            progress_data[job_id]["message"] = "PDF export complete"
            
            # Add 100% to history if not already there
            if "history" in progress_data[job_id]:
                last_entry = progress_data[job_id]["history"][-1] if progress_data[job_id]["history"] else None
                if not last_entry or last_entry.get("percentage") != 100:
                    progress_data[job_id]["history"].append({
                        "percentage": 100,
                        "message": "PDF export complete",
                        "timestamp": datetime.now().isoformat(),
                        "status": "completed"
                    })
            
            # Generate a filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            server_suffix = f"_{server_id}" if server_id else ""
            filename = f"grafana-report{server_suffix}-{timestamp}.pdf"
            
            logger.debug(f"Report exported successfully: {filename}")
            
            return {
                "job_id": job_id,
                "status": "completed",
                "download_url": f"/api/download/{job_id}",
                "server_id": server_id
            }
        finally:
            # Make sure to close the PDF generator to release resources
            await pdf_generator.close()
    except Exception as e:
        logger.error(f"Error exporting report: {str(e)}")
        # Fehler im progress_data speichern
        if job_id in progress_data:
            progress_data[job_id]["error"] = str(e)
            progress_data[job_id]["status"] = "error"
        else:
            progress_data[job_id] = {
                "percentage": 0,
                "message": "Error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "status": "error",
                "server_id": server_id,
                "history": [{
                    "percentage": 0,
                    "message": "Error",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "status": "error"
                }]
            }
        raise HTTPException(status_code=500, detail=f"Error exporting report: {str(e)}")
    finally:
        # Restore the original server if we changed it
        if server_id and original_server:
            grafana_service.set_current_server(original_server)

@router.get("/progress/{job_id}")
async def get_progress(job_id: str, token: str = None):
    """Stream progress updates for a specific job"""
    from api.api_controller import auth_service
    progress_data = get_progress_data()
    
    # Authentifizierung über Token in der URL
    if token:
        try:
            user_info = auth_service.verify_token(token)
            if not user_info:
                logger.warning(f"Invalid token provided for progress stream: {job_id}")
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"}
                )
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            raise HTTPException(
                status_code=401,
                detail="Authentication error",
                headers={"WWW-Authenticate": "Bearer"}
            )
    else:
        # Wenn kein Token angegeben ist, prüfen wir ob der Endpoint öffentlich sein soll
        # Dies ist eine Vereinfachung für Entwicklungszwecke - für Produktion sollte immer ein Token verlangt werden
        if os.environ.get("ALLOW_PUBLIC_PROGRESS", "false").lower() != "true":
            logger.warning(f"No token provided for progress stream: {job_id}")
            raise HTTPException(
                status_code=401,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    logger.info(f"Client connected to progress stream for job {job_id}")
    
    # *** WICHTIG: Initialisiere progress_data sofort, wenn es noch nicht existiert ***
    if job_id not in progress_data:
        progress_data[job_id] = {
            "percentage": 0,
            "message": "Initializing report generation",
            "timestamp": datetime.now().isoformat(),
            "history": []
        }
        logger.info(f"Initialized progress data for job {job_id}")
    
    async def event_generator():
        try:
            logger.info("Generate progress update event")
            # Anfangs kurz warten, um sicherzustellen, dass wir keine Rasse-Bedingung mit dem ersten Update haben
            await asyncio.sleep(0.2)
            
            while True:
                # Wenn der Job in Bearbeitung ist
                if job_id in progress_data:
                    current_progress = progress_data[job_id]

                    if current_progress.get("cancelled", False):
                        # Sende ein Abbruch-Event und beende den Stream
                        cancel_data = json.dumps({
                            "percentage": -1,
                            "message": "Job cancelled by user",
                            "status": "cancelled"
                        })
                        yield f"data: {cancel_data}\n\n"
                        break
                    
                    status = "completed" if current_progress.get("percentage", 0) >= 100 else "in_progress"
                    
                    update = {
                        "percentage": current_progress.get("percentage", 0),
                        "message": current_progress.get("message", "Processing"),
                        "status": status
                    }
                    data = json.dumps(update)
                    yield f"data: {data}\n\n"
                    
                    # Wenn der Job bereits fertig ist, beenden
                    if status == "completed" or "error" in current_progress:
                        break
                    
                    # Wenn PDF-Daten verfügbar sind, wird fertig
                    if "pdf_data" in current_progress:
                        yield f"data: {json.dumps({'percentage': 100, 'status': 'completed', 'message': 'PDF ready for download'})}\n\n"
                        break
                else:
                    # Job nicht gefunden, aber wir nehmen NICHT an, dass er abgeschlossen ist!
                    # Stattdessen initialisieren wir ihn mit 0%
                    logger.info(f"Job {job_id} not found in progress data, initializing with 0%")
                    progress_data[job_id] = {
                        "percentage": 0,
                        "message": "Waiting for PDF generation to start",
                        "timestamp": datetime.now().isoformat(),
                        "history": []
                    }
                    
                    data = json.dumps({
                        "percentage": 0,
                        "message": "Initializing...",
                        "status": "initializing"
                    })
                    yield f"data: {data}\n\n"
                
                # Kurze Pause, um nicht zu viele Events zu senden
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            logger.info(f"Connection for job {job_id} was closed by client")
            raise
        except Exception as e:
            logger.error(f"Error in event generator for job {job_id}: {str(e)}")
            # Eine letzte Nachricht senden, um den Client zu informieren
            error_data = json.dumps({"error": str(e), "status": "error"})
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Für NGINX wichtig
        }
    )

@router.delete("/job/{job_id}")
async def cancel_job(job_id: str):
    """Cancel an ongoing report generation job"""
    logger.info(f"Request to cancel job {job_id}")
    progress_data = get_progress_data()
    
    if job_id in progress_data:
        progress_data[job_id]["cancelled"] = True
        progress_data[job_id]["message"] = "Job cancelled by user"
        logger.info(f"Job {job_id} marked as cancelled")
        return {"status": "cancelled"}
    else:
        logger.warning(f"Job {job_id} not found for cancellation")
        raise HTTPException(status_code=404, detail="Job not found")