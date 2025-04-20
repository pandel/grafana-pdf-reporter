import os
import sys
import json
import uuid
import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from io import BytesIO
import logging
import shutil

# Replace aiocron with APScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore

# Create PDF generator directly instead of using the factory
from services.pdf_generator import PDFGenerator

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

logging.getLogger('apscheduler').setLevel(os.environ.get('LOGLEVEL', 'WARNING').upper())
logging.getLogger('apscheduler').addHandler(stream_handler)

class SchedulerService:
    """Service to manage scheduled reports"""
    
    def __init__(self, schedules_dir: str = "schedules"):
        """
        Initialize Scheduler Service
        
        Args:
            schedules_dir: Directory to store schedule files
        """
        self.schedules_dir = schedules_dir
        self.active_jobs = {}  # Dictionary to track active scheduled jobs
        self.grafana_service = None
        self.template_service = None
        self.layout_service = None
        self.email_settings = {}  # Store email settings from application config
        
        # Job queue and processing
        self.job_queue = []  # Simple list as a queue
        self.currently_running_job = None  # Track currently running job

        # Initialize the APScheduler
        self.scheduler = AsyncIOScheduler(
            jobstores={
                    'default': MemoryJobStore()
                }
        )

        # Add a job to regularly check and process the queue
        self.scheduler.add_job(
            self._process_queue,
            'interval',
            seconds=15,  # Check every 15 seconds
            id='queue_processor',
            replace_existing=True
        )
    
        # Create schedules directory if it doesn't exist
        if not os.path.exists(schedules_dir):
            os.makedirs(schedules_dir)
    
    def initialize(self, grafana_service, template_service, layout_service, email_settings=None):
        """
        Initialize the scheduler with required services
        
        Args:
            grafana_service: GrafanaService instance
            template_service: TemplateService instance
            layout_service: LayoutService instance
            email_settings: Optional email settings from application config
        """
        self.grafana_service = grafana_service
        self.template_service = template_service
        self.layout_service = layout_service
                
        if email_settings:
            self.email_settings = email_settings
            logger.info("Email settings loaded into SchedulerService")
        
        # Start the scheduler
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("APScheduler started")
        
        # Load and activate all schedules
        schedules = self.get_all_schedules()
        for schedule in schedules:
            if schedule.get('status') == 'active':
                self.activate_schedule(schedule["id"])

    def update_email_settings(self, email_settings):
        """
        Update email settings
        
        Args:
            email_settings: New email settings dictionary
        """
        self.email_settings = email_settings
        logger.info("Email settings updated in SchedulerService")

    async def shutdown(self):
        """Clean up active jobs on shutdown"""
        # Clear the job queue
        self.job_queue = []
        
        # Shutdown the scheduler
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("APScheduler shutdown complete")
    
    def get_all_schedules(self) -> List[Dict[str, Any]]:
        """
        Get all scheduled reports
        
        Returns:
            List of schedules with id and name
        """
        schedules = []
        
        for filename in os.listdir(self.schedules_dir):
            if filename.endswith(".json"):
                schedule_id = filename[:-5]  # Remove .json extension
                schedule_path = os.path.join(self.schedules_dir, filename)
                
                try:
                    with open(schedule_path, 'r') as f:
                        schedule_data = json.load(f)
                        schedules.append({
                            "id": schedule_id,
                            "name": schedule_data.get("name", "Unnamed Schedule"),
                            "created": schedule_data.get("created", ""),
                            "modified": schedule_data.get("modified", ""),
                            "lastRun": schedule_data.get("lastRun"),
                            "nextRun": schedule_data.get("nextRun"),
                            "status": schedule_data.get("status", "active"),
                            "layoutId": schedule_data.get("layoutId"),
                            "schedule": schedule_data.get("schedule", {}),
                            "created_by": schedule_data.get("created_by", ""),
                            "modified_by": schedule_data.get("modified_by", ""),
                            "server_id": schedule_data.get("server_id")
                        })
                except Exception as e:
                    logger.error(f"Error reading schedule {schedule_id}: {str(e)}")
        
        return schedules
    
    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific schedule by ID
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            Schedule data or None if not found
        """
        schedule_path = os.path.join(self.schedules_dir, f"{schedule_id}.json")
        
        if not os.path.exists(schedule_path):
            return None
        
        try:
            with open(schedule_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading schedule {schedule_id}: {str(e)}")
            return None
    
    def create_schedule(self, schedule_data: Dict[str, Any], username: str = None) -> str:
        """
        Create a new scheduled report
        
        Args:
            schedule_data: Schedule configuration
            username: Username of creator (for ownership tracking)
            
        Returns:
            ID of the created schedule
        """
        schedule_id = str(uuid.uuid4())
        
        # Add metadata
        now = datetime.now().isoformat()
        schedule_data["created"] = now
        schedule_data["modified"] = now
        
        # Add creator information if provided
        if username:
            schedule_data["created_by"] = username
            schedule_data["modified_by"] = username
        
        # Add default status if not present
        if "status" not in schedule_data:
            schedule_data["status"] = "active"
            
        schedule_data["lastRun"] = None
        schedule_data["nextRun"] = None
        
        schedule_path = os.path.join(self.schedules_dir, f"{schedule_id}.json")
        
        with open(schedule_path, 'w') as f:
            json.dump(schedule_data, f, indent=2)
        
        return schedule_id

    def update_schedule(self, schedule_id: str, schedule_data: Dict[str, Any], username: str = None) -> bool:
        """
        Update an existing schedule
        
        Args:
            schedule_id: Schedule ID
            schedule_data: New schedule configuration
            username: Username of modifier (for ownership tracking)
            
        Returns:
            True if successful, False if schedule not found
        """
        schedule_path = os.path.join(self.schedules_dir, f"{schedule_id}.json")
        
        if not os.path.exists(schedule_path):
            return False
        
        # Preserve creation date and creator but update modified date and modifier
        try:
            with open(schedule_path, 'r') as f:
                existing_data = json.load(f)
                schedule_data["created"] = existing_data.get("created", datetime.now().isoformat())
                schedule_data["created_by"] = existing_data.get("created_by", username)
                schedule_data["lastRun"] = existing_data.get("lastRun")
                schedule_data["nextRun"] = existing_data.get("nextRun")

                # Preserve the history when updating
                if "history" in existing_data:
                    schedule_data["history"] = existing_data["history"]
        except Exception:
            schedule_data["created"] = datetime.now().isoformat()
            schedule_data["created_by"] = username
        
        schedule_data["modified"] = datetime.now().isoformat()
        if username:
            schedule_data["modified_by"] = username
        
        with open(schedule_path, 'w') as f:
            json.dump(schedule_data, f, indent=2)
        
        # Update the active job if it exists
        job_id = f"schedule_{schedule_id}"
        
        if job_id in self.active_jobs:
            # Remove the existing job
            self.scheduler.remove_job(job_id)
            self.active_jobs.pop(job_id)
            
            # Add the job again if active
            if schedule_data.get("status") == "active":
                self.activate_schedule(schedule_id)
        elif schedule_data.get("status") == "active":
            self.activate_schedule(schedule_id)
        
        return True
    
    def delete_schedule(self, schedule_id: str) -> bool:
        """
        Delete a schedule
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            True if successful, False if schedule not found
        """
        schedule_path = os.path.join(self.schedules_dir, f"{schedule_id}.json")
        
        if not os.path.exists(schedule_path):
            return False
        
        # Stop the active job if it exists
        job_id = f"schedule_{schedule_id}"
        if job_id in self.active_jobs:
            self.scheduler.remove_job(job_id)
            self.active_jobs.pop(job_id)
        
        os.remove(schedule_path)
        return True
    
    def activate_schedule(self, schedule_id: str) -> bool:
        """
        Activate a scheduled report
        
        Args:
            schedule_id: Schedule ID
            
        Returns:
            True if successful, False if schedule not found or inactive
        """
        schedule_data = self.get_schedule(schedule_id)
        
        if not schedule_data:
            logger.error(f"Schedule {schedule_id} not found")
            return False
        
        if schedule_data.get("status") != "active":
            logger.info(f"Schedule {schedule_id} is not active")
            return False
        
        # Check if there is a valid email server configured
        if not self._has_valid_email_config(schedule_data):
            logger.warning(f"Schedule {schedule_id} cannot be activated: No valid mail server configured")
            return False
        
        # Extract cron expression
        cron_expression = schedule_data.get("schedule", {}).get("cronExpression")
        if not cron_expression:
            logger.error(f"No cron expression found for schedule {schedule_id}")
            return False
        
        # Parse cron expression
        try:
            # Convert cron expression to APScheduler format
            # Traditional cron: minute hour day_of_month month day_of_week
            minute, hour, day, month, day_of_week = cron_expression.split()
            
            # Create an APScheduler cron trigger
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )
            
            # Job ID to keep track of this schedule
            job_id = f"schedule_{schedule_id}"
            
            # Remove job if it already exists (for updates)
            if job_id in self.active_jobs:
                self.scheduler.remove_job(job_id)
            
            try:
                # Add the job to the scheduler, but set it to queue the job instead of running directly
                job = self.scheduler.add_job(
                    self._queue_scheduled_report,  # This now just queues the job instead of running it
                    trigger=trigger,
                    id=job_id,
                    args=[schedule_id],
                    replace_existing=True
                )
            except Exception as e:
                logger.error(f"Error adding job to scheduler {schedule_id}: {str(e)}")
                return False
            
            # Store the job
            self.active_jobs[job_id] = job
            
            # Update nextRun in the schedule file
            next_run_time = job.next_run_time
            if next_run_time:
                schedule_data["nextRun"] = next_run_time.isoformat()
                self._save_schedule(schedule_id, schedule_data)
            
            logger.info(f"Schedule {schedule_id} activated with cron expression: {cron_expression}")
            return True
        except Exception as e:
            logger.error(f"Error activating schedule {schedule_id}: {str(e)}")
            return False
            
    def _has_valid_email_config(self, schedule_data: Dict[str, Any]) -> bool:
        """
        Check if a valid email configuration exists
        
        Args:
            schedule_data: Schedule data to check
            
        Returns:
            True if a valid email configuration exists, False otherwise
        """
        # Check if email is enabled for this schedule
        email_config = schedule_data.get("schedule", {}).get("email", {})
        if not email_config or not email_config.get("enabled", False):
            logger.info("Email sending is disabled for this schedule")
            return True  # If email is disabled, no mail server is needed
        
        # Check for SMTP server in schedule-specific config or global settings
        smtp_server = email_config.get("smtpServer") or self.email_settings.get("server", "")
        
        if not smtp_server:
            logger.warning("No SMTP server configured in schedule or global settings")
            return False
        
        return True    

    async def _run_scheduled_report(self, schedule_id: str):
        """
        Run a scheduled report
        
        Args:
            schedule_id: Schedule ID
        """
        if not self.grafana_service or not self.template_service or not self.layout_service:
            logger.error(f"Services not initialized, cannot run schedule {schedule_id}")
            return
        
        logger.info(f"Running scheduled report {schedule_id}")
        schedule_data = self.get_schedule(schedule_id)
        
        if not schedule_data:
            logger.error(f"Schedule {schedule_id} not found")
            return
        
        # Initialize history entry
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "status": "started",
            "message": "Report generation started"
        }
        
        # Make sure the history list exists
        if "history" not in schedule_data:
            schedule_data["history"] = []
        
        # Add initial history entry
        schedule_data["history"].append(history_entry)
        self._save_schedule(schedule_id, schedule_data)
        
        try:
            # Get layout data
            layout_id = schedule_data.get("layoutId")
            if not layout_id:
                logger.error(f"No layout ID specified for schedule {schedule_id}")
                # Update history entry with error
                history_entry["status"] = "error"
                history_entry["message"] = "No layout ID specified"
                self._update_history_entry(schedule_id, history_entry)
                return
                    
            layout_data = self.layout_service.get_layout(layout_id)
            if not layout_data:
                logger.error(f"Layout {layout_id} not found for schedule {schedule_id}")
                # Update history entry with error
                history_entry["status"] = "error"
                history_entry["message"] = f"Layout {layout_id} not found"
                self._update_history_entry(schedule_id, history_entry)
                return
            
            # Get report layout
            report_layout = layout_data
            
            # Get server_id from schedule or layout data
            server_id = schedule_data.get("server_id") or layout_data.get("server_id")
            if server_id:
                logger.info(f"Using server {server_id} for scheduled report")
            
            # Get template
            template_id = report_layout.get("templateId")
            template_config = {}
            
            if template_id:
                template_config = self.template_service.get_template(template_id)
                if not template_config:
                    logger.warning(f"Template {template_id} not found, using default")
                    template_config = self.template_service.get_default_template()
            else:
                template_config = self.template_service.get_default_template()
            
            # Switch to correct organization
            org_id = report_layout.get("organizationId")
            if org_id:
                self.grafana_service.switch_organization(org_id, server_id)
                logger.info(f"Switched to organization {org_id}")

            # Grafana version
            grafana_version = self.grafana_service.get_grafana_version(server_id)

            self.grafana_service.set_current_server(server_id)
            grafana_conn = self.grafana_service.get_connection_info()

            grafana_url = grafana_conn.get("url")
            grafana_username = grafana_conn.get("username")
            grafana_password = grafana_conn.get("password")
            
            logger.info(f"Creating PDF Generator with Grafana URL: {grafana_url}")
            
            # Create and initialize PDF generator
            pdf_generator = PDFGenerator(grafana_url, grafana_username, grafana_password)
            await pdf_generator.initialize()
            
            try:
                # Generate report with server_id if provided
                logger.info(f"Generating report for schedule {schedule_id} with layout {layout_id}")
                pdf_data = await pdf_generator.generate_report(
                    layout_config=report_layout,
                    template_config=template_config,
                    grafana_service=self.grafana_service,
                    server_id=server_id,
                    grafana_version=grafana_version
                )
                
                # Save PDF file in history
                timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                filename = f"{schedule_id}_{timestamp}.pdf"
                history_file_path = os.path.join(self.schedules_dir, "history", filename)
                
                # Ensure history directory exists
                history_dir = os.path.join(self.schedules_dir, "history")
                if not os.path.exists(history_dir):
                    os.makedirs(history_dir)
                
                # Save PDF to history
                with open(history_file_path, 'wb') as f:
                    pdf_data.seek(0)
                    shutil.copyfileobj(pdf_data, f)
                
                # Update history entry with success and file path
                history_entry["status"] = "completed"
                history_entry["message"] = "Report generated successfully"
                history_entry["file_path"] = filename
                
                # Send report via email if configured
                email_config = schedule_data.get("schedule", {}).get("email", {})
                if email_config and email_config.get("enabled", False):
                    logger.info(f"Sending email for schedule {schedule_id}")
                    try:
                        await self._send_report_email(
                            pdf_data=pdf_data,
                            schedule_name=schedule_data.get("name", "Grafana Report"),
                            email_config=email_config
                        )
                        history_entry["email_sent"] = True
                    except Exception as email_error:
                        logger.error(f"Error sending email: {str(email_error)}")
                        history_entry["email_sent"] = False
                        history_entry["email_error"] = str(email_error)
                
                # Update last run time
                updated_data = {
                    "lastRun": datetime.now().isoformat()
                }
                
                # Update next run time from job
                job_id = f"schedule_{schedule_id}"
                job = self.scheduler.get_job(job_id)
                if job and job.next_run_time:
                    updated_data["nextRun"] = job.next_run_time.isoformat()
                
                # Update history entry in schedule data
                self._update_history_entry(schedule_id, history_entry, updated_data)
                logger.info(f"Scheduled report {schedule_id} completed successfully")
            finally:
                # Make sure to close the PDF generator to release resources
                await pdf_generator.close()
                
        except Exception as e:
            # Update history entry with error
            history_entry["status"] = "error"
            history_entry["message"] = f"Error generating report: {str(e)}"
            self._update_history_entry(schedule_id, history_entry)
            logger.error(f"Error running scheduled report {schedule_id}: {str(e)}")

    # Füge diese neue Hilfsmethode hinzu
    def _update_history_entry(self, schedule_id: str, history_entry: Dict[str, Any], updated_data: Dict[str, Any] = None):
        """
        Update the latest history entry in a schedule
        
        Args:
            schedule_id: Schedule ID
            history_entry: Updated history entry
            updated_data: Additional data to update in the schedule
        """
        schedule_data = self.get_schedule(schedule_id)
        if not schedule_data:
            logger.error(f"Schedule {schedule_id} not found when updating history")
            return
        
        # Update additional data if provided
        if updated_data:
            for key, value in updated_data.items():
                schedule_data[key] = value
        
        # Make sure history exists
        if "history" not in schedule_data:
            schedule_data["history"] = []
        
        # Find and update the matching history entry by timestamp
        for i, entry in enumerate(schedule_data["history"]):
            if entry.get("timestamp") == history_entry.get("timestamp"):
                schedule_data["history"][i] = history_entry
                break
        else:
            # If no matching entry found, just add it
            schedule_data["history"].append(history_entry)
        
        # Limit history size to last 50 entries
        if len(schedule_data["history"]) > 50:
            schedule_data["history"] = schedule_data["history"][-50:]
        
        # Save updated schedule
        self._save_schedule(schedule_id, schedule_data)
    
    def _save_schedule(self, schedule_id: str, schedule_data: Dict[str, Any]):
        """
        Save schedule data to file
        
        Args:
            schedule_id: Schedule ID
            schedule_data: Schedule data to save
        """
        schedule_path = os.path.join(self.schedules_dir, f"{schedule_id}.json")
        
        with open(schedule_path, 'w') as f:
            json.dump(schedule_data, f, indent=2)
    
    async def _send_report_email(self, pdf_data: BytesIO, schedule_name: str, email_config: Dict[str, Any]):
        """
        Send report via email
        
        Args:
            pdf_data: PDF report as BytesIO
            schedule_name: Name of the schedule
            email_config: Email configuration from the schedule
        """
        # Extract email config
        recipients = email_config.get("recipients", [])
        if not recipients:
            logger.warning("No recipients specified, skipping email")
            return

        # Check if we should use Graph API
        use_graph_api = self.email_settings.get("useGraphAPI", False)
        
        if use_graph_api:
            # Send using Graph API
            await self._send_email_graph_api(
                pdf_data=pdf_data,
                recipients=recipients,
                subject=email_config.get("subject", f"Grafana Report: {schedule_name}"),
                body=email_config.get("body", f"Attached is your scheduled Grafana report: {schedule_name}"),
                filename=f"{schedule_name.replace(' ', '_')}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.pdf"
            )
        else:        
            # Use scheduler's email settings with overrides from schedule-specific config
            smtp_server = email_config.get("smtpServer") or self.email_settings.get("server", "")
            smtp_port = email_config.get("smtpPort") or self.email_settings.get("port", 587)
            smtp_user = email_config.get("smtpUser") or self.email_settings.get("username", "")
            smtp_password = email_config.get("smtpPassword") or self.email_settings.get("password", "")
            use_tls = email_config.get("useTLS", self.email_settings.get("useTLS", True))
            
            # Use sender from schedule, fallback to global config, then to SMTP username
            sender = email_config.get("sender") or self.email_settings.get("sender", smtp_user)
            
            subject = email_config.get("subject", f"Grafana Report: {schedule_name}")
            body = email_config.get("body", f"Attached is your scheduled Grafana report: {schedule_name}")
            
            # Log email settings (excluding password)
            logger.debug(f"Sending email using SMTP server: {smtp_server}:{smtp_port}, user: {smtp_user}, TLS: {use_tls}")
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)
            msg['Date'] = formatdate(localtime=True)
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body))
            
            # Add PDF attachment
            pdf_data.seek(0)
            attachment = MIMEBase('application', 'pdf')
            attachment.set_payload(pdf_data.read())
            encoders.encode_base64(attachment)
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = f"{schedule_name.replace(' ', '_')}-{timestamp}.pdf"
            attachment.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(attachment)
            
            # Send email
            try:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    if use_tls:
                        server.starttls()
                    
                    if smtp_user and smtp_password:
                        server.login(smtp_user, smtp_password)
                    
                    server.send_message(msg)
                    logger.info(f"Email sent to {', '.join(recipients)}")
                    
            except Exception as e:
                logger.error(f"Error sending email: {str(e)}")

    async def _send_email_graph_api(self, pdf_data: BytesIO, recipients: List[str], subject: str, body: str, filename: str):
        """
        Send report via Microsoft Graph API
        
        Args:
            pdf_data: PDF report as BytesIO
            recipients: List of email recipients
            subject: Email subject
            body: Email body
            filename: Attachment filename
        """
        try:
            import base64
            import msal
            import requests
            import json
            
            # Get Microsoft Graph settings
            tenant_id = self.email_settings.get("tenantId", "")
            client_id = self.email_settings.get("clientId", "")
            client_secret = self.email_settings.get("clientSecret", "")
            sender_email = self.email_settings.get("userEmail", "")
            
            # Get proxy settings
            use_proxy = self.email_settings.get("useProxy", False)
            proxy_url = self.email_settings.get("proxyUrl", "")
            proxy_port = self.email_settings.get("proxyPort", 8080)
            proxy_user = self.email_settings.get("proxyUser", "")
            proxy_password = self.email_settings.get("proxyPassword", "")
            verify_cert = self.email_settings.get("verifyCertGraphAPI", True)
            
            # Decrypt proxy password if it's encrypted
            if proxy_password and isinstance(proxy_password, str) and proxy_password.startswith("encrypted:"):
                # Import here to avoid circular import
                from services.encryption_service import EncryptionService
                encryption_service = EncryptionService()
                proxy_password = encryption_service.decrypt(proxy_password)
            
            if not tenant_id or not client_id or not client_secret or not sender_email:
                logger.error("Missing required Microsoft Graph API settings")
                return
            
            # Setup proxy configuration for MSAL
            # MSAL uses requests internally, so we need to prepare a proxies dict
            proxies = None
            if use_proxy and proxy_url:
                proxy_auth = ""
                if proxy_user and proxy_password:
                    proxy_auth = f"{proxy_user}:{proxy_password}@"
                
                proxy_scheme = "http"
                if proxy_url.startswith("http://") or proxy_url.startswith("https://"):
                    proxy_scheme = proxy_url.split("://")[0]
                    proxy_url = proxy_url.split("://")[1]
                
                proxy_string = f"{proxy_scheme}://{proxy_auth}{proxy_url}:{proxy_port}"
                proxies = {
                    "http": proxy_string,
                    "https": proxy_string
                }
                logger.info(f"Using proxy for Graph API: {proxy_scheme}://{proxy_url}:{proxy_port}")
            
            # Create MSAL app with proxy configuration
            # If using proxies and http_client is set, configure the session
            session=requests.Session()
            if not verify_cert:
                logger.debug(" Do not verify certificate")
                session.verify = False

            if proxies:
                logger.debug("Proxy assigned to MSAL Client")
                session.proxies = proxies
            
            app = msal.ConfidentialClientApplication(
                client_id=client_id,
                client_credential=client_secret,
                authority=f"https://login.microsoftonline.com/{tenant_id}",
                http_client=session if proxies else None
            )
            
            # Get token
            logger.debug("Acquiring token for Graph API")
            scopes = ['https://graph.microsoft.com/.default']
            result = app.acquire_token_for_client(scopes=scopes)
            
            if "access_token" not in result:
                logger.error(f"Failed to get Graph API token: {result.get('error_description')}")
                return
            
            # Prepare email with attachment
            token = result["access_token"]
            
            # Get PDF data and encode as base64
            pdf_data.seek(0)
            pdf_bytes = pdf_data.read()
            encoded_attachment = base64.b64encode(pdf_bytes).decode('utf-8')
            
            # Create email payload
            email_payload = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": "text",
                        "content": body
                    },
                    "toRecipients": [
                        {"emailAddress": {"address": email}} for email in recipients
                    ],
                    "attachments": [
                        {
                            "@odata.type": "#microsoft.graph.fileAttachment",
                            "name": filename,
                            "contentType": "application/pdf",
                            "contentBytes": encoded_attachment
                        }
                    ]
                },
                "saveToSentItems": "true"
            }
            
            # Send email using Graph API
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # Use the same proxy configuration for the direct Graph API call
            request_kwargs = {
                'headers': headers,
                'data': json.dumps(email_payload)
            }
            
            if proxies:
                request_kwargs['proxies'] = proxies
            
            response = requests.post(
                f'https://graph.microsoft.com/v1.0/users/{sender_email}/sendMail',
                **request_kwargs
            )
            
            if response.status_code >= 400:
                logger.error(f"Error sending email via Graph API: {response.status_code} - {response.text}")
            else:
                logger.info(f"Email sent successfully via Microsoft Graph API to {', '.join(recipients)}")
            
        except Exception as e:
            logger.error(f"Error sending email via Graph API: {str(e)}")

    def migrate_schedules_to_server_id(self, default_server_id: str = None) -> bool:
        """
        Migrate existing schedules to include server_id
        
        Args:
            default_server_id: Default server ID to assign (if None, schedules will have null server_id)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            count = 0
            for filename in os.listdir(self.schedules_dir):
                if filename.endswith(".json"):
                    schedule_path = os.path.join(self.schedules_dir, filename)
                    
                    try:
                        with open(schedule_path, 'r') as f:
                            schedule_data = json.load(f)
                        
                        # Check if migration is needed
                        if "server_id" not in schedule_data:
                            # Try to get server_id from associated layout
                            layout_id = schedule_data.get("layoutId")
                            if layout_id and self.layout_service:
                                try:
                                    layout = self.layout_service.get_layout(layout_id)
                                    if layout and "server_id" in layout:
                                        schedule_data["server_id"] = layout["server_id"]
                                    else:
                                        schedule_data["server_id"] = default_server_id
                                except Exception as layout_error:
                                    logger.error(f"Error getting layout for server_id: {str(layout_error)}")
                                    schedule_data["server_id"] = default_server_id
                            else:
                                schedule_data["server_id"] = default_server_id
                            
                            # Save updated schedule
                            with open(schedule_path, 'w') as f:
                                json.dump(schedule_data, f, indent=2)
                            
                            count += 1
                    except Exception as e:
                        logger.error(f"Error migrating schedule {filename}: {str(e)}")
            
            logger.info(f"Migrated {count} schedules to include server_id")
            return True
        except Exception as e:
            logger.error(f"Error migrating schedules: {str(e)}")
            return False

    # Synchrone Version der Queue-Einreihung
    def _queue_scheduled_report(self, schedule_id: str):
        """
        Queue a scheduled report for processing
        
        Args:
            schedule_id: Schedule ID to queue
        """
        logger.info(f"Queueing scheduled report {schedule_id}")
        
        # Update the schedule with queued status
        schedule_data = self.get_schedule(schedule_id)
        if schedule_data:
            # Initialize history entry
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "status": "queued",
                "message": "Report generation queued"
            }
            
            # Make sure the history list exists
            if "history" not in schedule_data:
                schedule_data["history"] = []
            
            # Add initial history entry
            schedule_data["history"].append(history_entry)
            self._save_schedule(schedule_id, schedule_data)
        
        # Add job to the queue if not already in queue
        if schedule_id not in self.job_queue:
            self.job_queue.append(schedule_id)
            logger.info(f"Job {schedule_id} added to queue. Queue length: {len(self.job_queue)}")
        else:
            logger.info(f"Job {schedule_id} already in queue")

    # Synchrone Methode zur Überprüfung und zum Start des nächsten Jobs
    def _process_queue(self):
        """
        Check the job queue and start the next job if none is running
        This is a synchronous method called by APScheduler
        """
        # Skip if no jobs in queue or a job is already running
        if not self.job_queue or self.currently_running_job:
            return
        
        # Get next job from queue
        schedule_id = self.job_queue.pop(0)
        self.currently_running_job = schedule_id
        logger.info(f"Starting queued job for schedule: {schedule_id}")
        
        # Starte einen neuen Thread für die asynchrone Verarbeitung
        import threading
        
        def run_async_job():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._run_report_and_cleanup(schedule_id))
            finally:
                loop.close()
        
        # Starte den Job in einem separaten Thread
        thread = threading.Thread(target=run_async_job)
        thread.daemon = True  # Daemon-Thread, um das Beenden des Hauptprogramms nicht zu blockieren
        thread.start()

    # Hilfsmethode für Report-Ausführung und Aufräumen
    async def _run_report_and_cleanup(self, schedule_id):
        """Run report and clean up after completion"""
        try:
            # Run the actual report
            await self._run_scheduled_report(schedule_id)
        except Exception as e:
            logger.error(f"Error processing job {schedule_id}: {str(e)}")
            
            # Update history with error if possible
            schedule_data = self.get_schedule(schedule_id)
            if schedule_data and "history" in schedule_data and schedule_data["history"]:
                for entry in reversed(schedule_data["history"]):
                    if entry.get("status") in ["started", "queued"]:
                        entry["status"] = "error"
                        entry["message"] = f"Error: {str(e)}"
                        self._save_schedule(schedule_id, schedule_data)
                        break
        finally:
            # Reset current job
            self.currently_running_job = None
            logger.info(f"Job {schedule_id} processing completed. Remaining queue: {len(self.job_queue)}")