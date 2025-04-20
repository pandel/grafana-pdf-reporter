import os
import sys
import tempfile
import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Page, Browser
from reportlab.lib.pagesizes import A4, A3, LETTER, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from io import BytesIO
from PIL import Image as PILImage

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get('LOGLEVEL', 'DEBUG').upper())
formatter = logging.Formatter("%(asctime)s [%(levelname)5s] %(name)30s: %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

class PDFGenerator:
    """Generate PDF reports from Grafana panels using Playwright for rendering"""
    
    def __init__(self, grafana_url: str, grafana_username: str, grafana_password: str):
        """
        Initialize PDF Generator
        
        Args:
            grafana_url: Grafana server URL
            grafana_username: Grafana username for authentication
            grafana_password: Grafana password for authentication
        """
        # Ensure the URL is properly formatted and there are no trailing slashes
        self.grafana_url = grafana_url.rstrip('/')
        self.grafana_username = grafana_username
        self.grafana_password = grafana_password
        self.temp_dir = tempfile.mkdtemp()
        self.browser = None
        self.context = None
        
        # Log the actual URL being used to help with debugging
        logger.info(f"PDF Generator initialized with Grafana URL: {self.grafana_url}")
    
    async def initialize(self):
        """Initialize Playwright browser"""
        try:
            playwright = await async_playwright().start()
            # https://github.com/microsoft/playwright-python/issues/2820
            self.browser = await playwright.chromium.launch(headless=True, channel="chromium")
            self.context = await self.browser.new_context(ignore_https_errors=True)
        except Exception as e:
            logger.error(f"Error initializing Playwright Browser: {str(e)}")
            raise

        # Login to Grafana
        await self._login_to_grafana()
    
    async def close(self):
        """Close Playwright browser"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def _login_to_grafana(self):
        """Authenticate with Grafana"""
        page = await self.context.new_page()
        
        try:
            logger.debug(f"Attempting to log in to Grafana at {self.grafana_url}/login")
            await page.goto(f"{self.grafana_url}/login")
            await page.fill('input[name="user"]', self.grafana_username)
            await page.fill('input[name="password"]', self.grafana_password)
            await page.click('button[type="submit"]')
            await page.wait_for_selector('.page-dashboard', timeout=30000)
            logger.info("Successfully logged in to Grafana")
        except Exception as e:
            logger.error(f"Error logging in to Grafana: {str(e)}")
            raise
        finally:
            await page.close()
    
    async def capture_panel(self, panel_url: str, width: int, height: int, grafana_version: str) -> BytesIO:
        """
        Capture a panel as image using Playwright
        
        Args:
            panel_url: URL to the panel
            width: Desired width
            height: Desired height
            grafana_version: Grafana version
            
        Returns:
            BytesIO object containing the panel image
        """
        page = await self.context.new_page()
        
        try:
            logger.info(f"Capturing panel from URL: {panel_url}")
            await page.set_viewport_size({"width": width, "height": height})
            await page.goto(panel_url, wait_until="domcontentloaded")
            
            # Import settings service to get selectors
            from api.api_controller import settings_service
            
            # Get selectors from settings
            settings = settings_service.get_decrypted_settings()
            selectors = settings.get("grafana_selectors", [])
            
            # Find matching selector for the version
            # see: https://autify.com/blog/playwright-get-by-id
            selector_found = False
            for selector_config in selectors:
                if grafana_version.startswith(selector_config.get("version", "")):
                    selector = selector_config.get("selector", "")
                    if selector:
                        logger.debug(f"Using selector '{selector}' for Grafana version {grafana_version}")
                        #await page.get_by_test_id(selector).wait_for(timeout=30000)
                        await page.locator(f'[data-testid^="{selector}"]').wait_for(timeout=30000);
                        selector_found = True
                        break
            
            # Default fallback if no matching selector found
            if not selector_found:
                logger.warning(f"No matching selector for Grafana version {grafana_version}, using defaults")
                if grafana_version.startswith("9."):
                    #await page.get_by_test_id("header-container").wait_for(timeout=30000)
                    await page.locator(f'[data-testid^="data-testid Panel header"]').wait_for(timeout=30000);
                elif grafana_version.startswith("11."):
                    #await page.get_by_test_id("data-testid panel content").wait_for(timeout=30000)
                    await page.locator(f'[data-testid^="data-testid panel content"]').wait_for(timeout=30000);
            
            await page.wait_for_load_state(state="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)  # Give charts time to render
            
            # Take screenshot
            screenshot = await page.screenshot(type="png")

            return BytesIO(screenshot)
        finally:
            await page.close()

    def _ensure_numeric_values(self, template):
        """
        Ensure all template values that should be numeric are actually numbers.

        Args:
            template: Template configuration dict

        Returns:
            Template with all numeric values converted to numbers
        """
        # Make a deep copy to avoid modifying the original
        template = json.loads(json.dumps(template))

        # Convert header values
        if "header" in template:
            if "height" in template["header"]:
                template["header"]["height"] = float(template["header"]["height"])

        # Convert footer values
        if "footer" in template:
            if "height" in template["footer"]:
                template["footer"]["height"] = float(template["footer"]["height"])

        # Convert page margin values
        if "page" in template:
            for key in ["marginTop", "marginBottom", "marginLeft", "marginRight"]:
                if key in template["page"]:
                    template["page"][key] = float(template["page"][key])

        return template

    def _generate_multi_page_pdf(self, panel_images: List[Dict[str, Any]], template: Dict[str, Any], 
                                 layout: Dict[str, int], time_range=None, grafana_version=None) -> BytesIO:
        """
        Generate multi-page PDF report from panel images
        
        Args:
            panel_images: List of panel image data (BytesIO objects) with position info
            template: Template configuration for header/footer
            layout: Layout configuration (rows, columns, etc.)
            time_range: Dictionary containing time range info (from, to)
            
        Returns:
            BytesIO object containing the PDF
        """
        # Ensure all template values are of the correct type
        template = self._ensure_numeric_values(template)

        # Setup PDF size and orientation
        page_sizes = {
            "A4": A4,
            "A3": A3,
            "Letter": LETTER
        }
        page_size = page_sizes.get(template["page"]["size"], A4)
        
        if template["page"]["orientation"] == "landscape":
            page_size = landscape(page_size)
        
        # Create PDF buffer
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=page_size)
        pdf.setAuthor("Grafana PDF Reporter")
        pdf.setSubject("Security Report")
        pdf.setTitle(template["header"]["title"])
        # Add Grafana version to PDF metadata if available
        if grafana_version:
            pdf.setKeywords(f"Grafana {grafana_version}")

        # Get page dimensions
        page_width, page_height = page_size
        
        # Calculate content area dimensions (excluding margins)
        margins = template["page"]
        content_width = page_width - (margins["marginLeft"] + margins["marginRight"]) * mm
        spacing_between_sections = 1 * mm
        content_height = page_height - (margins["marginTop"] + margins["marginBottom"] + 
                                    template["header"]["height"] + template["footer"]["height"] + 
                                    2 * spacing_between_sections) * mm
        
        # Define spacing between panels (1mm)
        spacing = 1 * mm
        
        # Calculate grid cell dimensions with spacing
        rows_per_page = layout["rows"]
        columns = layout["columns"]
        
        # Subtract the total spacing from the available content dimensions
        # For n cells, we need (n-1) spacing areas between them
        horizontal_spacing_total = spacing * (columns - 1)
        vertical_spacing_total = spacing * (rows_per_page - 1)
        
        # Calculate cell dimensions accounting for spacing
        cell_width = (content_width - horizontal_spacing_total) / columns
        cell_height = (content_height - vertical_spacing_total) / rows_per_page
        
        # Group panels by page based on their y-coordinate
        panels_by_page = {}
        for panel in panel_images:
            page_index = panel["y"] // rows_per_page
            if page_index not in panels_by_page:
                panels_by_page[page_index] = []
            panels_by_page[page_index].append(panel)
        
        # Sort pages by index
        sorted_pages = sorted(panels_by_page.keys())
        total_pages = len(sorted_pages)
        
        # Draw each page
        for i, page_index in enumerate(sorted_pages):
            if i > 0:
                # Add a new page for subsequent pages
                pdf.showPage()
            
            # Position for content area (top of content area)
            content_y = page_height - (margins["marginTop"] * mm + template["header"]["height"] * mm + spacing_between_sections)
            
            # Draw header
            self._draw_header(pdf, template["header"], page_width, page_height, margins)
            
            # Draw panels for this page
            panels_on_page = panels_by_page[page_index]
            for panel in panels_on_page:
                # Calculate position within this page's grid
                # Adjust y-coordinate relative to the current page
                relative_y = panel["y"] % rows_per_page
                
                # Calculate position in PDF coordinates with spacing
                # For x position: each cell gets its width plus spacing between cells
                x = margins["marginLeft"] * mm + panel["x"] * (cell_width + spacing)
                
                # For y position: calculate from top of content area
                # Each row gets its height plus spacing between rows
                y = content_y - (relative_y * (cell_height + spacing) + panel["h"] * cell_height)
                
                # Panel dimensions
                width = panel["w"] * cell_width
                # If the panel spans multiple grid cells, we need to add spacing between them
                if panel["w"] > 1:
                    width += spacing * (panel["w"] - 1)
                
                height = panel["h"] * cell_height
                # If the panel spans multiple grid cells, we need to add spacing between them
                if panel["h"] > 1:
                    height += spacing * (panel["h"] - 1)

                try:
                    # Ensure it's a BytesIO object
                    if isinstance(panel["image"], BytesIO):
                        img_data = panel["image"]
                        img_data.seek(0)  # Ensure we're at the beginning
                    else:
                        logger.error(f"Unexpected image type: {type(panel['image'])}")
                        continue  # Skip this panel

                    # Resize image to fit cell
                    img = PILImage.open(img_data)
                    img = img.resize((int(width), int(height)), PILImage.Resampling.LANCZOS)

                    # Save resized image to temporary BytesIO
                    temp_img = BytesIO()
                    img.save(temp_img, format="PNG")
                    temp_img.seek(0)
                    temp_img = ImageReader(temp_img)

                    # Draw image on PDF
                    pdf.drawImage(temp_img, x, y, width=width, height=height)
                        
                except Exception as e:
                    logger.error(f"Error processing panel image: {e}")
                    continue  # Skip this panel on error
            
            # Draw footer with time range info and page number
            self._draw_footer(
                pdf, 
                template["footer"], 
                page_width, 
                page_height, 
                margins, 
                time_range,
                current_page=i+1, 
                total_pages=total_pages
            )
        
        # Finalize PDF
        pdf.save()
        buffer.seek(0)
        return buffer

    def _draw_header(self, pdf, header_config, page_width, page_height, margins):
        """Draw header on PDF page"""
        # Header background
        pdf.setFillColor(colors.HexColor(header_config["backgroundColor"]))
        pdf.rect(
            margins["marginLeft"] * mm, 
            page_height - (margins["marginTop"] + header_config["height"]) * mm,
            page_width - (margins["marginLeft"] + margins["marginRight"]) * mm,
            header_config["height"] * mm,
            fill=1,
            stroke=0
        )
        
        # Header title
        pdf.setFillColor(colors.HexColor(header_config["textColor"]))
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(
            (margins["marginLeft"] + 5) * mm,
            page_height - (margins["marginTop"] + header_config["height"] / 2) * mm,
            header_config["title"]
        )
        
        if header_config.get("logoUrl"):
            logo_height = header_config["height"] * 0.8 * mm
            pdf.drawImage(
                header_config["logoUrl"],
                page_width - (margins["marginRight"] + 30) * mm,
                page_height - (margins["marginTop"] + header_config["height"] * 0.9) * mm,
                width=30 * mm,
                height=logo_height,
                preserveAspectRatio=True
            )
            
            # Current date - when logo is present, place it in center
            pdf.setFont("Helvetica", 9)
            
            # Calculate center position
            date_text = datetime.now().strftime("%Y-%m-%d %H:%M")
            date_width = pdf.stringWidth(date_text, "Helvetica", 9)
            date_x = (page_width - date_width) / 2
            
            pdf.drawString(
                date_x,
                page_height - (margins["marginTop"] + header_config["height"] / 2) * mm,
                date_text
            )
        else:
            # Current date - when no logo is present, place it at right margin
            pdf.setFont("Helvetica", 9)
            pdf.drawString(
                page_width - (margins["marginRight"] + 50) * mm,
                page_height - (margins["marginTop"] + header_config["height"] / 2) * mm,
                datetime.now().strftime("%Y-%m-%d %H:%M")
            )
    
    def _draw_footer(self, pdf, footer_config, page_width, page_height, margins, time_range=None, 
                     current_page=1, total_pages=1):
        """Draw footer on PDF page with time range info and page numbers"""
        # Footer background
        pdf.setFillColor(colors.HexColor(footer_config["backgroundColor"]))
        pdf.rect(
            margins["marginLeft"] * mm, 
            margins["marginBottom"] * mm,
            page_width - (margins["marginLeft"] + margins["marginRight"]) * mm,
            footer_config["height"] * mm,
            fill=1,
            stroke=0
        )
        
        # Footer text
        pdf.setFillColor(colors.HexColor(footer_config["textColor"]))
        pdf.setFont("Helvetica", 9)
        
        # Original footer text - left aligned
        footer_text = footer_config["text"]
        pdf.drawString(
            (margins["marginLeft"] + 5) * mm,
            (margins["marginBottom"] + footer_config["height"] / 2) * mm,
            footer_text
        )
        
        # Page numbers - right aligned
        page_number_text = footer_config["pageNumberFormat"].replace("(page)", str(current_page)).replace("(total)", str(total_pages))
        pdf.drawString(
            page_width - (margins["marginRight"] + 50) * mm,
            (margins["marginBottom"] + footer_config["height"] / 2) * mm,
            page_number_text
        )
        
        # Add time range information if available - centered
        if time_range and "from" in time_range and "to" in time_range:
            time_range_text = f"Time Range: {time_range['from']} to {time_range['to']}"
            # Calculate text width to center properly
            time_range_width = pdf.stringWidth(time_range_text, "Helvetica", 9)
            # Center position
            time_range_x = (page_width - time_range_width) / 2
            # Draw time range info centered
            pdf.drawString(
                time_range_x,
                (margins["marginBottom"] + footer_config["height"] / 2) * mm,
                time_range_text
            )

    async def generate_report(self, layout_config: Dict[str, Any], template_config: Dict[str, Any], 
                         grafana_service, job_id: str = None, progress_callback=None,
                         server_id: str = None, grafana_version: str = None) -> BytesIO:
        """
        Generate a complete PDF report based on layout and template

        Args:
            layout_config: Configuration for the report layout
            template_config: Template configuration
            grafana_service: Instance of GrafanaService
            job_id: Optional job ID for tracking progress
            progress_callback: Optional callback function to report progress
        
        Returns:
            BytesIO object containing the PDF report
        """
        # Set the server to use if specified
        if server_id:
            original_server = grafana_service.get_current_server_id()
            grafana_service.set_current_server(server_id)

            # If no explicit version was provided, try to get it now
            if grafana_version is None:
                grafana_version = grafana_service.get_grafana_version(server_id)
        
        try:
            panel_images = []
            total_panels = len(layout_config["panels"])
            completed_panels = 0
            
            # Berechne Gewichtung der einzelnen Schritte
            # Wir haben: 1 Login + N Panels + 1 PDF Erstellung
            total_steps = 1 + total_panels + 1
            login_weight = 1.0 / total_steps * 100  # Anteil für Login
            panel_weight = 1.0 / total_steps * 100  # Anteil pro Panel
            pdf_weight = 1.0 / total_steps * 100    # Anteil für PDF-Erstellung
            
            # Set time range for all panels
            time_range = layout_config.get("timeRange", {})
            time_from = time_range.get("from", "now-6h")
            time_to = time_range.get("to", "now")
            
            # Check if job has been cancelled
            if job_id and self.check_job_cancelled(job_id):
                logger.info(f"Job {job_id} was cancelled before starting")
                if progress_callback:
                    progress_callback(job_id, -1, "Report generation cancelled")
                raise Exception("Report generation cancelled by user")
                    
            # Capture each panel
            for panel_item in layout_config["panels"]:
                # Check if job has been cancelled
                if job_id and self.check_job_cancelled(job_id):
                    logger.info(f"Job {job_id} was cancelled during panel capture")
                    if progress_callback:
                        progress_callback(job_id, -1, "Report generation cancelled")
                    raise Exception("Report generation cancelled by user")
                    
                dashboard_uid = panel_item["dashboardUid"]
                panel_id = panel_item["panelId"]

                # Calculate panel dimensions based on layout
                width = 800  # Base width
                height = 320  # Base height

                # Generate panel URL
                panel_url = grafana_service.get_panel_url(
                    dashboard_uid,
                    panel_id,
                    width,
                    height,
                    theme=layout_config.get("theme", "dark"),
                    time_from=time_from,
                    time_to=time_to
                )

                # Report progress for panel capture
                if progress_callback and job_id:
                    panel_name = panel_item.get("title", f"Panel {panel_id}")
                    completed_percentage = login_weight + panel_weight * completed_panels
                    progress_callback(
                        job_id, 
                        int(completed_percentage),
                        f"Capturing panel {completed_panels+1}/{total_panels}: {panel_name}"
                    )

                # Capture the panel
                panel_image = await self.capture_panel(panel_url, width, height, grafana_version)

                # Add to list with layout position
                panel_images.append({
                    "image": panel_image,
                    "x": panel_item["x"],
                    "y": panel_item["y"],
                    "w": panel_item["w"],
                    "h": panel_item["h"],
                    "title": panel_item.get("title", "")
                })
                
                # Update progress
                completed_panels += 1
                
            # Check if job has been cancelled before PDF compilation
            if job_id and self.check_job_cancelled(job_id):
                logger.info(f"Job {job_id} was cancelled before PDF compilation")
                if progress_callback:
                    progress_callback(job_id, -1, "Report generation cancelled")
                raise Exception("Report generation cancelled by user")
            
            # Report progress for PDF compilation starting
            if progress_callback and job_id:
                completed_percentage = login_weight + panel_weight * total_panels
                progress_callback(job_id, int(completed_percentage), "All panels captured, compiling PDF")

            # Generate the PDF with all panels and include time range
            pdf_data = self._generate_multi_page_pdf(
                panel_images=panel_images,
                template=template_config,
                layout={
                    "rows": layout_config["rows"],
                    "columns": layout_config["columns"]
                },
                time_range={"from": time_from, "to": time_to}
            )
            
            # Report completion
            if progress_callback and job_id:
                progress_callback(job_id, 100, "PDF generation complete")
            
            return pdf_data

        finally:
            # Restore the original server if we changed it
            if server_id and original_server:
                grafana_service.set_current_server(original_server)

    def check_job_cancelled(self, job_id):
        """
        Check if a job has been cancelled
        
        Args:
            job_id: The ID of the job to check
            
        Returns:
            True if the job has been cancelled, False otherwise
        """
        # Import here to avoid circular imports
        from api.api_controller import progress_data
        
        if job_id and job_id in progress_data:
            return progress_data[job_id].get("cancelled", False)
        return False
