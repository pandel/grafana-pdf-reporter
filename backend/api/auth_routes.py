import os
import sys
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

# Import our auth service
from services.auth_service import AuthService

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


# Initialize router
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Initialize auth service
auth_service = AuthService()

# OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# Request/Response models
class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False
    display_name: Optional[str] = None
    auth_type: str = "internal"

class UserUpdate(BaseModel):
    password: Optional[str] = None
    is_admin: Optional[bool] = None
    display_name: Optional[str] = None
    auth_type: Optional[str] = None

class UserResponse(BaseModel):
    username: str
    is_admin: bool
    display_name: Optional[str] = None
    auth_type: str = "internal"
    created: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class SetupStatus(BaseModel):
    needs_setup: bool

class PasswordChange(BaseModel):
    current_password: str
    new_password: str


# Dependency to get current user from token
async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    user = auth_service.verify_token(token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Dependency to check admin access
async def get_admin_user(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions"
        )
    return current_user

# Change password endpoint
@router.post("/change-password")
async def change_password(
    password_data: PasswordChange, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Change the password of the current user"""
    logger.debug(f"Password change request for user: {current_user['username']}")
    
    # Verify current password
    user_info = auth_service.authenticate(current_user['username'], password_data.current_password)
    if not user_info:
        logger.warning(f"Invalid current password for user: {current_user['username']}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Change password
    success = auth_service.change_password(
        current_user['username'], 
        password_data.new_password
    )
    
    if not success:
        logger.error(f"Failed to change password for user: {current_user['username']}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )
    
    logger.info(f"Password changed successfully for user: {current_user['username']}")
    return {"message": "Password changed successfully"}

# Check if setup is needed
@router.get("/setup-status")
async def check_setup_status():
    """Check if initial setup is needed (no users exist)"""
    logger.debug("Checking setup status")
    try:
        needs_setup = auth_service.is_first_time_setup()
        return {"needs_setup": needs_setup}
    except Exception as e:
        logger.error(f"Error checking setup status: {str(e)}")
        # Bei Fehler (z.B. Dateizugriffsprobleme) gehen wir davon aus, dass Setup benötigt wird
        return {"needs_setup": True, "error": str(e)}

# Initial setup endpoint
@router.post("/setup", response_model=Token)
async def setup(user: UserCreate):
    """Setup initial admin user (only works if no users exist)"""
    logger.debug(f"Setting up initial user: {user.username}")
    
    # Check if it's first time setup
    if not auth_service.is_first_time_setup():
        logger.warning("Setup attempted but users already exist")
        raise HTTPException(
            status_code=403,
            detail="Setup already completed"
        )
    
    # Create user
    try:
        success = auth_service.create_user(user.username, user.password, user.is_admin)
        if not success:
            logger.error("Failed to create user during setup")
            raise HTTPException(
                status_code=500,
                detail="Failed to create user. Please check server logs for details."
            )
        
        # Authenticate user and generate token
        user_info = auth_service.authenticate(user.username, user.password)
        if not user_info:
            logger.error("Failed to authenticate newly created user")
            raise HTTPException(
                status_code=500,
                detail="Failed to authenticate user after creation"
            )
        
        # Return token
        token = auth_service.generate_token(user_info)
        logger.info(f"Setup completed successfully for user: {user.username}")
        return {"access_token": token}
    except Exception as e:
        logger.error(f"Unexpected error during setup: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Setup failed: {str(e)}"
        )

# Login endpoint
@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token"""
    logger.debug(f"Login attempt for user: {form_data.username}")
    
    # Authenticate user
    user_info = auth_service.authenticate(form_data.username, form_data.password)
    if not user_info:
        logger.warning(f"Login failed for user: {form_data.username}")
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate token
    token = auth_service.generate_token(user_info)
    logger.info(f"Login successful for user: {form_data.username}")
    return {"access_token": token}

# Get current user info
@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user info"""
    logger.debug(f"Getting info for user: {current_user['username']}")
    return current_user

# Admin endpoint to list all users
@router.get("/users", response_model=Dict[str, Any])
async def get_users(admin_user: Dict[str, Any] = Depends(get_admin_user)):
    """Get all users (admin only)"""
    logger.debug(f"Admin {admin_user['username']} requesting user list")
    return auth_service.get_users()

# Admin endpoint to create a new user
@router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, admin_user: Dict[str, Any] = Depends(get_admin_user)):
    """Create a new user (admin only)"""
    logger.debug(f"Admin {admin_user['username']} creating new user: {user.username}")
    logger.debug(f"User data received: {user.dict()}")     
    # Create user
    success = auth_service.create_user(
        user.username, 
        user.password, 
        user.is_admin,
        user.auth_type
    )
    
    if not success:
        logger.error(f"Failed to create user: {user.username}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create user"
        )
    
    # Update additional fields if provided
    if user.display_name:
        auth_service.update_user(
            user.username,
            {"display_name": user.display_name},
            admin_user["username"]
        )
    
    # Return user info
    user_info = auth_service.get_user(user.username)
    if not user_info:
        raise HTTPException(
            status_code=404,
            detail="User created but could not be retrieved"
        )
    
    logger.info(f"User {user.username} created successfully")
    return user_info

# Admin endpoint to update a user
@router.put("/users/{username}", response_model=UserResponse)
async def update_user(
    username: str, 
    user: UserUpdate, 
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    """Update a user (admin only)"""
    logger.debug(f"Admin {admin_user['username']} updating user: {username}")
    
    # Update user
    success = auth_service.update_user(
        username,
        user.dict(exclude_unset=True),
        admin_user["username"]
    )
    
    if not success:
        logger.error(f"Failed to update user: {username}")
        raise HTTPException(
            status_code=404,
            detail="User not found or could not be updated"
        )
    
    # Return updated user info
    user_info = auth_service.get_user(username)
    if not user_info:
        raise HTTPException(
            status_code=404,
            detail="User updated but could not be retrieved"
        )
    
    logger.info(f"User {username} updated successfully")
    return user_info

# Admin endpoint to delete a user
@router.delete("/users/{username}")
async def delete_user(
    username: str, 
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    """Delete a user (admin only)"""
    logger.debug(f"Admin {admin_user['username']} deleting user: {username}")
    
    # Delete user
    success = auth_service.delete_user(username, admin_user["username"])
    
    if not success:
        logger.error(f"Failed to delete user: {username}")
        raise HTTPException(
            status_code=404,
            detail="User not found or could not be deleted"
        )
    
    logger.info(f"User {username} deleted successfully")
    return {"status": "success", "message": f"User {username} deleted successfully"}

# Get specific user info (admin only)
@router.get("/users/{username}", response_model=UserResponse)
async def get_user_info(
    username: str, 
    admin_user: Dict[str, Any] = Depends(get_admin_user)
):
    """Get specific user info (admin only)"""
    logger.debug(f"Admin {admin_user['username']} getting user info: {username}")
    
    user_info = auth_service.get_user(username)
    if not user_info:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    return user_info

# Dependency to get current user from token
async def get_current_user(request: Request) -> Dict[str, Any]:
    """Get the current user from the request's state or token"""
    # If user is already in request state (set by middleware)
    if hasattr(request.state, 'user'):
        return request.state.user
    
    # Otherwise get from token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header.split(" ")[1]
    user = auth_service.verify_token(token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user