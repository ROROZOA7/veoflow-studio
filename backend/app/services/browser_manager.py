"""
Browser Manager Service - Handles Playwright browser lifecycle
"""

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from app.config import config_manager, settings
from pathlib import Path
import logging
import asyncio
import os
import subprocess
import time
import uuid
from typing import Optional

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages Playwright browser instances and contexts"""
    
    def __init__(self, worker_id: str = None):
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self._initialized = False
        self.worker_id = worker_id or str(uuid.uuid4())[:8]
        self.profile_path = None
    
    def _cleanup_chrome_processes(self, profile_path: Path | str) -> None:
        """Kill any existing Chrome processes using this profile"""
        try:
            if isinstance(profile_path, Path):
                profile_str = str(profile_path.absolute())
            else:
                profile_str = str(Path(profile_path).absolute())
            
            # Kill Chrome processes using this profile
            subprocess.run(
                ["pkill", "-f", f"user-data-dir.*{profile_str}"],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                timeout=5
            )
            # Also try killing by profile path in a different way
            subprocess.run(
                ["pkill", "-f", profile_str],
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                timeout=5
            )
            time.sleep(1)  # Give processes time to terminate
        except Exception as e:
            logger.debug(f"Error cleaning up Chrome processes: {e}")
    
    def _cleanup_profile_locks(self, profile_path: Path) -> None:
        """Remove browser lock files"""
        lock_files = [
            profile_path / "SingletonLock",
            profile_path / "lockfile",
            profile_path / "SingletonSocket",
            profile_path / "SingletonCookie"
        ]
        for lock_file in lock_files:
            if lock_file.exists():
                try:
                    lock_file.unlink()
                    logger.debug(f"Removed lock file: {lock_file.name}")
                except Exception as e:
                    logger.debug(f"Could not remove {lock_file.name}: {e}")
    
    async def initialize_with_profile_path(self, profile_path: Path) -> None:
        """Initialize browser with specific profile path"""
        if self._initialized:
            logger.info("Browser manager already initialized, skipping...")
            return
        
        try:
            # Validate profile path
            if not profile_path:
                raise ValueError("Profile path is None or empty")
            
            profile_path = Path(profile_path).resolve()  # Resolve to absolute path
            logger.info(f"Initializing browser with profile path: {profile_path}")
            
            # Check if profile path exists or can be created
            try:
                profile_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Profile directory ready: {profile_path}")
            except PermissionError as perm_error:
                logger.error(f"Permission denied creating profile directory: {perm_error}")
                raise Exception(f"Cannot create profile directory (permission denied): {profile_path}")
            except Exception as dir_error:
                logger.error(f"Failed to create profile directory: {dir_error}")
                raise Exception(f"Cannot create profile directory: {dir_error}")
            
            # Ensure Default subdirectory exists (required for Chrome profile structure)
            default_dir = profile_path / "Default"
            try:
                default_dir.mkdir(exist_ok=True)
                logger.info(f"Default directory ready: {default_dir}")
            except Exception as default_error:
                logger.error(f"Failed to create Default directory: {default_error}")
                raise Exception(f"Cannot create Default directory in profile: {default_error}")
            
            # Check if cookies exist and log info
            cookies_file = default_dir / "Cookies"
            if cookies_file.exists():
                try:
                    cookie_size = cookies_file.stat().st_size
                    logger.info(f"✓ Found existing Cookies file ({cookie_size} bytes) in profile")
                except Exception as cookie_stat_error:
                    logger.warning(f"Cookies file exists but cannot read stats: {cookie_stat_error}")
            else:
                logger.warning("⚠ No Cookies file found in profile - session may not be restored")
            
            # Check for Login Data file
            login_data_file = default_dir / "Login Data"
            if login_data_file.exists():
                logger.info("✓ Login Data file found in profile")
            else:
                logger.debug("Login Data file not found (this is OK for new profiles)")
            
            self.profile_path = profile_path
            
            # Start Playwright
            try:
                logger.info("Starting Playwright...")
                self.playwright = await async_playwright().start()
                logger.info("Playwright started successfully")
            except Exception as playwright_error:
                logger.error(f"Failed to start Playwright: {playwright_error}")
                raise Exception(f"Cannot start Playwright: {playwright_error}")
            
            # Get browser configuration
            headless = config_manager.get("browser.headless", settings.BROWSER_HEADLESS)
            viewport = config_manager.get("browser.viewport", {"width": 1920, "height": 1080})
            logger.info(f"Browser config: headless={headless}, viewport={viewport}")
            
            # Clean up any existing browser locks and processes
            logger.info(f"Cleaning up browser locks for profile: {profile_path}")
            self._cleanup_chrome_processes(profile_path)
            self._cleanup_profile_locks(profile_path)
            
            # Wait a bit more to ensure cleanup
            await asyncio.sleep(1)
            
            # Launch browser with persistent context
            # IMPORTANT: user_data_dir should point to the PARENT directory (profile_path)
            # NOT the Default subdirectory - Chrome will automatically use Default/
            user_data_dir_str = str(profile_path.absolute())
            
            # For manual login, use minimal flags to avoid interference
            # But ensure cookies and session state are preserved
            # Note: launch_persistent_context automatically uses the profile's cookies/storage
            launch_options = {
                "headless": headless,
                "viewport": viewport,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "args": [
                    # FIX: Minimal flags to match manual browser behavior
                    # Don't use --disable-blink-features=AutomationControlled as it might trigger detection
                    # Keep it as close to normal Chrome as possible
                    "--disable-dev-shm-usage",  # Docker compatibility
                    "--no-sandbox",  # Docker compatibility (required in some environments)
                    # Preserve session state
                    "--enable-features=NetworkService,NetworkServiceInProcess",
                    # Don't clear cookies/session on startup
                    # Removed --disable-background-networking and other flags that might interfere
                    # Keep it as close to normal Chrome as possible
                ],
                "ignore_https_errors": False,
                "bypass_csp": False  # Don't bypass CSP for manual login
            }
            
            # Try to use system Chrome if available
            try:
                chrome_path = Path("/usr/bin/google-chrome")
                chromium_path = Path("/usr/bin/chromium")
                if chrome_path.exists() or chromium_path.exists():
                    launch_options["channel"] = "chrome"
            except Exception:
                pass
            
            # Launch persistent context
            max_retries = 3
            retry_count = 0
            last_error = None
            
            logger.info(f"Launching browser with persistent context: {user_data_dir_str}")
            while retry_count < max_retries:
                try:
                    self.context = await self.playwright.chromium.launch_persistent_context(
                        user_data_dir_str,
                        **launch_options
                    )
                    logger.info("✓ Browser context launched successfully")
                    break
                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    error_type = type(e).__name__
                    logger.warning(f"Browser launch attempt {retry_count + 1}/{max_retries} failed: {error_type}: {error_str[:200]}")
                    
                    if ("target page, context or browser has been closed" in error_str or 
                        "existing browser session" in error_str or
                        "opening in existing browser session" in error_str or
                        "targetclosederror" in error_str):
                        retry_count += 1
                        if retry_count < max_retries:
                            logger.warning(f"Browser session conflict detected, cleaning up (attempt {retry_count}/{max_retries})...")
                            self._cleanup_chrome_processes(profile_path)
                            self._cleanup_profile_locks(profile_path)
                            await asyncio.sleep(2)
                        else:
                            logger.error(f"Failed to launch browser after {max_retries} attempts due to session conflicts")
                            raise Exception(f"Browser launch failed after {max_retries} attempts: {error_type}: {str(e)[:500]}")
                    else:
                        # Different error - log details and raise
                        logger.error(f"Browser launch failed with unexpected error: {error_type}: {str(e)}")
                        raise Exception(f"Browser launch failed: {error_type}: {str(e)[:500]}")
            
            if not self.context:
                raise Exception(f"Browser context is None after launch attempts. Last error: {last_error}")
            
            # For persistent contexts, browser might not be directly accessible
            # Try to get browser from context, but it's OK if it's None for persistent contexts
            try:
                self.browser = getattr(self.context, 'browser', None)
                if self.browser:
                    logger.info("✓ Browser object obtained from context")
                else:
                    # For persistent contexts, browser might be None - this is OK
                    # We can still use the context to create pages
                    logger.info("✓ Browser context created (persistent context - browser object may be None)")
                    # Try to create a test page to verify context works
                    try:
                        test_page = await self.context.new_page()
                        await test_page.close()
                        logger.info("✓ Context verified - can create pages")
                    except Exception as test_error:
                        logger.warning(f"Context test page creation failed: {test_error}")
                        # Don't fail here - might still work
            except Exception as browser_error:
                logger.warning(f"Could not get browser from context: {browser_error}")
                # For persistent contexts, this might be OK - try to verify context works
                try:
                    test_page = await self.context.new_page()
                    await test_page.close()
                    logger.info("✓ Context works despite browser being None")
                    self.browser = None  # Explicitly set to None
                except Exception as test_error:
                    logger.error(f"Context verification failed: {test_error}")
                    raise Exception(f"Cannot verify context works: {test_error}")
            
            self._initialized = True
            logger.info("✓ Browser manager initialized successfully with profile path")
            
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            logger.error(f"✗ Failed to initialize browser manager: {error_type}: {error_msg}")
            logger.error(f"Profile path was: {profile_path if 'profile_path' in locals() else 'unknown'}")
            
            # Clean up on failure
            try:
                if hasattr(self, 'playwright') and self.playwright:
                    await self.playwright.stop()
            except:
                pass
            
            self._initialized = False
            self.context = None
            self.browser = None
            
            raise Exception(f"Profile loading failed: {error_type}: {error_msg}")
    
    async def initialize(self) -> None:
        """Initialize Playwright and browser instance"""
        if self._initialized:
            return
        
        try:
            # Check for active profile first
            from app.services.profile_manager import ProfileManager
            profile_manager = ProfileManager()
            active_profile = profile_manager.get_active_profile()
            
            if active_profile:
                # Use active profile
                profile_path = Path(active_profile.profile_path)
                await self.initialize_with_profile_path(profile_path)
                return
            
            self.playwright = await async_playwright().start()
            
            # Get browser configuration
            headless = config_manager.get("browser.headless", settings.BROWSER_HEADLESS)
            chrome_profile_path = config_manager.get(
                "browser.chromeProfilePath",
                settings.CHROME_PROFILE_PATH
            )
            
            # Check if using existing Chrome profile
            use_existing_profile = config_manager.get("browser.useExistingProfile", False)
            existing_profile_path = config_manager.get("browser.existingProfilePath", "")
            
            viewport = config_manager.get("browser.viewport", {"width": 1920, "height": 1080})
            
            # Determine which profile to use
            if use_existing_profile and existing_profile_path:
                base_profile = Path(existing_profile_path)
                if not base_profile.exists():
                    logger.warning(f"Existing profile path not found: {existing_profile_path}, using default")
                    base_profile = Path(chrome_profile_path)
                    base_profile.mkdir(parents=True, exist_ok=True)
                    # If using default, we can create worker-specific subdirectories
                    use_worker_profile = True
                else:
                    logger.info(f"Using existing Chrome profile: {existing_profile_path}")
                    # When using existing profile, don't create subdirectories
                    # (we want to use the actual logged-in session)
                    use_worker_profile = False
            else:
                # Use default profile path
                base_profile = Path(chrome_profile_path)
                base_profile.mkdir(parents=True, exist_ok=True)
                use_worker_profile = True
            
            # For multi-worker scenarios, create a unique profile per worker
            # This prevents conflicts when multiple workers run simultaneously
            # BUT: Only do this if NOT using an existing profile (we want to share the login session)
            if use_worker_profile and (os.getenv("CELERY_WORKER_NAME") or self.worker_id != "default"):
                # Use worker-specific profile subdirectory
                profile_path = base_profile / f"worker_{self.worker_id}"
                profile_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Using worker-specific profile: {profile_path}")
            else:
                # Single worker or using existing profile - use base profile directly
                profile_path = base_profile
                logger.info(f"Using shared profile: {profile_path}")
            
            self.profile_path = profile_path
            
            # Clean up any existing browser locks and processes
            logger.info(f"Cleaning up browser locks for profile: {profile_path}")
            self._cleanup_chrome_processes(profile_path)
            self._cleanup_profile_locks(profile_path)
            
            # Wait a bit more to ensure cleanup
            await asyncio.sleep(1)
            
            # Launch browser with persistent context (for profile persistence)
            # Note: user_data_dir must be the first positional argument, not a keyword
            user_data_dir_str = str(profile_path.absolute())
            
            # Ensure Default subdirectory exists (required for Chrome profile structure)
            default_dir = profile_path / "Default"
            default_dir.mkdir(exist_ok=True)
            
            # Check if cookies exist and log info
            cookies_file = default_dir / "Cookies"
            if cookies_file.exists():
                cookie_size = cookies_file.stat().st_size
                logger.info(f"Found existing Cookies file ({cookie_size} bytes) in profile")
            else:
                logger.warning("No Cookies file found in profile - session may not be restored")
            
            # Build additional options (excluding user_data_dir)
            launch_options = {
                "headless": headless,
                "viewport": viewport,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "args": [
                    # FIX: Minimal flags to match manual browser behavior
                    # Don't use --disable-blink-features=AutomationControlled as it might trigger detection
                    # Don't use --disable-web-security as it might cause issues
                    # Keep it as close to normal Chrome as possible
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    # Preserve session state
                    "--enable-features=NetworkService,NetworkServiceInProcess"
                ],
                "ignore_https_errors": False,
                "bypass_csp": True
                # Note: launch_persistent_context automatically uses the profile's cookies/storage
            }
            
            # Try to use system Chrome if available (optional)
            try:
                chrome_path = Path("/usr/bin/google-chrome")
                chromium_path = Path("/usr/bin/chromium")
                if chrome_path.exists() or chromium_path.exists():
                    launch_options["channel"] = "chrome"
            except Exception:
                # If channel detection fails, continue without it
                pass
            
            # Call launch_persistent_context with user_data_dir as first positional arg
            user_data_dir_str = str(profile_path.absolute())
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    self.context = await self.playwright.chromium.launch_persistent_context(
                        user_data_dir_str,
                        **launch_options
                    )
                    break  # Success, exit retry loop
                except Exception as e:
                    error_str = str(e).lower()
                    if ("target page, context or browser has been closed" in error_str or 
                        "existing browser session" in error_str or
                        "opening in existing browser session" in error_str):
                        retry_count += 1
                        if retry_count < max_retries:
                            logger.warning(f"Browser session conflict detected (attempt {retry_count}/{max_retries}), cleaning up...")
                            self._cleanup_chrome_processes(profile_path)
                            self._cleanup_profile_locks(profile_path)
                            await asyncio.sleep(2)
                        else:
                            logger.error(f"Failed to launch browser after {max_retries} attempts")
                            raise
                    else:
                        # Different error, don't retry
                        raise
            
            # Get browser from context (persistent context has browser property)
            self.browser = self.context.browser
            
            self._initialized = True
            logger.info("Browser manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser manager: {e}")
            raise
    
    async def new_page(self) -> Page:
        """Create a new page in the browser context"""
        if not self._initialized:
            await self.initialize()
        
        return await self.context.new_page()
    
    async def ensure_logged_in(self) -> bool:
        """
        Check if user is logged in to Google Flow.
        Returns True if logged in, False otherwise.
        """
        page = await self.new_page()
        
        try:
            flow_url = config_manager.get("flow.url", settings.FLOW_URL)
            await page.goto(flow_url)
            await page.wait_for_timeout(2000)
            
            # Check for login indicators
            has_login_prompt = await page.locator('text=Sign in').count() > 0
            has_flow_ui = await page.locator('main, [role="main"]').count() > 0
            
            is_logged_in = has_flow_ui and not has_login_prompt
            
            if not is_logged_in:
                logger.info("User not logged in. Manual login required.")
            
            return is_logged_in
            
        except Exception as e:
            logger.error(f"Error checking login status: {e}")
            return False
        finally:
            await page.close()
    
    async def close(self) -> None:
        """Close browser and cleanup resources"""
        try:
            # Close all pages first
            if self.context:
                pages = self.context.pages
                for page in pages:
                    try:
                        if not page.is_closed():
                            await page.close()
                    except:
                        pass
            
            # For persistent context, close the context (which closes the browser)
            if self.context:
                try:
                    await self.context.close()
                except:
                    pass
            elif self.browser:
                try:
                    await self.browser.close()
                except:
                    pass
            
            # Clean up profile locks after closing
            if self.profile_path:
                await asyncio.sleep(0.5)  # Give browser time to release locks
                self._cleanup_profile_locks(self.profile_path)
            
            if self.playwright:
                try:
                    await self.playwright.stop()
                except:
                    pass
            
            self._initialized = False
            self.context = None
            self.browser = None
            logger.info("Browser manager closed")
        except Exception as e:
            logger.error(f"Error closing browser manager: {e}")
            # Force cleanup even on error
            self._initialized = False
            self.context = None
            self.browser = None

