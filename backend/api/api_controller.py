import os
import sys
import logging
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import application version
from version import VERSION, VERSION_INFO


# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

logger.info(f"Starting Grafana PDF Reporter Backend v{VERSION}")

# Import services
from services.grafana_service import GrafanaService
from services.pdf_generator import PDFGenerator
from services.template_service import TemplateService
from services.scheduler_service import SchedulerService
from services.layout_service import LayoutService
from services.settings_service import SettingsService
from services.auth_service import AuthService

# Import auth routes
from api.auth_routes import router as auth_router
from api.auth_routes import get_current_user, get_admin_user

# Import auth middleware
from api.auth_middleware import AuthMiddleware

# Import all routers
from api.health_routes import router as health_router
from api.dashboard_routes import router as dashboard_router
from api.template_routes import router as template_router
from api.layout_routes import router as layout_router
from api.report_routes import router as report_router
from api.schedule_routes import router as schedule_router
from api.settings_routes import router as settings_router

# Initialize FastAPI app
app = FastAPI(
    title="Grafana PDF Report Generator API",
    version=VERSION,
    description=VERSION_INFO["description"],
    debug=True,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

# Add CORS middleware to allow requests from Vue.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    #allow_methods=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.debug(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Request error: {str(e)}")
        raise

# Initialize services - these need to be accessible from the router modules
grafana_service = GrafanaService()
template_service = TemplateService("templates")
scheduler_service = SchedulerService("schedules")
layout_service = LayoutService("layouts")
settings_service = SettingsService("config", "settings.json")
auth_service = AuthService("config", "users.json")

# Ein globales Dict zur Speicherung von Fortschrittsinformationen
progress_data = {}

# Add auth middleware
auth_middleware = AuthMiddleware(auth_service=auth_service)

# Middleware zum Stack hinzufügen
@app.middleware("http")
async def auth_middleware_handler(request, call_next):
    return await auth_middleware(request, call_next)

# Helfer-Funktion zum Aktualisieren des Fortschritts
def update_progress(job_id, percentage, message=None):
    # Initialisieren, falls der Job-Eintrag noch nicht existiert
    if job_id not in progress_data:
        progress_data[job_id] = {
            "percentage": 0,
            "message": "Initializing",
            "timestamp": datetime.now().isoformat(),
            "history": []  # Für die Speicherung aller Updates
        }
    
    # Aktuelles Update zum Verlauf hinzufügen
    update = {
        "percentage": percentage,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    # Aktuellen Status aktualisieren
    progress_data[job_id]["percentage"] = percentage
    progress_data[job_id]["message"] = message
    progress_data[job_id]["timestamp"] = update["timestamp"]
    
    # Update zur Historie hinzufügen
    if "history" not in progress_data[job_id]:
        progress_data[job_id]["history"] = []
    progress_data[job_id]["history"].append(update)
    
    logger.debug(f"Progress updates for {job_id}: {str(percentage)}")
    
    # Alte Jobs nach einer Weile löschen (z.B. nach 30 Minuten)
    current_time = datetime.now()
    for job in list(progress_data.keys()):
        job_time = datetime.fromisoformat(progress_data[job]["timestamp"])
        if (current_time - job_time).total_seconds() > 1800:  # 30 Minuten
            del progress_data[job]

# Include routers
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(dashboard_router)
app.include_router(template_router)
app.include_router(layout_router)
app.include_router(report_router)
app.include_router(schedule_router)
app.include_router(settings_router)

@app.on_event("startup")
async def startup_event():
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s"))
    logging.getLogger("uvicorn").addHandler(handler)
    logging.getLogger("uvicorn.error").addHandler(handler)
    logging.getLogger("uvicorn.access").addHandler(handler)

    """Initialize services on startup"""
    logger.info(f"Starting Grafana PDF Reporter v{VERSION}...")
    try:
        # Load settings
        app_settings = settings_service.get_decrypted_settings()
        logger.info("Application settings loaded")
        
        # Check if migration is needed and perform it if necessary
        if "grafana_servers" not in app_settings:
            logger.info("Migrating settings to multi-server format...")
            if settings_service.migrate_legacy_settings():
                logger.info("Successfully migrated settings to multi-server format")
                # Reload settings after migration
                app_settings = settings_service.get_decrypted_settings()
        
        # Initialize Grafana service with multi-server support
        global grafana_service
        grafana_service = GrafanaService()
        
        # Default server ID to use for migrations
        default_server_id = None
        
        if "grafana_servers" in app_settings:
            if grafana_service.initialize_from_settings(app_settings):
                logger.debug("Grafana service initialized with multiple servers")
                # Get the current server ID for migrations
                default_server_id = grafana_service.get_current_server_id()
            else:
                logger.warning("Failed to initialize Grafana service with servers from settings")
                # Try to initialize with legacy settings as fallback
                if "grafana" in app_settings:
                    grafana_settings = app_settings["grafana"]
                    logger.debug("Attempting to initialize with legacy Grafana settings")
                    grafana_service = GrafanaService(
                        base_url=grafana_settings.get("url"),
                        grafana_username=grafana_settings.get("username"),
                        grafana_password=grafana_settings.get("password")
                    )
        else:
            # Legacy code path in case migration failed
            grafana_settings = app_settings.get("grafana", {})
            logger.info(f"Using legacy Grafana settings")
            grafana_service = GrafanaService(
                base_url=grafana_settings.get("url"),
                grafana_username=grafana_settings.get("username"),
                grafana_password=grafana_settings.get("password")
            )
        
        # Migrate layouts and schedules to include server_id if needed
        layout_service.migrate_layouts_to_server_id(default_server_id)
        
        # Wait for layout migration to complete before migrating schedules
        # as schedules may reference layouts for server_id
        scheduler_service.migrate_schedules_to_server_id(default_server_id)
        
        # Get email settings
        email_settings = app_settings.get("email", {})
        
        # Initialize and activate schedules with email settings
        scheduler_service.initialize(
            grafana_service, 
            template_service, 
            layout_service,
            email_settings=email_settings
        )
        
        logger.info(f"Grafana PDF Reporter v{VERSION} started successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("Shutting down application...")
    try:
        await scheduler_service.shutdown()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Add error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)},
        headers=exc.headers,
    )