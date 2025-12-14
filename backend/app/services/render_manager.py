"""
Render Manager Service - Orchestrates scene rendering workflow
"""

import logging
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from app.services.browser_manager import BrowserManager
from app.services.flow_controller import FlowController
from app.services.character_manager import CharacterManager
from app.config import config_manager, settings, DOWNLOADS_PATH

logger = logging.getLogger(__name__)


class RenderManager:
    """Manages the complete scene rendering workflow"""
    
    def __init__(self, worker_id: str = None):
        import os
        # Use worker ID if available, otherwise use process ID
        if not worker_id:
            worker_id = os.getenv("CELERY_WORKER_NAME", f"worker_{os.getpid()}")
        self.browser_manager = BrowserManager(worker_id=worker_id)
        self.flow_controller = FlowController(self.browser_manager)
        self.character_manager = CharacterManager()
        # Ensure we use ProfileManager to get the active profile
        from app.services.profile_manager import ProfileManager
        self.profile_manager = ProfileManager()
    
    async def render_scene(
        self,
        scene: Dict[str, Any],
        project_id: str,
        characters: Optional[List[Dict[str, Any]]] = None,
        render_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Render a single scene using browser automation
        
        Args:
            scene: Scene dictionary with prompt and metadata
            project_id: Project ID for organizing outputs
            characters: Optional list of characters for consistency
            render_settings: Optional render settings dict with aspect_ratio, videos_per_scene, model
        
        Returns:
            {
                "success": bool,
                "video_path": str,
                "scene_id": str,
                "error": str (if failed)
            }
        """
        page = None
        try:
            # Ensure we're using the active profile (the one where user logged in)
            active_profile = self.profile_manager.get_active_profile()
            if not active_profile:
                raise Exception("No active profile found. Please set an active profile in settings.")
            
            logger.info(f"Using active profile for rendering: {active_profile.name} ({active_profile.id})")
            logger.info(f"Profile path: {active_profile.profile_path}")
            
            # Validate profile path exists
            from pathlib import Path
            profile_path = Path(active_profile.profile_path)
            if not profile_path.exists():
                raise Exception(f"Profile path does not exist: {profile_path}. Please check the profile configuration.")
            
            # Check if Default directory exists
            default_dir = profile_path / "Default"
            if not default_dir.exists():
                logger.warning(f"Default directory does not exist in profile, creating it: {default_dir}")
                try:
                    default_dir.mkdir(parents=True, exist_ok=True)
                except Exception as default_error:
                    raise Exception(f"Cannot create Default directory in profile: {default_error}")
            
            # CRITICAL FIX: Initialize browser with the active profile path directly
            # This ensures we use the logged-in profile, not a worker-specific one without cookies
            logger.info("Initializing browser manager with active profile path...")
            try:
                await self.browser_manager.initialize_with_profile_path(profile_path)
                logger.info("✓ Browser manager initialized with active profile")
            except Exception as init_error:
                error_type = type(init_error).__name__
                error_msg = str(init_error)
                logger.error(f"✗ Failed to initialize browser with profile: {error_type}: {error_msg}")
                raise Exception(f"Profile loading failed: {error_type}: {error_msg}")
            
            # Create new page with retry logic for closed target errors
            page = None
            max_page_retries = 3
            for page_attempt in range(max_page_retries):
                try:
                    logger.info(f"Creating new page (attempt {page_attempt + 1}/{max_page_retries})...")
                    
                    # Verify browser is still initialized
                    if not self.browser_manager._initialized:
                        logger.warning("Browser manager not initialized, re-initializing...")
                        await self.browser_manager.initialize_with_profile_path(profile_path)
                    
                    # Check context is alive
                    if not self.browser_manager.context:
                        logger.error("Browser context is None - cannot create page")
                        raise Exception("Browser context is None")
                    
                    # For persistent contexts, browser might be None - check context instead
                    if self.browser_manager.browser:
                        if not self.browser_manager.browser.is_connected():
                            logger.error("Browser is not connected - cannot create page")
                            raise Exception("Browser is not connected")
                    else:
                        # Browser is None (common for persistent contexts) - verify context works
                        logger.debug("Browser object is None (normal for persistent contexts), verifying context...")
                        try:
                            # Try to get pages count as a test
                            pages = self.browser_manager.context.pages
                            logger.debug(f"Context has {len(pages)} existing pages")
                        except Exception as context_test_error:
                            logger.error(f"Context verification failed: {context_test_error}")
                            raise Exception(f"Context is not usable: {context_test_error}")
                    
                    page = await self.browser_manager.new_page()
                    logger.info("Page created successfully")
                    
                    # Verify page is not immediately closed
                    if page.is_closed():
                        logger.warning("Page was immediately closed after creation")
                        if page_attempt < max_page_retries - 1:
                            await asyncio.sleep(1)
                            continue
                        else:
                            raise Exception("Page keeps getting closed immediately after creation")
                    
                    break  # Success
                except Exception as page_error:
                    if page_attempt < max_page_retries - 1:
                        logger.warning(f"Page creation attempt {page_attempt + 1} failed: {page_error}, retrying...")
                        await asyncio.sleep(2)
                    else:
                        logger.error(f"Failed to create page after {max_page_retries} attempts: {page_error}")
                        raise Exception(f"Cannot create page: {page_error}")
            
            if not page:
                raise Exception("Failed to create page after all retries")
            
            # Navigate to Flow with retry logic for closed pages
            logger.info(f"Navigating to Flow for scene {scene.get('id', 'unknown')}")
            nav_retries = 5  # Increased retries for page closure issues
            for nav_attempt in range(nav_retries):
                try:
                    # Check page is still alive before navigation
                    if page.is_closed():
                        logger.warning(f"Page closed before navigation attempt {nav_attempt + 1}, recreating...")
                        if nav_attempt < nav_retries - 1:
                            try:
                                await page.close()
                            except:
                                pass
                            page = await self.browser_manager.new_page()
                            logger.info("Page recreated, waiting before retry...")
                            await asyncio.sleep(2)  # Wait a bit longer for page to stabilize
                            continue
                        else:
                            raise Exception("Page closed and cannot be recreated after all retries")
                    
                    # Navigate to Flow
                    await self.flow_controller.navigate_to_flow(page)
                    break  # Success
                    
                except Exception as nav_error:
                    error_str = str(nav_error).lower()
                    error_type = type(nav_error).__name__
                    
                    # FIX: Handle "Page closed - needs new page" exception from navigate_to_flow
                    if "page closed" in error_str and "needs new page" in error_str:
                        if nav_attempt < nav_retries - 1:
                            logger.warning(f"Page closed during navigation (attempt {nav_attempt + 1}/{nav_retries}), recreating page...")
                            try:
                                if page and not page.is_closed():
                                    await page.close()
                            except:
                                pass
                            await asyncio.sleep(2)
                            # Recreate page
                            try:
                                page = await self.browser_manager.new_page()
                                logger.info("✓ Page recreated for navigation retry")
                                await asyncio.sleep(1)  # Wait for page to stabilize
                                continue  # Retry navigation
                            except Exception as recreate_error:
                                logger.error(f"Failed to recreate page: {recreate_error}")
                                if nav_attempt < nav_retries - 1:
                                    await asyncio.sleep(3)  # Wait longer before retrying
                                    continue
                                else:
                                    raise Exception(f"Cannot recreate page after {nav_retries} attempts: {recreate_error}")
                        else:
                            logger.error(f"Page keeps closing during navigation after {nav_retries} attempts")
                            raise Exception(f"Browser/page keeps closing during navigation. This may indicate the browser crashed or there's a conflict with another process.")
                    
                    # Handle closed target errors
                    elif ("target" in error_str and "closed" in error_str) or "TargetClosedError" in error_type:
                        if nav_attempt < nav_retries - 1:
                            logger.warning(f"Navigation failed due to closed target (attempt {nav_attempt + 1}/{nav_retries}), recreating page...")
                            try:
                                if page and not page.is_closed():
                                    await page.close()
                            except:
                                pass
                            await asyncio.sleep(2)
                            # Recreate page
                            try:
                                page = await self.browser_manager.new_page()
                                logger.info("✓ Page recreated for TargetClosedError retry")
                                await asyncio.sleep(1)  # Wait for page to stabilize
                                continue  # Retry navigation
                            except Exception as recreate_error:
                                logger.error(f"Failed to recreate page: {recreate_error}")
                                if nav_attempt < nav_retries - 1:
                                    await asyncio.sleep(3)  # Wait longer before retrying
                                    continue
                                else:
                                    raise Exception(f"Cannot recreate page after {nav_retries} attempts: {recreate_error}")
                        else:
                            logger.error(f"Navigation failed after {nav_retries} attempts due to closed target")
                            raise Exception(f"Browser/page keeps closing during navigation. This may indicate the browser crashed or there's a conflict with another process.")
                    
                    # Check if it's a login issue
                    elif "login" in error_str or "sign in" in error_str:
                        return {
                            "success": False,
                            "error": "Login required. Please log in to Google Flow manually in the browser window, then try again. Or use setup_chrome_profile.sh to copy your logged-in profile.",
                            "scene_id": scene.get("id", ""),
                            "requires_login": True
                        }
                    else:
                        # Other errors - check if we should retry
                        if nav_attempt < nav_retries - 1:
                            logger.warning(f"Navigation failed (attempt {nav_attempt + 1}/{nav_retries}): {nav_error}")
                            logger.warning("Retrying navigation...")
                            await asyncio.sleep(2)
                            # Check if page is still alive, recreate if needed
                            if page.is_closed():
                                logger.warning("Page closed after error, recreating...")
                                try:
                                    page = await self.browser_manager.new_page()
                                    logger.info("✓ Page recreated after error")
                                    await asyncio.sleep(1)
                                except Exception as recreate_error:
                                    logger.error(f"Failed to recreate page: {recreate_error}")
                            continue
                        else:
                            # Last attempt - raise the error
                            logger.error(f"Navigation failed after {nav_retries} attempts: {nav_error}")
                            raise
            
            # Ensure we're in a new project/editor view
            logger.info("Ensuring we're in editor view...")
            await self.flow_controller.ensure_new_project(page)
            
            # Configure render settings if provided
            if render_settings:
                logger.info(f"Configuring render settings: {render_settings}")
                await self.flow_controller.configure_render_settings(
                    page,
                    aspect_ratio=render_settings.get("aspect_ratio", "16:9"),
                    videos_per_scene=render_settings.get("videos_per_scene", 2),
                    model=render_settings.get("model", "veo3.1-fast")
                )
            else:
                logger.info("No render settings provided, using defaults")
            
            # Build prompt with character consistency
            prompt = self._build_scene_prompt(scene, characters)
            logger.info(f"Using prompt: {prompt[:100]}...")
            
            # Inject prompt
            await self.flow_controller.inject_prompt(page, prompt)
            
            # Trigger generation
            logger.info("Triggering video generation...")
            await self.flow_controller.trigger_generation(page)
            
            # Wait for completion
            logger.info("Waiting for render completion...")
            result = await self.flow_controller.wait_for_completion(page)
            
            if result["status"] != "completed":
                error_msg = result.get("error", "Render failed")
                logger.error(f"Render failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "scene_id": scene.get("id", "")
                }
            
            # Download video
            output_path = os.path.join(DOWNLOADS_PATH, project_id)
            os.makedirs(output_path, exist_ok=True)
            
            scene_id = scene.get("id", "unknown")
            logger.info(f"Downloading video for scene {scene_id}...")
            video_path = await self.flow_controller.download_video(
                page, output_path, scene_id
            )
            
            logger.info(f"Scene rendered successfully: {video_path}")
            return {
                "success": True,
                "video_path": video_path,
                "scene_id": scene_id
            }
            
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            
            # Get full error details including traceback for debugging
            import traceback
            tb_str = traceback.format_exc()
            
            # If error is too short or just "Flow", try to get more context
            if not error_msg or len(error_msg) < 10 or error_msg == "Flow":
                # Try to extract more meaningful error from traceback
                tb_lines = tb_str.split('\n')
                for line in tb_lines:
                    if 'Error' in line or 'Exception' in line or 'Failed' in line:
                        if len(line) > len(error_msg):
                            error_msg = line.strip()
                            break
                
                # If still too short, use error type and first traceback line
                if len(error_msg) < 10:
                    error_msg = f"{error_type}: {error_msg}"
                    if tb_lines and len(tb_lines) > 1:
                        # Get the actual error line from traceback
                        for line in tb_lines[-5:]:  # Check last 5 lines
                            if line.strip() and not line.strip().startswith('File'):
                                error_msg = f"{error_type}: {line.strip()}"
                                break
            
            # Build full error message with context
            error_full = f"{error_msg}"
            if len(error_msg) < 50:  # If error is short, add more context
                # Add first line of traceback for context
                if tb_str:
                    tb_first_line = tb_str.split('\n')[0] if tb_str.split('\n') else ""
                    if tb_first_line and tb_first_line != error_msg:
                        error_full = f"{error_msg} ({tb_first_line[:100]})"
            
            logger.error(f"Render error: {error_full}", exc_info=True)
            
            # Return error (limit to 1000 chars to avoid serialization issues)
            return {
                "success": False,
                "error": error_full[:1000],
                "scene_id": scene.get("id", ""),
                "error_type": error_type
            }
        finally:
            # Always close page and cleanup browser
            if page:
                try:
                    await page.close()
                except:
                    pass
            # Close browser manager to free up resources
            try:
                await self.browser_manager.close()
            except:
                pass
    
    def _build_scene_prompt(
        self,
        scene: Dict[str, Any],
        characters: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build final scene prompt with character consistency"""
        base_prompt = scene.get("prompt", scene.get("description", ""))
        
        if characters:
            return self.character_manager.build_scene_prompt_with_characters(
                base_prompt,
                characters
            )
        
        return base_prompt
    
    async def close(self):
        """Cleanup browser resources"""
        await self.browser_manager.close()

