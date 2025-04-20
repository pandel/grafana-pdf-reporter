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

class TemplateService:
    """Service to manage report templates"""
    
    def __init__(self, templates_dir: str):
        """
        Initialize Template Service
        
        Args:
            templates_dir: Directory to store template files
        """
        self.templates_dir = templates_dir
        
        # Create templates directory if it doesn't exist
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
        
        # Create default template if none exists
        if len(self.get_all_templates()) == 0:
            self._create_default_template()
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """
        Get all available templates
        
        Returns:
            List of templates with id and name
        """
        templates = []
        
        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".json"):
                template_id = filename[:-5]  # Remove .json extension
                template_path = os.path.join(self.templates_dir, filename)
                
                try:
                    with open(template_path, 'r') as f:
                        template_data = json.load(f)
                        templates.append({
                            "id": template_id,
                            "name": template_data.get("name", "Unnamed Template"),
                            "created": template_data.get("created", ""),
                            "modified": template_data.get("modified", "")
                        })
                except Exception as e:
                    logger.error(f"Error reading template {template_id}: {str(e)}")
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific template by ID
        
        Args:
            template_id: Template ID
            
        Returns:
            Template data or None if not found
        """
        template_path = os.path.join(self.templates_dir, f"{template_id}.json")
        
        if not os.path.exists(template_path):
            logger.error(f"File not accessible: {template_path}")
            return None
        
        try:
            with open(template_path, 'r') as f:
                logger.info(f"Reading template JSON file: {template_path}")
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading template {template_id}: {str(e)}")
            return None
    
    def create_template(self, template_data: Dict[str, Any]) -> str:
        """
        Create a new template
        
        Args:
            template_data: Template configuration
            
        Returns:
            ID of the created template
        """
        template_id = str(uuid.uuid4())
        
        # Add metadata
        now = datetime.now().isoformat()
        template_data["created"] = now
        template_data["modified"] = now
        
        template_path = os.path.join(self.templates_dir, f"{template_id}.json")
        
        with open(template_path, 'w') as f:
            json.dump(template_data, f, indent=2)
        
        return template_id
    
    def update_template(self, template_id: str, template_data: Dict[str, Any]) -> bool:
        """
        Update an existing template
        
        Args:
            template_id: Template ID
            template_data: New template configuration
            
        Returns:
            True if successful, False if template not found
        """
        template_path = os.path.join(self.templates_dir, f"{template_id}.json")
        
        if not os.path.exists(template_path):
            return False
        
        # Preserve creation date but update modified date
        try:
            with open(template_path, 'r') as f:
                existing_data = json.load(f)
                template_data["created"] = existing_data.get("created", datetime.now().isoformat())
        except Exception:
            template_data["created"] = datetime.now().isoformat()
        
        template_data["modified"] = datetime.now().isoformat()
        
        with open(template_path, 'w') as f:
            json.dump(template_data, f, indent=2)
        
        return True
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template
        
        Args:
            template_id: Template ID
            
        Returns:
            True if successful, False if template not found
        """
        # Don't allow deleting default template
        if template_id == "default":
            return False
        
        template_path = os.path.join(self.templates_dir, f"{template_id}.json")
        
        if not os.path.exists(template_path):
            return False
        
        os.remove(template_path)
        return True
    
    def get_default_template(self) -> Dict[str, Any]:
        """
        Get the default template
        
        Returns:
            Default template configuration
        """
        default_template = self.get_template("default")
        
        if not default_template:
            # Recreate default template if it's missing
            self._create_default_template()
            default_template = self.get_template("default")
        
        return default_template
    
    def _create_default_template(self):
        """Create a default template"""
        default_template = {
            "name": "Default Template",
            "header": {
                "title": "Grafana Report",
                "logoUrl": "",
                "backgroundColor": "#BCAAA4",
                "textColor": "#000000",
                "height": 15
            },
            "footer": {
                "text": "Generated with Grafana Report Generator",
                "pageNumberFormat": "Page (page) of (total)",
                "backgroundColor": "#ECEFF1",
                "textColor": "#000000",
                "height": 10
            },
            "page": {
                "size": "A4",
                "orientation": "landscape",
                "marginTop": 20,
                "marginBottom": 20,
                "marginLeft": 20,
                "marginRight": 20
            }
        }
        
        # Save as default.json
        now = datetime.now().isoformat()
        default_template["created"] = now
        default_template["modified"] = now
        
        template_path = os.path.join(self.templates_dir, "default.json")
        
        with open(template_path, 'w') as f:
            json.dump(default_template, f, indent=2)
