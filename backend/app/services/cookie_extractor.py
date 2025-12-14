"""
Cookie Extractor Service - Extracts and saves cookies from browser
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional
from playwright.async_api import BrowserContext, Page
from app.services.browser_manager import BrowserManager
from app.services.flow_controller import FlowController
from app.config import config_manager, settings

logger = logging.getLogger(__name__)


class CookieExtractor:
    """Extracts cookies from browser and verifies login status"""
    
    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager
    
    async def extract_cookies_from_context(self, context: BrowserContext) -> List[Dict]:
        """Extract all cookies from browser context"""
        try:
            cookies = await context.cookies()
            logger.info(f"Extracted {len(cookies)} cookies from browser context")
            return cookies
        except Exception as e:
            logger.error(f"Failed to extract cookies: {e}")
            raise
    
    async def extract_cookies_from_page(self, page: Page) -> List[Dict]:
        """Extract cookies from specific page"""
        try:
            context = page.context
            cookies = await context.cookies()
            logger.info(f"Extracted {len(cookies)} cookies from page")
            return cookies
        except Exception as e:
            logger.error(f"Failed to extract cookies from page: {e}")
            raise
    
    async def save_cookies_to_context(self, context: BrowserContext, cookies: List[Dict]) -> bool:
        """Save cookies to browser context"""
        try:
            await context.add_cookies(cookies)
            logger.info(f"Saved {len(cookies)} cookies to browser context")
            return True
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
            return False
    
    async def verify_login_status(self, page: Page) -> bool:
        """Verify if user is logged in to Google Flow - non-intrusive check only"""
        try:
            # Don't navigate - just check current page state
            # This prevents any interference with user's manual login
            
            current_url = page.url
            logger.info(f"Verifying Flow login status. Current URL: {current_url}")
            
            # If we're on accounts.google.com, definitely not logged in
            if "accounts.google.com" in current_url and "/signin" in current_url:
                logger.info("On Google sign-in page - not logged in")
                return False
            
            # More flexible Flow URL check - Flow can be on different paths
            # Flow URLs can be:
            # - https://labs.google/fx/tools/flow
            # - https://labs.google/fx/vi/tools/flow (with "vi" variant)
            # - https://labs.google.com/fx/tools/flow
            is_flow_url = (
                ("labs.google.com" in current_url or "labs.google" in current_url) and 
                ("/fx/" in current_url and "/tools/flow" in current_url) and
                "accounts.google.com" not in current_url
            )
            
            if is_flow_url:
                logger.info("On Flow page - checking login indicators...")
                
                # Wait a bit for page to fully load
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=5000)
                except:
                    pass
                
                # Check for login indicators (non-intrusive - just count, don't interact)
                # Only count VISIBLE login indicators
                login_text_count = 0
                login_google_count = 0
                login_link_count = 0
                
                try:
                    login_text_locators = page.locator('text=Sign in')
                    for i in range(await login_text_locators.count()):
                        if await login_text_locators.nth(i).is_visible():
                            login_text_count += 1
                except:
                    pass
                
                try:
                    login_google_locators = page.locator('text=Sign in with Google')
                    for i in range(await login_google_locators.count()):
                        if await login_google_locators.nth(i).is_visible():
                            login_google_count += 1
                except:
                    pass
                
                try:
                    login_link_locators = page.locator('a[href*="accounts.google.com"]')
                    for i in range(await login_link_locators.count()):
                        if await login_link_locators.nth(i).is_visible():
                            login_link_count += 1
                except:
                    pass
                
                total_login_indicators = login_text_count + login_google_count + login_link_count
                
                # Check for prompt inputs (indicates logged in)
                # Count both visible and hidden inputs (they might be in a collapsed state)
                prompt_inputs = 0
                try:
                    input_locators = page.locator('textarea, [contenteditable="true"], [contenteditable], [role="textbox"]')
                    prompt_inputs = await input_locators.count()
                except:
                    pass
                
                # Also check for common Flow UI elements that indicate logged in
                flow_ui_elements = 0
                try:
                    # Check for common Flow UI elements
                    flow_ui_locators = page.locator('[class*="flow"], [class*="prompt"], [class*="generate"], [id*="flow"]')
                    flow_ui_elements = await flow_ui_locators.count()
                except:
                    pass
                
                # Logged in if:
                # 1. We have prompt inputs OR Flow UI elements, AND
                # 2. No visible login indicators
                is_logged_in = (prompt_inputs > 0 or flow_ui_elements > 0) and total_login_indicators == 0
                
                logger.info(f"Flow login check: logged_in={is_logged_in}, inputs={prompt_inputs}, flow_ui={flow_ui_elements}, login_indicators={total_login_indicators} (text={login_text_count}, google={login_google_count}, links={login_link_count})")
                
                # If we're on Flow page but can't determine, assume logged in (user might have logged in manually)
                # This is important because after manual login, the page might not have loaded all elements yet
                if not is_logged_in:
                    # If we're on Flow page and no login indicators, likely logged in
                    if total_login_indicators == 0:
                        logger.info("On Flow page with no login indicators - assuming logged in")
                        is_logged_in = True
                    else:
                        # Check page title and content for more clues
                        try:
                            page_title = await page.title()
                            page_content = await page.content()
                            # If page title has "Flow" and no sign-in content, likely logged in
                            if "Flow" in page_title and "accounts.google.com" not in page_content and "Sign in" not in page_content:
                                logger.info("Page title and content suggest logged in")
                                is_logged_in = True
                        except:
                            pass
                
                return is_logged_in
            
            # If we're on mail.google.com, assume logged in
            if "mail.google.com" in current_url:
                logger.info("On Gmail page - assuming logged in")
                return True
            
            # Default: not logged in
            logger.warning(f"Unknown URL pattern: {current_url} - assuming not logged in")
            return False
            
        except Exception as e:
            logger.error(f"Failed to verify login status: {e}", exc_info=True)
            # On error, if we're on a Flow-like URL, assume logged in (user might have logged in manually)
            try:
                current_url = page.url
                if "labs.google.com" in current_url and "accounts.google.com" not in current_url:
                    logger.warning("Error checking login, but on Flow page - assuming logged in")
                    return True
            except:
                pass
            return False
    
    async def verify_gmail_login(self, page: Page) -> bool:
        """Verify if user is logged in to Gmail - non-intrusive check only"""
        try:
            # Don't navigate - just check current page state
            # This prevents any interference with user's manual login
            
            current_url = page.url
            
            # If we're on accounts.google.com, definitely not logged in
            if "accounts.google.com" in current_url:
                return False
            
            # If we're on mail.google.com, check for login button
            if "mail.google.com" in current_url:
                try:
                    has_login = await page.locator('text=Sign in').count() > 0
                    is_logged_in = not has_login
                    logger.info(f"Gmail login status (non-intrusive): logged_in={is_logged_in}")
                    return is_logged_in
                except:
                    # If we can't check, assume logged in if we're on mail.google.com
                    return True
            
            # Default: not logged in
            return False
            
        except Exception as e:
            logger.error(f"Failed to verify Gmail login: {e}")
            return False

