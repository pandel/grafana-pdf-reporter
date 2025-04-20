import os
import sys
import re
import logging
import json
from typing import List, Pattern, Dict, Any, Optional, Callable, Union
from fastapi import Request, status
from fastapi.responses import JSONResponse

from services.auth_service import AuthService

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class AuthMiddleware:
    """Middleware to handle authentication for protected routes"""
    
    def __init__(
        self, 
            auth_service: AuthService,
            public_paths: List[Union[str, Pattern]] = None,
            setup_check_path: str = "/api/auth/setup-status",
            admin_only_paths: List[str] = None
        ):
        """
        Initialize Auth Middleware
        
        Args:
            auth_service: Authentication service instance
            public_paths: List of paths that don't require authentication
            setup_check_path: Path to check if setup is needed
        """
        self.auth_service = auth_service
        self.public_paths = public_paths or []
        self.setup_check_path = setup_check_path
        
        # Always add common public paths
        default_public = [
            "/api/health",
            "/api/auth/token",
            "/api/auth/setup",
            setup_check_path,
            "/api/settings/initialized",
            "/api/docs",
            "/api/openapi.json"
        ]
        
        for path in default_public:
            if path not in self.public_paths:
                self.public_paths.append(path)
        
        self.admin_only_paths = admin_only_paths or [
            "/api/settings",
            "/api/auth/users"
        ]
        
        # Routes, die Besitzprüfung benötigen
        self.ownership_paths = {
            r"/api/layouts/([^/]+)": self._check_layout_ownership,
            r"/api/schedules/([^/]+)": self._check_schedule_ownership,
            # Weitere Pfade nach Bedarf
        }
        
        logger.info(f"Auth middleware initialized with {len(self.public_paths)} public paths")
        logger.info(f"Auth middleware initialized with {len(self.admin_only_paths)} admin-only paths")   

    async def __call__(self, request: Request, call_next):
        """Process the request"""
        path = request.url.path
        method = request.method

        # Check if path is public
        if self._is_public_path(path):
            logger.debug(f"Public path accessed: {path}")
            return await call_next(request)
        
        # Check if it's first time setup
        if self.auth_service.is_first_time_setup():
            logger.info("First time setup detected, allowing access")
            return await call_next(request)

        # Spezialbehandlung für Progress-Stream-Endpunkte
        if path.startswith("/api/progress/"):
            # Versuche Token aus URL-Parameter zu lesen
            token_param = request.query_params.get("token")
            
            if token_param:
                # Verifiziere Token aus URL-Parameter
                user_info = self.auth_service.verify_token(token_param)
                
                if user_info:
                    logger.debug(f"Authenticated access to {path} by user: {user_info['username']} (via URL token)")
                    return await call_next(request)
            
        # Check token and get user info
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning(f"Unauthorized access attempt to {path}: No valid Authorization header")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = auth_header.split(" ")[1]
        
        # Verify token
        user_info = self.auth_service.verify_token(token)
        if not user_info:
            logger.warning(f"Unauthorized access attempt to {path}: Invalid token")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if path requires admin permission
        for admin_path in self.admin_only_paths:
            if path.startswith(admin_path):
                # Check if user is admin
                if not user_info.get("is_admin", False):
                    logger.warning(f"Unauthorized admin access attempt to {path} by user: {user_info['username']}")
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "Admin permission required"}
                    )
                break
        
        # Check for paths requiring ownership validation 
        # Skip for admins, they can access everything
        if not user_info.get("is_admin", False) and method in ["PUT", "DELETE"]:
            for pattern, check_func in self.ownership_paths.items():
                match = re.match(pattern, path)
                if match:
                    resource_id = match.group(1)
                    ownership_result = await check_func(request, user_info, resource_id)
                    
                    if not ownership_result:
                        logger.warning(f"Ownership check failed for {path} by user: {user_info['username']}")
                        return JSONResponse(
                            status_code=status.HTTP_403_FORBIDDEN,
                            content={"detail": "You don't have permission to modify this resource"}
                        )
                    break
        
        # Add user info to request state for use in endpoints
        request.state.user = user_info
        
        # Token is valid, continue with request
        logger.debug(f"Authenticated access to {path} by user: {user_info['username']}")
        return await call_next(request)
    
    def _is_public_path(self, path: str) -> bool:
        """Check if a path is public"""
        for public_path in self.public_paths:
            if isinstance(public_path, str) and path.startswith(public_path):
                return True
            elif hasattr(public_path, "match") and public_path.match(path):
                return True
        return False
    
    async def _check_layout_ownership(self, request: Request, user_info: Dict[str, Any], layout_id: str) -> bool:
        """
        Check if user owns the layout
        
        Args:
            request: FastAPI request
            user_info: User information
            layout_id: Layout ID to check
            
        Returns:
            True if user owns the layout or is admin, False otherwise
        """
        # Admins can access any layout
        if user_info.get("is_admin", False):
            return True
        
        # Read the layout file
        from services.layout_service import LayoutService
        layout_service = LayoutService("layouts")
        layout = layout_service.get_layout(layout_id)
        
        if not layout:
            return False
        
        # Check if user is the creator
        created_by = layout.get("created_by", None)
        return created_by == user_info["username"]

    async def _check_schedule_ownership(self, request: Request, user_info: Dict[str, Any], schedule_id: str) -> bool:
        """
        Check if user owns the schedule
        
        Args:
            request: FastAPI request
            user_info: User information
            schedule_id: Schedule ID to check
            
        Returns:
            True if user owns the schedule or is admin, False otherwise
        """
        # Admins can access any schedule
        if user_info.get("is_admin", False):
            return True
        
        # Read the schedule file
        from services.scheduler_service import SchedulerService
        scheduler_service = SchedulerService("schedules")
        schedule = scheduler_service.get_schedule(schedule_id)
        
        if not schedule:
            return False
        
        # Check if user is the creator
        created_by = schedule.get("created_by", None)
        return created_by == user_info["username"]