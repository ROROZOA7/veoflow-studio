"""
Guided Login Service - Manages guided login flow with browser tabs
"""

import logging
import asyncio
from pathlib import Path
from typing import Dict, Optional
from playwright.async_api import Page, BrowserContext
from app.services.browser_manager import BrowserManager
from app.services.cookie_extractor import CookieExtractor
from app.services.flow_controller import FlowController
from app.services.profile_manager import ProfileManager
from app.core.database import SessionLocal
from app.config import config_manager, settings

logger = logging.getLogger(__name__)


class GuidedLoginService:
    """Manages guided login flow with step-by-step instructions"""
    
    def __init__(self):
        self.profile_manager = ProfileManager()
        self.browser_managers: Dict[str, BrowserManager] = {}
        self.browser_contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Dict[str, Page]] = {}  # {profile_id: {"gmail": page, "flow": page}}
    
    async def open_browser_with_profile(self, profile_id: str) -> Dict:
        """Open browser with specific profile"""
        try:
            profile = self.profile_manager.get_profile(profile_id)
            if not profile:
                raise ValueError(f"Profile {profile_id} not found")
            
            # Initialize browser manager with profile
            browser_manager = BrowserManager(worker_id=f"profile-{profile_id}")
            await browser_manager.initialize_with_profile_path(Path(profile.profile_path))
            
            # Store references
            self.browser_managers[profile_id] = browser_manager
            self.browser_contexts[profile_id] = browser_manager.context
            self.pages[profile_id] = {}
            
            logger.info(f"Opened browser with profile: {profile.name}")
            
            return {
                "success": True,
                "message": f"Browser opened with profile: {profile.name}",
                "profile_id": profile_id,
                "profile_name": profile.name
            }
            
        except Exception as e:
            logger.error(f"Failed to open browser with profile: {e}")
            raise
    
    async def open_gmail_tab(self, profile_id: str) -> Dict:
        """Open Gmail login tab - just opens the URL, no automation"""
        try:
            if profile_id not in self.browser_contexts:
                await self.open_browser_with_profile(profile_id)
            
            context = self.browser_contexts[profile_id]
            page = await context.new_page()
            
            gmail_url = "https://accounts.google.com/signin/v2/identifier?continue=https%3A%2F%2Fmail.google.com%2Fmail&flowName=GlifWebSignIn&flowEntry=ServiceLogin"
            
            # Just navigate to URL and let user interact manually
            # Don't wait for anything - just open and leave it alone
            await page.goto(gmail_url, wait_until="domcontentloaded", timeout=30000)
            
            # Store page reference (but don't interact with it)
            if profile_id not in self.pages:
                self.pages[profile_id] = {}
            self.pages[profile_id]["gmail"] = page
            
            logger.info(f"Opened Gmail tab for profile: {profile_id} - user can now log in manually")
            
            return {
                "success": True,
                "message": "Gmail login page opened. Please log in manually in the browser window.",
                "url": gmail_url
            }
            
        except Exception as e:
            logger.error(f"Failed to open Gmail tab: {e}")
            raise
    
    async def open_flow_tab(self, profile_id: str) -> Dict:
        """Open Flow login tab - just opens the URL, no automation"""
        try:
            if profile_id not in self.browser_contexts:
                await self.open_browser_with_profile(profile_id)
            
            context = self.browser_contexts[profile_id]
            page = await context.new_page()
            
            flow_url = config_manager.get("flow.url", settings.FLOW_URL)
            
            # Just navigate to URL and let user interact manually
            # Don't wait for anything - just open and leave it alone
            await page.goto(flow_url, wait_until="domcontentloaded", timeout=30000)
            
            # Store page reference (but don't interact with it)
            if profile_id not in self.pages:
                self.pages[profile_id] = {}
            self.pages[profile_id]["flow"] = page
            
            logger.info(f"Opened Flow tab for profile: {profile_id} - user can now log in manually")
            
            return {
                "success": True,
                "message": "Flow page opened. Please log in manually in the browser window.",
                "url": flow_url
            }
            
        except Exception as e:
            logger.error(f"Failed to open Flow tab: {e}")
            raise
    
    async def check_login_status(self, profile_id: str) -> Dict:
        """Check login status for both Gmail and Flow - non-intrusive check only"""
        try:
            result = {
                "gmail_logged_in": False,
                "flow_logged_in": False,
                "both_logged_in": False
            }
            
            if profile_id not in self.pages:
                return result
            
            pages = self.pages[profile_id]
            cookie_extractor = CookieExtractor(self.browser_managers[profile_id])
            
            # Check Gmail - just check current URL and page content, don't navigate
            if "gmail" in pages:
                try:
                    page = pages["gmail"]
                    # Just check current state without navigating or interacting
                    current_url = page.url
                    # Simple check: if we're on mail.google.com and not on login page
                    if "mail.google.com" in current_url and "accounts.google.com" not in current_url:
                        result["gmail_logged_in"] = True
                    else:
                        # Check if login button exists (means not logged in)
                        try:
                            login_count = await page.locator('text=Sign in').count()
                            result["gmail_logged_in"] = login_count == 0
                        except:
                            # If we can't check, assume not logged in
                            result["gmail_logged_in"] = False
                except Exception as e:
                    logger.warning(f"Could not check Gmail login: {e}")
            
            # Check Flow - just check current URL and page content, don't navigate
            if "flow" in pages:
                try:
                    page = pages["flow"]
                    
                    # Check if page is still open
                    if page.is_closed():
                        logger.warning("Flow page is closed, cannot check login status")
                        result["flow_logged_in"] = False
                    else:
                        # Use CookieExtractor's verify_login_status for consistent checking
                        try:
                            result["flow_logged_in"] = await cookie_extractor.verify_login_status(page)
                            logger.info(f"Flow login status: {result['flow_logged_in']}")
                        except Exception as check_error:
                            logger.error(f"Error checking Flow login status: {check_error}", exc_info=True)
                            # If we can't check but we're on the flow page, assume logged in
                            # (user might have logged in manually)
                            try:
                                current_url = page.url
                                # Use same flexible Flow URL pattern
                                is_flow_url = (
                                    ("labs.google.com" in current_url or "labs.google" in current_url) and 
                                    ("/fx/" in current_url and "/tools/flow" in current_url) and
                                    "accounts.google.com" not in current_url
                                )
                                if is_flow_url:
                                    result["flow_logged_in"] = True
                                    logger.info("Assuming Flow is logged in (on Flow page but check failed)")
                                else:
                                    result["flow_logged_in"] = False
                            except:
                                result["flow_logged_in"] = False
                except Exception as e:
                    logger.error(f"Could not check Flow login: {e}", exc_info=True)
                    result["flow_logged_in"] = False
            
            result["both_logged_in"] = result["gmail_logged_in"] and result["flow_logged_in"]
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to check login status: {e}")
            return {
                "gmail_logged_in": False,
                "flow_logged_in": False,
                "both_logged_in": False,
                "error": str(e)
            }
    
    async def confirm_login_and_save(self, profile_id: str) -> Dict:
        """Extract cookies and save to profile"""
        try:
            if profile_id not in self.browser_contexts:
                raise ValueError(f"No browser context found for profile {profile_id}")
            
            context = self.browser_contexts[profile_id]
            cookie_extractor = CookieExtractor(self.browser_managers[profile_id])
            
            # Extract all cookies from context
            cookies = await cookie_extractor.extract_cookies_from_context(context)
            
            if not cookies:
                return {
                    "success": False,
                    "message": "No cookies found. Please make sure you're logged in.",
                    "cookies_count": 0
                }
            
            # Verify login status
            login_status = await self.check_login_status(profile_id)
            
            if not login_status["both_logged_in"]:
                return {
                    "success": False,
                    "message": "Not fully logged in. Please complete login for both Gmail and Flow.",
                    "login_status": login_status,
                    "cookies_count": len(cookies)
                }
            
            # Cookies are automatically saved in the Chrome profile directory
            # The profile path already contains the cookies in the Default/Cookies file
            # We just need to verify they're there
            
            logger.info(f"Login confirmed for profile {profile_id}. Cookies saved to profile.")
            
            # Update profile metadata
            profile = self.profile_manager.get_profile(profile_id)
            if profile:
                db = SessionLocal()
                try:
                    profile.profile_metadata = profile.profile_metadata or {}
                    profile.profile_metadata["cookies_saved"] = True
                    profile.profile_metadata["cookies_count"] = len(cookies)
                    profile.profile_metadata["last_login_check"] = asyncio.get_event_loop().time()
                    db.commit()
                except Exception as e:
                    logger.warning(f"Failed to update profile metadata: {e}")
                finally:
                    db.close()
            
            return {
                "success": True,
                "message": "Login confirmed and cookies saved successfully!",
                "cookies_count": len(cookies),
                "login_status": login_status
            }
            
        except Exception as e:
            logger.error(f"Failed to confirm login and save: {e}")
            raise
    
    async def close_profile_browser(self, profile_id: str) -> None:
        """Close browser for specific profile"""
        try:
            if profile_id in self.browser_managers:
                await self.browser_managers[profile_id].close()
                del self.browser_managers[profile_id]
            
            if profile_id in self.browser_contexts:
                del self.browser_contexts[profile_id]
            
            if profile_id in self.pages:
                del self.pages[profile_id]
            
            logger.info(f"Closed browser for profile: {profile_id}")
            
        except Exception as e:
            logger.error(f"Failed to close browser: {e}")

