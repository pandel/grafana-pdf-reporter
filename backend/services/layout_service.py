import os
import sys
import json
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

class LayoutService:
    """Service to manage saved report layouts"""
    
    def __init__(self, layouts_dir: str):
        """
        Initialize Layout Service
        
        Args:
            layouts_dir: Directory to store layout files
        """
        self.layouts_dir = layouts_dir
        
        # Create layouts directory if it doesn't exist
        if not os.path.exists(layouts_dir):
            os.makedirs(layouts_dir)
    
    def get_all_layouts(self) -> List[Dict[str, Any]]:
        """
        Get all available layouts
        
        Returns:
            List of layouts with id and name
        """
        layouts = []
        
        for filename in os.listdir(self.layouts_dir):
            if filename.endswith(".json"):
                layout_id = filename[:-5]  # Remove .json extension
                layout_path = os.path.join(self.layouts_dir, filename)
                
                try:
                    with open(layout_path, 'r') as f:
                        layout_data = json.load(f)
                        layouts.append({
                            "id": layout_id,
                            "name": layout_data.get("name", "Unnamed Layout"),
                            "description": layout_data.get("description", ""),
                            "organizationId": layout_data.get("organizationId"),
                            "created": layout_data.get("created", ""),
                            "modified": layout_data.get("modified", ""),
                            "created_by": layout_data.get("created_by", ""),
                            "modified_by": layout_data.get("modified_by", ""),
                            "server_id": layout_data.get("server_id")
                        })
                except Exception as e:
                    logger.error(f"Error reading layout {layout_id}: {str(e)}")
        
        return layouts
    
    def get_layout(self, layout_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific layout by ID
        
        Args:
            layout_id: Layout ID
            
        Returns:
            Layout data or None if not found
        """
        layout_path = os.path.join(self.layouts_dir, f"{layout_id}.json")
        
        if not os.path.exists(layout_path):
            logger.error(f"File not accessible: {layout_path}")
            return None
        
        try:
            with open(layout_path, 'r') as f:
                logger.info(f"Reading layout JSON file: {layout_path}")
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading layout {layout_id}: {str(e)}")
            return None
    
    def create_layout(self, layout_data: Dict[str, Any], username: str = None) -> str:
        """
        Create a new layout
        
        Args:
            layout_data: Layout configuration
            username: Username of creator (for ownership tracking)
            
        Returns:
            ID of the created layout
        """
        try:
            # Stellen Sie sicher, dass das Verzeichnis existiert
            if not os.path.exists(self.layouts_dir):
                logger.warning(f"Layout directory doesn't exist, creating: {self.layouts_dir}")
                os.makedirs(self.layouts_dir)
            
            layout_id = str(uuid.uuid4())
            logger.info(f"Generated new layout ID: {layout_id}")
            
            # Add metadata
            now = datetime.now().isoformat()
            layout_data["created"] = now
            layout_data["modified"] = now
            
            # Add creator information if provided
            if username:
                layout_data["created_by"] = username
                layout_data["modified_by"] = username
            
            # Ensure server_id is present (even if null)
            if "server_id" not in layout_data:
                layout_data["server_id"] = None
                
            layout_path = os.path.join(self.layouts_dir, f"{layout_id}.json")
            logger.info(f"Saving layout to path: {layout_path}")
            
            # Debug output
            logger.debug(f"Layout data to save: {json.dumps(layout_data, indent=2)}")
            
            # Check if path is writable
            dir_writable = os.access(self.layouts_dir, os.W_OK)
            logger.info(f"Directory {self.layouts_dir} is writable: {dir_writable}")
            
            # Attempt to write the file
            with open(layout_path, 'w') as f:
                json.dump(layout_data, f, indent=2)
                logger.info(f"Successfully saved layout to {layout_path}")
            
            # Verify file was created
            if os.path.exists(layout_path):
                logger.info(f"Verified: Layout file exists at {layout_path}")
            else:
                logger.error(f"File wasn't created at {layout_path}")
                    
            return layout_id
        except Exception as e:
            logger.error(f"Error creating layout: {str(e)}")
            # Raise error to be handled by API
            raise

    def update_layout(self, layout_id: str, layout_data: Dict[str, Any], username: str = None) -> bool:
        """
        Update an existing layout
        
        Args:
            layout_id: Layout ID
            layout_data: New layout configuration
            username: Username of modifier (for ownership tracking)
            
        Returns:
            True if successful, False if layout not found
        """
        layout_path = os.path.join(self.layouts_dir, f"{layout_id}.json")
        
        if not os.path.exists(layout_path):
            return False
        
        # Preserve creation date and creator but update modified date and modifier
        try:
            with open(layout_path, 'r') as f:
                existing_data = json.load(f)
                layout_data["created"] = existing_data.get("created", datetime.now().isoformat())
                layout_data["created_by"] = existing_data.get("created_by", username)
        except Exception:
            layout_data["created"] = datetime.now().isoformat()
            layout_data["created_by"] = username
        
        layout_data["modified"] = datetime.now().isoformat()
        if username:
            layout_data["modified_by"] = username
        
        with open(layout_path, 'w') as f:
            json.dump(layout_data, f, indent=2)
        
        return True
    
    def delete_layout(self, layout_id: str) -> bool:
        """
        Delete a layout
        
        Args:
            layout_id: Layout ID
            
        Returns:
            True if successful, False if layout not found
        """
        layout_path = os.path.join(self.layouts_dir, f"{layout_id}.json")
        
        if not os.path.exists(layout_path):
            return False
        
        os.remove(layout_path)
        return True
    
    def migrate_layouts_to_server_id(self, default_server_id: str = None) -> bool:
        """
        Migrate existing layouts to include server_id
        
        Args:
            default_server_id: Default server ID to assign (if None, layouts will have null server_id)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            count = 0
            for filename in os.listdir(self.layouts_dir):
                if filename.endswith(".json"):
                    layout_path = os.path.join(self.layouts_dir, filename)
                    
                    try:
                        with open(layout_path, 'r') as f:
                            layout_data = json.load(f)
                        
                        # Check if migration is needed
                        if "server_id" not in layout_data:
                            layout_data["server_id"] = default_server_id
                            
                            # Save updated layout
                            with open(layout_path, 'w') as f:
                                json.dump(layout_data, f, indent=2)
                            
                            count += 1
                    except Exception as e:
                        logger.error(f"Error migrating layout {filename}: {str(e)}")
            
            logger.info(f"Migrated {count} layouts to include server_id")
            return True
        except Exception as e:
            logger.error(f"Error migrating layouts: {str(e)}")
            return False