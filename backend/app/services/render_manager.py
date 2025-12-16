"""
Render Manager Service - Orchestrates scene rendering workflow
"""

import logging
import os
import asyncio
import fcntl  # For file-based profile locking on Unix-like systems
from pathlib import Path
from typing import Dict, Any, Optional, List
from shutil import copytree
from app.services.browser_manager import BrowserManager
from app.services.flow_controller import FlowController
from app.services.character_manager import CharacterManager
from app.config import config_manager, settings, DOWNLOADS_PATH

logger = logging.getLogger(__name__)


class RenderManager:
    """Manages the complete scene rendering workflow"""
    
    def __init__(self, worker_id: str = None):
        # Use worker ID if available, otherwise use process ID
        if not worker_id:
            worker_id = os.getenv("CELERY_WORKER_NAME", f"worker_{os.getpid()}")
        self.worker_id = worker_id
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
        
        Returns:
            {
                "success": bool,
                "video_path": str,
                "scene_id": str,
                "error": str (if failed)
            }
        """
        # Get scene context for logging at the start
        scene_id_str = scene.get("id", "unknown")
        scene_number = scene.get("number", "?")
        scene_prompt_preview = scene.get("prompt", "")[:50] if scene.get("prompt") else "None"
        
        logger.info(f"[Scene {scene_number} ID: {scene_id_str}] ===== RENDER SCENE STARTED =====")
        logger.info(f"[Scene {scene_number} ID: {scene_id_str}] Prompt preview: {scene_prompt_preview}...")
        logger.info(f"[Scene {scene_number} ID: {scene_id_str}] Project ID: {project_id}")
        
        page = None
        lock_file = None  # File handle used for profile locking (may remain None)
        try:
            # Ensure we're using the active profile (the one where user logged in)
            active_profile = self.profile_manager.get_active_profile()
            if not active_profile:
                raise Exception("No active profile found. Please set an active profile in settings.")
            
            logger.info(f"Using active profile for rendering: {active_profile.name} ({active_profile.id})")
            logger.info(f"Profile path: {active_profile.profile_path}")

            # Validate base active profile path exists
            from pathlib import Path
            base_profile_path = Path(active_profile.profile_path)
            if not base_profile_path.exists():
                raise Exception(f"Profile path does not exist: {base_profile_path}. Please check the profile configuration.")

            # Create a worker-specific profile directory cloned from the active profile
            # This allows parallel workers without sharing the same Chrome user-data-dir
            worker_profiles_root = self.profile_manager.profiles_dir / "worker_profiles"
            worker_profiles_root.mkdir(parents=True, exist_ok=True)
            worker_profile_path = worker_profiles_root / f"{active_profile.id}_worker_{self.worker_id}"

            if not worker_profile_path.exists():
                logger.info(f"Creating worker-specific profile by copying active profile to: {worker_profile_path}")
                try:
                    copytree(base_profile_path, worker_profile_path, dirs_exist_ok=True)
                except TypeError:
                    # For older Python without dirs_exist_ok, ignore if already copied partially
                    try:
                        copytree(base_profile_path, worker_profile_path)
                    except FileExistsError:
                        logger.info(f"Worker profile already exists: {worker_profile_path}")
                except Exception as copy_error:
                    logger.warning(f"Could not clone active profile for worker: {copy_error}")
                    # Fallback to using base profile directly (may limit parallelism)
                    worker_profile_path = base_profile_path

            profile_path = worker_profile_path
            logger.info(f"Using worker-specific profile path: {profile_path}")

            # Ensure Default directory exists in worker profile
            default_dir = profile_path / "Default"
            if not default_dir.exists():
                logger.warning(f"Default directory does not exist in worker profile, creating it: {default_dir}")
                try:
                    default_dir.mkdir(parents=True, exist_ok=True)
                except Exception as default_error:
                    raise Exception(f"Cannot create Default directory in worker profile: {default_error}")

            # Initialize browser with the worker-specific profile path
            logger.info("Initializing browser manager with worker-specific profile path...")
            try:
                await self.browser_manager.initialize_with_profile_path(profile_path)
                logger.info("✓ Browser manager initialized with worker-specific profile")
            except Exception as init_error:
                error_type = type(init_error).__name__
                error_msg = str(init_error)
                logger.error(f"✗ Failed to initialize browser with worker profile: {error_type}: {error_msg}")
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
                    logger.info(f"[Scene {scene_number} ID: {scene_id_str}] Page created successfully")
                    
                    # Verify page is not immediately closed
                    if page.is_closed():
                        logger.warning(f"[Scene {scene_number} ID: {scene_id_str}] Page was immediately closed after creation")
                        if page_attempt < max_page_retries - 1:
                            await asyncio.sleep(2)  # Wait longer before retry
                            continue
                        else:
                            raise Exception(f"[Scene {scene_number} ID: {scene_id_str}] Page keeps getting closed immediately after creation")
                    
                    break  # Success
                except Exception as page_error:
                    error_str = str(page_error)
                    if page_attempt < max_page_retries - 1:
                        logger.warning(f"[Scene {scene_number} ID: {scene_id_str}] Page creation attempt {page_attempt + 1}/{max_page_retries} failed: {error_str}, retrying...")
                        await asyncio.sleep(3)  # Wait longer before retry
                    else:
                        logger.error(f"[Scene {scene_number} ID: {scene_id_str}] Failed to create page after {max_page_retries} attempts: {error_str}")
                        raise Exception(f"[Scene {scene_number} ID: {scene_id_str}] Cannot create page: {error_str}")
            
            if not page:
                raise Exception("Failed to create page after all retries")
            
            # Get scene context for logging
            scene_id_str = scene.get("id", "unknown")
            scene_number = scene.get("number", "?")
            
            # Navigate to Flow with retry logic for closed pages
            logger.info(f"[Scene {scene_number} ID: {scene_id_str}] Navigating to Flow...")
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
                            logger.info(f"[Scene {scene_number} ID: {scene_id_str}] Page recreated, waiting before retry...")
                            await asyncio.sleep(2)  # Wait a bit longer for page to stabilize
                            continue
                        else:
                            raise Exception(f"[Scene {scene_number} ID: {scene_id_str}] Page closed and cannot be recreated after all retries")
                    
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
            
            # Ensure we're in a new project/editor view. For automated scene rendering,
            # we force creation of a fresh project so each scene has a clean editor.
            logger.info(f"[Scene {scene_number} ID: {scene_id_str}] Ensuring we're in editor view (force_new=True for automated scene render)...")
            await self.flow_controller.ensure_new_project(page, force_new=True)
            logger.info(f"[Scene {scene_number} ID: {scene_id_str}] ✓ Editor view ready for prompt injection")
            
            # Get render settings from project if not provided
            if not render_settings:
                from app.models.project import Project
                from app.core.database import SessionLocal
                temp_db = SessionLocal()
                try:
                    project = temp_db.query(Project).filter(Project.id == project_id).first()
                    if project:
                        render_settings = project.get_render_settings()
                        logger.info(f"Loaded render settings from project: {render_settings}")
                    else:
                        render_settings = {"aspect_ratio": "16:9", "videos_per_scene": 2, "model": "veo3.1-fast"}
                        logger.info("Project not found, using default render settings")
                finally:
                    temp_db.close()
            
            # Configure render settings (if method exists)
            if render_settings and hasattr(self.flow_controller, 'configure_render_settings'):
                logger.info(f"Configuring render settings: {render_settings}")
                try:
                    await self.flow_controller.configure_render_settings(
                        page,
                        aspect_ratio=render_settings.get("aspect_ratio", "16:9"),
                        videos_per_scene=render_settings.get("videos_per_scene", 2),
                        model=render_settings.get("model", "veo3.1-fast")
                    )
                except AttributeError:
                    logger.warning("configure_render_settings not available, skipping render settings configuration")
            elif render_settings:
                logger.warning("Render settings provided but configure_render_settings method not available")
            
            # Build prompt with character consistency
            prompt = self._build_scene_prompt(scene, characters)
            logger.info(f"[Scene {scene_number} ID: {scene_id_str}] Using prompt ({len(prompt)} chars): {prompt[:100]}...")
            
            # Inject prompt
            logger.info(f"[Scene {scene_number} ID: {scene_id_str}] Injecting prompt into Flow editor...")
            await self.flow_controller.inject_prompt(page, prompt)
            logger.info(f"[Scene {scene_number} ID: {scene_id_str}] ✓ Prompt injected")
            
            # Wait a bit after injecting prompt to ensure it's fully set
            await asyncio.sleep(1)
            
            # Verify prompt is still in textarea before triggering
            try:
                textarea = page.locator('textarea, [contenteditable]').first
                if await textarea.count() > 0:
                    is_textarea = await textarea.get_attribute("tagName") == "TEXTAREA"
                    if is_textarea:
                        prompt_check = await textarea.input_value()
                    else:
                        prompt_check = await textarea.text_content()
                    
                    if not prompt_check or len(prompt_check.strip()) < len(prompt.strip()) * 0.8:
                        logger.warning(f"⚠️ Prompt appears incomplete before triggering: {len(prompt_check) if prompt_check else 0} chars (expected ~{len(prompt)} chars)")
                        logger.info("Re-injecting prompt...")
                        await self.flow_controller.inject_prompt(page, prompt)
                        await asyncio.sleep(1)
                    else:
                        logger.info(f"✓ Prompt verified before triggering: {len(prompt_check)} chars")
            except Exception as verify_error:
                logger.warning(f"Could not verify prompt before triggering: {verify_error}")
            
            # Trigger generation
            logger.info(f"[Scene {scene_number} ID: {scene_id_str}] Triggering video generation...")
            started = await self.flow_controller.trigger_generation(page)
            logger.info(f"[Scene {scene_number} ID: {scene_id_str}] Generation trigger result: {started}")
            
            if not started:
                logger.warning("Generation did not start; re-injecting prompt and retrying once...")
                await asyncio.sleep(1)
                await self.flow_controller.inject_prompt(page, prompt)
                await asyncio.sleep(1)
                started = await self.flow_controller.trigger_generation(page)
                if not started:
                    # Flow UI may still have started generation even if our
                    # detection failed (UI changes frequently). Log a warning
                    # but continue to wait_for_completion instead of failing.
                    logger.warning(
                        "Generation did not start after retry according to detectors; "
                        "proceeding to wait_for_completion in case it actually started."
                    )
            
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
            
            logger.info(f"[Scene {scene_number} ID: {scene_id_str}] Scene rendered successfully: {video_path}")
            logger.info(f"[Scene {scene_number} ID: {scene_id_str}] ===== RENDER SCENE COMPLETED =====")
            return {
                "success": True,
                "video_path": video_path,
                "scene_id": scene_id_str
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
            
            logger.error(f"[Scene {scene_number} ID: {scene_id_str}] Render error: {error_full}", exc_info=True)
            
            # Return error (limit to 1000 chars to avoid serialization issues)
            return {
                "success": False,
                "error": error_full[:1000],
                "scene_id": scene_id_str,
                "error_type": error_type
            }
        finally:
            # Release profile lock
            if lock_file:
                try:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)
                    lock_file.close()
                except Exception:
                    pass
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

