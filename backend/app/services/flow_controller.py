"""
Flow Controller Service - Handles Google Flow UI automation
"""

from playwright.async_api import Page
from app.config import config_manager, settings, FLOW_URL, FLOW_SELECTORS, POLLING_INTERVAL_MS, IMAGES_PATH
import asyncio
import logging
import os
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def get_screenshot_path(filename: str) -> str:
    """Get path for screenshot in images directory"""
    # Use images directory from config
    images_dir = Path(IMAGES_PATH)
    images_dir.mkdir(parents=True, exist_ok=True)
    return str(images_dir / filename)


class FlowController:
    """Controls interaction with Google Flow UI"""
    
    def __init__(self, browser_manager):
        self.browser_manager = browser_manager
    
    async def navigate_to_flow(self, page: Page) -> None:
        """Navigate to Flow project page and wait for UI to load"""
        try:
            flow_url = config_manager.get("flow.url", FLOW_URL)
            logger.info(f"Navigating to {flow_url}")
            
            # FIX: Verify cookies are loaded from profile BEFORE navigation
            # This ensures the session is properly restored from the profile
            try:
                cookies = await page.context.cookies()
                logger.info(f"Current session has {len(cookies)} cookies before navigation")
                # Log domain info for debugging
                google_cookies = [c for c in cookies if "google.com" in c.get("domain", "")]
                if google_cookies:
                    logger.info(f"✓ Found {len(google_cookies)} Google cookies in session - profile session loaded correctly")
                    
                    # Verify we have authentication cookies (not just tracking cookies)
                    auth_cookies = [c for c in google_cookies if any(auth_name in c.get("name", "").lower() for auth_name in ["sid", "session", "auth", "oauth", "login"])]
                    if auth_cookies:
                        logger.info(f"✓ Found {len(auth_cookies)} authentication cookies - session appears valid")
                    else:
                        logger.warning("⚠ No authentication cookies found - session may not be fully restored")
                else:
                    logger.error("✗ No Google cookies found in session - profile session NOT loaded correctly!")
                    logger.error("This may cause login redirects or credit loading errors")
                    # Don't fail here, but log the issue clearly
            except Exception as cookie_check_error:
                logger.warning(f"Could not check cookies before navigation: {cookie_check_error}")
                logger.warning("This may indicate profile session is not properly loaded")
            
            # FIX: Make navigation as simple as possible - match manual browser navigation
            # Don't add init scripts or extra headers that might trigger detection or cause issues
            # When user manually opens URL in new tab, there are no init scripts or extra headers
            # This is why manual navigation works but automated navigation has issues
            
            # CRITICAL: Check if page/context is still alive before navigation
            try:
                if page.is_closed():
                    raise Exception("Page is already closed before navigation")
                
                # Check context - for persistent contexts, browser might be None (which is OK)
                context = page.context
                if not context:
                    raise Exception("Page context is None")
                
                # For persistent contexts, browser might be None - verify context works instead
                browser = getattr(context, 'browser', None)
                if browser:
                    # Browser exists - check if connected
                    if not browser.is_connected():
                        raise Exception("Browser is not connected")
                    logger.debug("Browser context is connected (browser object exists)")
                else:
                    # Browser is None (normal for persistent contexts) - verify context works
                    logger.debug("Browser object is None (normal for persistent contexts), verifying context...")
                    try:
                        # Try to get pages count as a test
                        pages = context.pages
                        logger.debug(f"Context verified - has {len(pages)} pages")
                    except Exception as context_test_error:
                        raise Exception(f"Context is not usable: {context_test_error}")
                    
            except Exception as pre_check_error:
                logger.error(f"Pre-navigation check failed: {pre_check_error}")
                raise Exception(f"Browser/page not ready for navigation: {pre_check_error}")
            
            # FIX: Simple navigation like check_session.py - no init scripts, no extra headers
            # This matches how a user manually opens the URL in a new tab
            logger.info("Navigating to Flow with simple navigation (matching manual browser behavior)...")
            
            # Retry navigation with exponential backoff for network errors and closed targets
            max_retries = 5  # Increased retries for closed target errors
            for attempt in range(max_retries):
                try:
                    # Re-check if page is still alive before each attempt
                    if page.is_closed():
                        logger.warning(f"Page closed before attempt {attempt + 1}, recreating...")
                        # Page is closed, we need to get a new one from render_manager
                        raise Exception("Page closed - needs recreation")
                    
                    # FIX: Don't set extra headers or init scripts - keep it simple like manual navigation
                    # Just navigate directly, same as check_session.py does
                    await page.goto(
                        flow_url,
                        wait_until="domcontentloaded",
                        timeout=60000
                    )
                    
                    # Wait a bit for any redirects or session restoration
                    await asyncio.sleep(2)
                    
                    # Check if we were redirected to login
                    current_url = page.url
                    if "accounts.google.com" in current_url or "/signin" in current_url:
                        logger.warning(f"Redirected to login page: {current_url}")
                        # Take screenshot for debugging
                        try:
                            screenshot_path = get_screenshot_path(f"flow_login_redirect_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                            await page.screenshot(path=screenshot_path, full_page=True)
                            logger.warning(f"Login redirect screenshot saved to {screenshot_path}")
                        except:
                            pass
                        
                        # FIX: Handle login redirect properly
                        # Check if browser is in headless mode (use module-level imports)
                        headless = config_manager.get("browser.headless", settings.BROWSER_HEADLESS)
                        
                        if headless:
                            # In headless mode, can't do manual login - raise error
                            logger.error("Login redirect detected in headless mode. Cannot perform manual login.")
                            logger.error("Solutions:")
                            logger.error("1. Set browser.headless=false in config to allow manual login")
                            logger.error("2. Log in manually in a regular browser, then use setup_chrome_profile.sh to copy your logged-in profile")
                            raise Exception(f"Login required but browser is in headless mode. Please log in manually first, then use setup_chrome_profile.sh to copy your logged-in profile. Redirect URL: {current_url}")
                        else:
                            # In non-headless mode, wait for user to log in manually
                            logger.warning("Login redirect detected. Waiting for manual login (up to 60 seconds)...")
                            logger.warning("Please log in to Google in the browser window that opened.")
                            
                            # Wait for login to complete (check if URL changes back to Flow)
                            login_wait_timeout = 60  # seconds
                            login_check_interval = 2  # seconds
                            login_waited = 0
                            login_completed = False
                            
                            while login_waited < login_wait_timeout:
                                await asyncio.sleep(login_check_interval)
                                login_waited += login_check_interval
                                
                                try:
                                    current_url_after_wait = page.url
                                    # Check if we're back on Flow page (not login page)
                                    if ("labs.google.com" in current_url_after_wait or "labs.google" in current_url_after_wait) and \
                                       ("/fx/" in current_url_after_wait or "/tools/flow" in current_url_after_wait) and \
                                       "accounts.google.com" not in current_url_after_wait:
                                        logger.info(f"✓ Login completed! Back on Flow page: {current_url_after_wait}")
                                        login_completed = True
                                        break
                                    
                                    # Also check if login page disappeared (user might have logged in)
                                    if "accounts.google.com" not in current_url_after_wait and "/signin" not in current_url_after_wait:
                                        # Might be on Flow page - verify
                                        await asyncio.sleep(2)  # Wait a bit more for redirect
                                        final_url = page.url
                                        if ("labs.google" in final_url and "flow" in final_url) or \
                                           ("labs.google" in final_url and "/fx/" in final_url):
                                            logger.info(f"✓ Login completed! On Flow page: {final_url}")
                                            login_completed = True
                                            break
                                except Exception as check_error:
                                    logger.debug(f"Error checking login status: {check_error}")
                                    continue
                            
                            if not login_completed:
                                # Login timeout - try to navigate back to Flow anyway
                                logger.warning("Login wait timeout. Attempting to navigate back to Flow...")
                                try:
                                    flow_url = config_manager.get("flow.url", FLOW_URL)
                                    await page.goto(flow_url, wait_until="domcontentloaded", timeout=30000)
                                    await asyncio.sleep(3)
                                    
                                    # Check if we're now on Flow page
                                    final_check_url = page.url
                                    if ("labs.google" in final_check_url and "flow" in final_check_url) or \
                                       ("labs.google" in final_check_url and "/fx/" in final_check_url):
                                        logger.info(f"✓ Successfully navigated to Flow after login: {final_check_url}")
                                        login_completed = True
                                    else:
                                        logger.error(f"Still not on Flow page after navigation: {final_check_url}")
                                        raise Exception(f"Login timeout. Please log in manually and try again. Current URL: {final_check_url}")
                                except Exception as nav_error:
                                    logger.error(f"Failed to navigate back to Flow after login: {nav_error}")
                                    raise Exception(f"Login required but not completed within {login_wait_timeout} seconds. Please log in manually and try again. Error: {nav_error}")
                            
                            # Verify login status using cookie extractor
                            if login_completed:
                                try:
                                    from app.services.cookie_extractor import CookieExtractor
                                    cookie_extractor = CookieExtractor(self.browser_manager)
                                    is_logged_in = await cookie_extractor.verify_login_status(page)
                                    
                                    if is_logged_in:
                                        logger.info("✓ Login verified - user is logged in to Flow")
                                        
                                        # Extract and log new cookies (they might have been refreshed)
                                        try:
                                            cookies = await page.context.cookies()
                                            google_cookies = [c for c in cookies if "google.com" in c.get("domain", "")]
                                            logger.info(f"Session has {len(cookies)} cookies ({len(google_cookies)} Google cookies) after login")
                                        except:
                                            pass
                                    else:
                                        logger.warning("Login status verification failed - but continuing anyway")
                                except Exception as verify_error:
                                    logger.warning(f"Could not verify login status: {verify_error} - continuing anyway")
                    
                    # Check if we're on Flow page (not login page) before breaking
                    final_url_check = page.url
                    if "accounts.google.com" in final_url_check or "/signin" in final_url_check:
                        # Still on login page - this shouldn't happen if login was handled above
                        if attempt < max_retries - 1:
                            logger.warning(f"Still on login page after handling, retrying navigation (attempt {attempt + 1}/{max_retries})...")
                            await asyncio.sleep(3)
                            continue
                        else:
                            raise Exception(f"Still on login page after all attempts. Please log in manually first. URL: {final_url_check}")
                    
                    break  # Success, exit retry loop
                except Exception as e:
                    error_str = str(e).lower()
                    error_type = type(e).__name__
                    
                    # Handle closed target errors specially
                    if ("target" in error_str and "closed" in error_str) or "TargetClosedError" in error_type:
                        if attempt < max_retries - 1:
                            wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s, 8s
                            logger.warning(f"Target closed error on attempt {attempt + 1}/{max_retries}: {e}")
                            logger.warning(f"Waiting {wait_time}s and checking browser state...")
                            
                            # Check browser manager state
                            try:
                                if hasattr(self, 'browser_manager') and self.browser_manager:
                                    context = self.browser_manager.context
                                    if context:
                                        # For persistent contexts, browser might be None - check context instead
                                        browser = getattr(context, 'browser', None)
                                        if browser:
                                            if not browser.is_connected():
                                                logger.error("Browser context disconnected - cannot recover")
                                                raise Exception("Browser context disconnected")
                                            logger.info("Browser context still connected, will retry with new page")
                                        else:
                                            # Browser is None (normal for persistent contexts) - verify context works
                                            try:
                                                pages = context.pages
                                                logger.info(f"Browser context verified (browser=None, {len(pages)} pages), will retry with new page")
                                            except Exception as context_test_error:
                                                logger.error(f"Context not usable: {context_test_error}")
                                                raise Exception(f"Context not usable: {context_test_error}")
                                    else:
                                        logger.warning("Browser context is None")
                            except Exception as state_check_error:
                                logger.debug(f"Browser state check failed: {state_check_error}")
                                # Don't raise here, just log - let the retry continue
                            
                            await asyncio.sleep(wait_time)
                            
                            # Try to get a new page if current one is closed
                            if page.is_closed():
                                logger.warning("Page is closed, need to get new page from browser manager")
                                # FIX: Raise a specific exception that render_manager can catch and handle
                                raise Exception("Page closed - needs new page")  # This will be caught by render_manager
                            
                            # Continue to retry
                            continue
                        else:
                            logger.error(f"Target closed error after {max_retries} attempts: {e}")
                            raise Exception(f"Browser/page closed during navigation after {max_retries} attempts. This may indicate the browser crashed or was closed externally.")
                    
                    # Handle network errors
                    elif ("err_network_changed" in error_str or 
                        "net::err" in error_str or
                        "navigation" in error_str) and attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        logger.warning(f"Network error on attempt {attempt + 1}: {e}. Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        # Try to reload the page context if page is still alive
                        try:
                            if not page.is_closed():
                                await page.reload(wait_until="domcontentloaded", timeout=30000)
                        except:
                            pass
                    else:
                        # Last attempt or different error - raise it
                        logger.error(f"Navigation failed after {attempt + 1} attempts: {e}")
                        raise
            
            # FIX: Wait for page to fully load and settle before checking for errors
            # This ensures cookies are loaded and credit information has time to load
            logger.info("Waiting for page to fully load and settle...")
            
            # Step 1: Wait for initial page load
            try:
                await page.wait_for_load_state("networkidle", timeout=30000)
                logger.info("✓ Page network idle")
            except:
                # If networkidle times out, try domcontentloaded
                try:
                    await page.wait_for_load_state("domcontentloaded", timeout=10000)
                    logger.info("✓ Page DOM content loaded")
                except:
                    logger.warning("Page load timeout - continuing anyway")
                # Give it a bit more time
                await asyncio.sleep(2)
            
            # Step 2: Flow is a Next.js/React app - wait for React to hydrate
            logger.info("Waiting for React app to hydrate...")
            await asyncio.sleep(3)
            
            # Wait for React root or main content to appear
            try:
                # Wait for React to render - look for common React indicators
                await page.wait_for_function(
                    """
                    () => {
                        // Check if React has rendered
                        const hasReactRoot = document.querySelector('#__next') || 
                                           document.querySelector('[data-reactroot]') ||
                                           document.querySelector('main') ||
                                           document.body.querySelector('div[id]');
                        return hasReactRoot !== null;
                    }
                    """,
                    timeout=15000
                )
                logger.info("✓ React app detected")
            except:
                logger.warning("React detection timeout - continuing anyway")
            
            # Step 3: CRITICAL FIX - Wait for credit information to load (or timeout gracefully)
            # Credit loading errors appear because we check too early before credits finish loading
            logger.info("Waiting for credit information to load (up to 10 seconds)...")
            credit_load_wait_time = 10  # seconds
            credit_check_interval = 1  # seconds
            credit_loaded = False
            
            for wait_attempt in range(credit_load_wait_time):
                try:
                    # Check if credit loading is complete by looking for:
                    # 1. No "loading" indicators for credits
                    # 2. Credit information is visible (or error is stable)
                    # 3. No active network requests for credit endpoints
                    
                    # Check for credit loading indicators
                    loading_indicators = await page.locator('[class*="loading"], [class*="spinner"], [aria-busy="true"]').count()
                    
                    # Check if credit error is already present (stable error, not transient)
                    credit_error_count = await page.locator('text=Không tải được số tín dụng').count()
                    
                    # If no loading indicators and either credits loaded OR error is stable, we're done
                    if loading_indicators == 0:
                        # Wait a bit more to ensure it's not just a brief pause
                        await asyncio.sleep(2)
                        # Check again
                        loading_indicators_after = await page.locator('[class*="loading"], [class*="spinner"], [aria-busy="true"]').count()
                        if loading_indicators_after == 0:
                            credit_loaded = True
                            logger.info(f"✓ Credit information loaded (or error is stable) after {wait_attempt + 1} seconds")
                            break
                except Exception as credit_check_error:
                    logger.debug(f"Credit check error: {credit_check_error}")
                
                await asyncio.sleep(credit_check_interval)
            
            if not credit_loaded:
                logger.warning(f"Credit information may still be loading after {credit_load_wait_time} seconds - continuing anyway")
            
            # Step 4: Additional wait for dynamic content and error popups to appear
            logger.info("Waiting for dynamic content and error popups to settle...")
            await asyncio.sleep(3)
            
            # FIX 2: Detect if we're on gallery view (project grid) vs editor view
            logger.info("Checking current page state (gallery vs editor)...")
            is_gallery_view = False
            is_editor_view = False
            
            try:
                # Check for gallery indicators (project cards, thumbnails, grid)
                gallery_indicators = [
                    'img[alt*="project"]',
                    '[class*="gallery"]',
                    '[class*="thumbnail"]',
                    '[class*="grid"]',
                    '[class*="card"]',
                    'button:has-text("Dự án mới")',  # Vietnamese "New project" button
                    'button:has-text("New project")'
                ]
                
                gallery_count = 0
                for indicator in gallery_indicators:
                    try:
                        count = await page.locator(indicator).count()
                        if count > 0:
                            gallery_count += count
                    except:
                        pass
                
                # Check for editor indicators (prompt input, textarea)
                editor_indicators = [
                    "textarea",
                    "[contenteditable='true']",
                    "[role='textbox']",
                    "[placeholder*='prompt']",
                    "[placeholder*='Describe']"
                ]
                
                editor_count = 0
                for indicator in editor_indicators:
                    try:
                        count = await page.locator(indicator).count()
                        if count > 0:
                            editor_count += count
                    except:
                        pass
                
                is_gallery_view = gallery_count > 0 and editor_count == 0
                is_editor_view = editor_count > 0
                
                logger.info(f"Page state: gallery={is_gallery_view}, editor={is_editor_view} (gallery_indicators={gallery_count}, editor_indicators={editor_count})")
                
                if is_gallery_view:
                    logger.info("✓ Detected gallery/project grid view - will need to click 'New project'")
                elif is_editor_view:
                    logger.info("✓ Detected editor view - ready for prompt injection")
                else:
                    logger.warning("? Unknown page state - will attempt to proceed")
            except Exception as state_check_error:
                logger.debug(f"Error checking page state: {state_check_error}")
            
            # Try to wait for any interactive elements
            try:
                # Wait for any form, input, or button to appear
                await page.wait_for_selector(
                    "textarea, input, button, [contenteditable], [role='textbox']",
                    timeout=10000,
                    state="attached"
                )
                logger.info("Interactive elements detected")
            except:
                logger.warning("No interactive elements found yet - will try anyway")
            
            await asyncio.sleep(2)
            
            # Check for Google authentication errors (500, 403, etc.)
            current_url = page.url
            page_title = await page.title()
            
            # Check for Google error pages
            if "accounts.google.com" in current_url:
                error_indicators = [
                    "500",
                    "That's an error",
                    "Server Error",
                    "Error 500",
                    "There was an error"
                ]
                
                page_text = ""
                try:
                    page_text = await page.locator("body").text_content() or ""
                except:
                    pass
                
                for error_indicator in error_indicators:
                    if error_indicator in page_title or error_indicator in page_text:
                        logger.error(f"Google authentication error detected: {error_indicator}")
                        logger.error(f"Current URL: {current_url}")
                        logger.error("This usually means:")
                        logger.error("1. Google detected automated access")
                        logger.error("2. Too many login attempts")
                        logger.error("3. Account security check required")
                        logger.error("\nSolutions:")
                        logger.error("- Wait a few minutes before retrying")
                        logger.error("- Log in manually in a regular Chrome window first")
                        logger.error("- Use an existing Chrome profile with saved session")
                        logger.error("- Check if account needs verification")
                        
                        # Try to navigate back to Flow URL
                        try:
                            logger.info("Attempting to navigate directly to Flow URL...")
                            flow_url = config_manager.get("flow.url", FLOW_URL)
                            await page.goto(flow_url, wait_until="domcontentloaded", timeout=30000)
                            await asyncio.sleep(3)
                            # Check if we're now on Flow page
                            if "labs.google" in page.url and "flow" in page.url:
                                logger.info("Successfully navigated to Flow after error")
                            else:
                                raise Exception("Still on error page after navigation attempt")
                        except Exception as nav_error:
                            logger.error(f"Could not recover from Google error: {nav_error}")
                            raise Exception(f"Google authentication error: {error_indicator}. Please log in manually in a regular browser first, then use setup_chrome_profile.sh to copy your logged-in profile.")
            
            # Check if we need to log in
            login_indicators = [
                'text=Sign in',
                'text=Sign in with Google',
                'a[href*="accounts.google.com"]',
                'button:has-text("Sign in")'
            ]
            
            needs_login = False
            for indicator in login_indicators:
                try:
                    if await page.locator(indicator).count() > 0:
                        needs_login = True
                        logger.warning("Login required - user needs to manually log in")
                        break
                except:
                    continue
            
            if needs_login:
                logger.info("Waiting for manual login (30 seconds)...")
                # Wait up to 30 seconds for user to log in
                for _ in range(30):
                    await asyncio.sleep(1)
                    if not needs_login:
                        # Re-check login status
                        still_needs_login = False
                        for indicator in login_indicators:
                            if await page.locator(indicator).count() > 0:
                                still_needs_login = True
                                break
                        if not still_needs_login:
                            logger.info("Login detected, continuing...")
                            break
            
            # Check for empty state error message
            empty_state_selectors = [
                "text=There doesn't seem to be anything here",
                "text=Try a different prompt",
                "[class*='empty']",
                "[class*='Empty']"
            ]
            
            has_empty_state = False
            for selector in empty_state_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        has_empty_state = True
                        logger.warning("Empty state detected - trying to find/create project or navigate to correct page")
                        # Try to find a "New Project" or "Create" button
                        try:
                            create_buttons = [
                                "button:has-text('New')",
                                "button:has-text('Create')",
                                "a:has-text('New')",
                                "a:has-text('Create')",
                                "[aria-label*='New']",
                                "[aria-label*='Create']"
                            ]
                            for btn_selector in create_buttons:
                                if await page.locator(btn_selector).count() > 0:
                                    logger.info(f"Found create button: {btn_selector}, clicking...")
                                    await page.locator(btn_selector).first.click()
                                    await asyncio.sleep(3)
                                    break
                        except Exception as e:
                            logger.debug(f"Could not find/create project button: {e}")
                        break
                except:
                    continue
            
            # Wait for main UI elements with multiple fallbacks
            # Use "attached" instead of "visible" - elements might be hidden by error banners
            selectors = [
                FLOW_SELECTORS.get("promptInput", "textarea"),
                "textarea",
                "[contenteditable='true']",
                "[role='textbox']",
                "main",
                "[role='main']",
                "body"
            ]
            
            element_found = False
            for selector in selectors:
                try:
                    # First try attached (element exists in DOM)
                    await page.wait_for_selector(selector, timeout=10000, state="attached")
                    element_found = True
                    logger.info(f"Found element with selector: {selector}")
                    break
                except:
                    # If attached fails, try visible as fallback
                    try:
                        await page.wait_for_selector(selector, timeout=5000, state="visible")
                        element_found = True
                        logger.info(f"Found visible element with selector: {selector}")
                        break
                    except:
                        continue
            
            # If no elements found, check if we're at least on the Flow page
            if not element_found:
                current_url = page.url
                if "labs.google" in current_url and ("/fx/" in current_url or "/tools/flow" in current_url):
                    # We're on Flow page, even if elements aren't ready - log warning but continue
                    logger.warning("On Flow page but elements not ready yet - continuing anyway")
                    # Wait a bit more for elements to appear
                    await asyncio.sleep(3)
                    # Check if body exists at least
                    try:
                        body = await page.locator("body").count()
                        if body > 0:
                            logger.info("Body element found - page is loaded, continuing")
                            element_found = True
                    except:
                        pass
                
                if not element_found:
                    # Take screenshot for debugging
                    try:
                        screenshot_path = get_screenshot_path(f"flow_page_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                        await page.screenshot(path=screenshot_path, full_page=True)
                        logger.error(f"Screenshot saved to {screenshot_path}")
                        # Log page info
                        page_title = await page.title()
                        page_url = page.url
                        logger.error(f"Page title: {page_title}, URL: {page_url}")
                    except:
                        pass
                    raise Exception("Could not find any page elements - page may not have loaded")
            
            # Additional wait for dynamic content and error banners to settle
            await asyncio.sleep(3)
            
            # FIX: Check for Google account popup errors (like "Rất tiếc, đã xảy ra lỗi!")
            try:
                google_popup_error_selectors = [
                    'text=Rất tiếc, đã xảy ra lỗi!',  # Vietnamese "Unfortunately, an error occurred!"
                    'text=Unfortunately, an error occurred!',
                    '[class*="error"]:has-text("Rất tiếc")',
                    '[class*="error"]:has-text("lỗi")',
                    '[role="dialog"]:has-text("Rất tiếc")',
                    '[role="dialog"]:has-text("error")',
                    '[role="alertdialog"]:has-text("Rất tiếc")',
                ]
                
                for selector in google_popup_error_selectors:
                    try:
                        error_elem = page.locator(selector).first
                        if await error_elem.count() > 0 and await error_elem.is_visible():
                            error_text = await error_elem.text_content() or ""
                            logger.error(f"Google account popup error detected: {error_text[:200]}")
                            
                            # Try to close the popup if possible
                            try:
                                close_btn = page.locator('[aria-label*="Close"], button:has-text("X"), button:has-text("Đóng")').first
                                if await close_btn.count() > 0 and await close_btn.is_visible():
                                    await close_btn.click()
                                    await asyncio.sleep(1)
                                    logger.info("Closed Google account popup error")
                            except:
                                pass
                            
                            # Take screenshot for debugging
                            screenshot_path = get_screenshot_path(f"google_account_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                            await page.screenshot(path=screenshot_path, full_page=True)
                            logger.error(f"Google account error screenshot saved to {screenshot_path}")
                            
                            # Raise error with context
                            raise Exception(f"Google account error detected: {error_text[:200]}. This may indicate account access issues or session problems. Screenshot: {screenshot_path}")
                    except Exception as popup_check_error:
                        if "Google account error detected" in str(popup_check_error):
                            raise  # Re-raise our custom error
                        continue
            except Exception as e:
                if "Google account error detected" in str(e):
                    raise  # Re-raise our custom error
                logger.debug(f"Could not check for Google account popup errors: {e}")
            
            # FIX: Check for credit loading errors AFTER page has fully loaded
            # Only check after we've waited for credit information to load
            # This prevents false positives from transient loading states
            # If credit loading fails, try to retry by refreshing the page
            try:
                credit_error_selectors = [
                    'text=Không tải được số tín dụng của bạn',  # Vietnamese "Could not load your credits"
                    'text=Could not load your credits',
                    'text=Không tải được',  # Partial match
                    '[class*="error"]:has-text("Không tải được")',
                    '[class*="error"]:has-text("tín dụng")',
                    '[role="alert"]:has-text("Không tải được")',
                    '[role="alert"]:has-text("tín dụng")',
                    '[aria-live="assertive"]:has-text("Không tải được")',
                ]
                
                credit_error_found = False
                credit_error_text = None
                
                # Wait a bit more to ensure error popups have appeared (if they're going to)
                await asyncio.sleep(2)
                
                # Check for credit loading errors with retry mechanism
                max_credit_retries = 2  # Try refreshing page once if credit loading fails
                for credit_retry in range(max_credit_retries):
                    credit_error_found = False
                    credit_error_text = None
                    
                    for selector in credit_error_selectors:
                        try:
                            error_elem = page.locator(selector).first
                            if await error_elem.count() > 0 and await error_elem.is_visible():
                                error_text = await error_elem.text_content() or ""
                                if error_text and ("Không tải được" in error_text or "Could not load" in error_text or "tín dụng" in error_text):
                                    credit_error_found = True
                                    credit_error_text = error_text.strip()
                                    
                                    # Wait a moment to see if it's a transient error that disappears
                                    await asyncio.sleep(2)
                                    
                                    # Check again - if still there, it's a real error
                                    if await error_elem.count() > 0 and await error_elem.is_visible():
                                        if credit_retry < max_credit_retries - 1:
                                            # Try refreshing the page to retry credit loading
                                            logger.warning(f"Credit loading error detected (attempt {credit_retry + 1}/{max_credit_retries}) - trying page refresh...")
                                            try:
                                                # Close error popup first
                                                try:
                                                    close_btn = page.locator('button:has-text("Đóng"), button:has-text("Close"), [aria-label*="Close"], [aria-label*="Đóng"]').first
                                                    if await close_btn.count() > 0 and await close_btn.is_visible():
                                                        await close_btn.click()
                                                        await asyncio.sleep(1)
                                                except:
                                                    pass
                                                
                                                # Refresh the page to retry credit loading
                                                logger.info("Refreshing page to retry credit loading...")
                                                await page.reload(wait_until="networkidle", timeout=30000)
                                                await asyncio.sleep(5)  # Wait for page to reload
                                                
                                                # Wait for credit information to load again
                                                logger.info("Waiting for credit information to load after refresh...")
                                                for wait_attempt in range(10):
                                                    loading_indicators = await page.locator('[class*="loading"], [class*="spinner"], [aria-busy="true"]').count()
                                                    if loading_indicators == 0:
                                                        await asyncio.sleep(2)
                                                        loading_indicators_after = await page.locator('[class*="loading"], [class*="spinner"], [aria-busy="true"]').count()
                                                        if loading_indicators_after == 0:
                                                            logger.info("Credit information loaded after refresh")
                                                            credit_error_found = False  # Reset - will check again
                                                            break
                                                    await asyncio.sleep(1)
                                                
                                                # Continue to next retry iteration to check again
                                                continue
                                            except Exception as refresh_error:
                                                logger.warning(f"Page refresh failed: {refresh_error} - will report error")
                                                break
                                        else:
                                            # Last retry - error is persistent, report it
                                            logger.warning(f"Credit loading error detected (persistent after {max_credit_retries} attempts): {credit_error_text[:200]}")
                                            
                                            # Try to close the error popup if possible (but don't fail if we can't)
                                            try:
                                                # Look for close button near the error
                                                close_btn = page.locator('button:has-text("Đóng"), button:has-text("Close"), [aria-label*="Close"], [aria-label*="Đóng"]').first
                                                if await close_btn.count() > 0 and await close_btn.is_visible():
                                                    await close_btn.click()
                                                    await asyncio.sleep(1)
                                                    logger.info("Closed credit loading error popup")
                                            except:
                                                pass
                                            
                                            # Take screenshot for debugging
                                            screenshot_path = get_screenshot_path(f"credit_loading_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                                            await page.screenshot(path=screenshot_path, full_page=True)
                                            logger.warning(f"Credit loading error screenshot saved to {screenshot_path}")
                                            
                                            # Log warning but don't fail - profile loaded successfully, just credit info failed
                                            # This is a non-fatal error - the profile works, just credit display failed
                                            logger.warning("Profile loaded successfully, but credit information failed to load after retries")
                                            logger.warning("This may indicate temporary network issues or account credit system problems")
                                            logger.warning("Automation will continue - video generation may still work if credits are available")
                                    else:
                                        # Error disappeared - was transient, ignore it
                                        logger.debug("Credit loading error was transient (disappeared) - ignoring")
                                        credit_error_found = False
                                    break
                        except Exception as credit_check_error:
                            continue
                    
                    # If no error found, break out of retry loop
                    if not credit_error_found:
                        break
                
                if not credit_error_found:
                    # Also check body text for credit loading errors (but only if persistent)
                    try:
                        body_text = await page.locator("body").text_content() or ""
                        if "Không tải được số tín dụng" in body_text or "Could not load your credits" in body_text:
                            # Check if it's in a persistent error element, not just transient text
                            persistent_error = await page.locator('[role="alert"]:has-text("Không tải được"), [class*="error"]:has-text("Không tải được")').count()
                            if persistent_error > 0:
                                logger.warning("Credit loading error detected in page body text (persistent)")
                                logger.warning("Profile loaded but credit information may not be available")
                    except:
                        pass
            except Exception as credit_error_check_error:
                logger.debug(f"Could not check for credit loading errors: {credit_error_check_error}")
            
            # FIX: Verify ULTRA badge/subscription status
            try:
                ultra_badge_selectors = [
                    'text=ULTRA',
                    '[class*="ultra"]',
                    '[class*="Ultra"]',
                    '[aria-label*="ULTRA"]',
                    'div:has-text("ULTRA")',
                ]
                
                has_ultra = False
                for selector in ultra_badge_selectors:
                    try:
                        ultra_elem = page.locator(selector).first
                        if await ultra_elem.count() > 0 and await ultra_elem.is_visible():
                            ultra_text = await ultra_elem.text_content() or ""
                            if "ULTRA" in ultra_text.upper():
                                has_ultra = True
                                logger.info(f"✓ ULTRA badge detected: {ultra_text[:50]}")
                                break
                    except:
                        continue
                
                if not has_ultra:
                    logger.warning("⚠ ULTRA badge not detected - account may not have ULTRA subscription")
                    # Don't fail here, just log warning - account might still work
            except Exception as ultra_check_error:
                logger.debug(f"Could not check for ULTRA badge: {ultra_check_error}")
            
            # Check for error banners and dismiss them if possible
            try:
                # Look for common error banners and close buttons
                error_close_selectors = [
                    'button:has-text("Close")',
                    'button:has-text("Đóng")',  # Vietnamese "Close"
                    '[aria-label*="Close"]',
                    '[aria-label*="Đóng"]',
                    'button[class*="close"]',
                    '.close-button'
                ]
                for selector in error_close_selectors:
                    try:
                        close_btn = page.locator(selector).first
                        if await close_btn.count() > 0 and await close_btn.is_visible():
                            logger.info(f"Dismissing error banner with selector: {selector}")
                            await close_btn.click()
                            await asyncio.sleep(1)
                            break
                    except:
                        continue
            except Exception as e:
                logger.debug(f"Could not dismiss error banners: {e}")
            
            # Verify page is ready (more lenient check)
            is_ready = await self._verify_page_ready(page)
            if not is_ready:
                # Log what we found for debugging
                try:
                    all_textareas = await page.locator("textarea").count()
                    all_buttons = await page.locator("button").count()
                    all_inputs = await page.locator("input").count()
                    all_contenteditables = await page.locator("[contenteditable]").count()
                    page_title = await page.title()
                    logger.warning(f"Page verification failed. Found {all_textareas} textareas, {all_buttons} buttons, {all_inputs} inputs, {all_contenteditables} contenteditables. Title: {page_title}")
                    
                    # Take screenshot
                    screenshot_path = get_screenshot_path(f"flow_page_not_ready_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    await page.screenshot(path=screenshot_path, full_page=True)
                    logger.warning(f"Screenshot saved to {screenshot_path}")
                except Exception as e:
                    logger.warning(f"Could not capture debug info: {e}")
                
                # Try to continue anyway - maybe selectors will work
                logger.warning("Page verification failed, but continuing - selectors may still work")
            
            logger.info("Successfully navigated to Flow")
            
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            
            # Build detailed error message
            detailed_error = f"Failed to navigate to Flow: {error_type}: {error_msg}"
            
            # If error message is too short, add context
            if len(error_msg) < 10:
                try:
                    page_url = page.url if page else "unknown"
                    page_title = await page.title() if page else "unknown"
                    detailed_error = f"Failed to navigate to Flow: {error_type}: {error_msg} (URL: {page_url}, Title: {page_title})"
                except:
                    pass
            
            logger.error(detailed_error, exc_info=True)
            
            # Take screenshot on error
            try:
                screenshot_path = get_screenshot_path(f"flow_navigation_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.error(f"Error screenshot saved to {screenshot_path}")
                detailed_error += f" (Screenshot: {screenshot_path})"
            except:
                pass
            
            # Re-raise with detailed error message
            raise Exception(detailed_error) from e
    
    async def _verify_page_ready(self, page: Page) -> bool:
        """Verify that Flow page is ready for interaction"""
        try:
            # Try multiple selector strategies
            input_selectors = [
                FLOW_SELECTORS.get("promptInput", "textarea"),
                "[role='textbox']",
                "[contenteditable='true']",
                "[contenteditable]",
                "textarea",
                "input[type='text']"
            ]
            
            button_selectors = [
                FLOW_SELECTORS.get("generateButton", "button"),
                'button:has-text("Generate")',
                'button[aria-label*="Generate"]',
                'button[type="submit"]',
                "button"
            ]
            
            has_input = False
            for selector in input_selectors:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        has_input = True
                        logger.info(f"Found input with selector: {selector}")
                        break
                except:
                    continue
            
            has_button = False
            for selector in button_selectors:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        has_button = True
                        logger.info(f"Found button with selector: {selector}")
                        break
                except:
                    continue
            
            # More lenient: just need an input OR button (not both)
            # This allows for pages that might have different structures
            return has_input or has_button
        except Exception as e:
            logger.debug(f"Page verification error: {e}")
            return False
    
    async def ensure_new_project(self, page: Page, force_new: bool = False) -> None:
        """Ensure we're in a new project/editor view by clicking 'New project' if needed.

        Args:
            page: Playwright page instance.
            force_new: When True, always try to create a fresh project even if
                       we're already in an editor view. This is useful for
                       automated scene rendering so each scene gets a clean
                       editor without leftover prompts/state from previous runs.
        """
        logger.info(f"[ensure_new_project] Checking if we need to create a new project (force_new={force_new})...")
        
        # Wait a bit for page to settle
        await asyncio.sleep(2)
        
        # FIX 4: Check if we're already in the editor (has prompt input visible)
        try:
            prompt_inputs = [
                "textarea",
                "[contenteditable='true']",
                "[role='textbox']"
            ]
            
            in_editor = False
            visible_inputs = []
            for selector in prompt_inputs:
                try:
                    element = page.locator(selector).first
                    count = await element.count()
                    if count > 0:
                        is_visible = await element.is_visible()
                        if is_visible:
                            visible_inputs.append(selector)
                            in_editor = True
                except:
                    continue
            
            if in_editor:
                if not force_new:
                    logger.info(f"✓ Already in editor view (found visible inputs: {visible_inputs}), no need to create new project")
                    # Verify we can actually interact with the input
                    try:
                        test_input = page.locator(visible_inputs[0]).first
                        await test_input.focus()
                        logger.info("✓ Editor input is interactive - ready for prompt injection")
                        return
                    except Exception as verify_error:
                        logger.warning(f"Editor input found but not interactive: {verify_error} - will try to click new project anyway")
                else:
                    logger.info(f"Already in editor view (found visible inputs: {visible_inputs}), but force_new=True - navigating to gallery to create a fresh project")
                    # When force_new=True and we're in editor, we need to navigate back to gallery first
                    # Try to find and click a "Home" or "Gallery" link/button
                    try:
                        home_selectors = [
                            'a[href*="/tools/flow"]',
                            'a:has-text("Home")',
                            'a:has-text("Gallery")',
                            'button:has-text("Home")',
                            'button:has-text("Gallery")',
                            '[aria-label*="Home"]',
                            '[aria-label*="Gallery"]',
                        ]
                        
                        navigated_to_gallery = False
                        for home_selector in home_selectors:
                            try:
                                home_button = page.locator(home_selector).first
                                if await home_button.count() > 0 and await home_button.is_visible():
                                    logger.info(f"Found home/gallery button: {home_selector}, clicking to navigate to gallery...")
                                    await home_button.click()
                                    await asyncio.sleep(3)  # Wait for navigation
                                    navigated_to_gallery = True
                                    break
                            except:
                                continue
                        
                        if not navigated_to_gallery:
                            # Fallback: navigate directly to Flow URL to get to gallery
                            logger.info("Home button not found, navigating directly to Flow URL to get gallery view...")
                            flow_url = config_manager.get("flow.url", "https://labs.google/fx/tools/flow/")
                            await page.goto(flow_url, wait_until="domcontentloaded", timeout=30000)
                            await asyncio.sleep(3)  # Wait for page to load
                            logger.info("Navigated to Flow URL, should be in gallery view now")
                    except Exception as nav_error:
                        logger.warning(f"Failed to navigate to gallery from editor: {nav_error}, will try to proceed anyway")
        except Exception as editor_check_error:
            logger.debug(f"Error checking editor state: {editor_check_error}")
        
        # FIX 2: Explicitly check for gallery view
        logger.info("Checking if we're on gallery/project grid view...")
        is_gallery = False
        try:
            gallery_indicators = [
                'button:has-text("Dự án mới")',  # Most reliable indicator
                'button:has-text("New project")',
                '[class*="gallery"]',
                '[class*="thumbnail"]',
                '[class*="grid"]',
                'img[alt*="project"]'
            ]
            
            for indicator in gallery_indicators:
                try:
                    count = await page.locator(indicator).count()
                    if count > 0:
                        is_gallery = True
                        logger.info(f"✓ Detected gallery view (found indicator: {indicator})")
                        break
                except:
                    continue
        except Exception as gallery_check_error:
            logger.debug(f"Error checking gallery state: {gallery_check_error}")
        
        if not is_gallery and not in_editor:
            logger.warning("Unknown page state - taking screenshot for debugging...")
            try:
                screenshot_path = get_screenshot_path(f"unknown_page_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.warning(f"Screenshot saved to {screenshot_path}")
            except:
                pass
        
        # FIX 3: Enhanced "New project" button detection
        # Based on screenshot, the button has text "Dự án mới" (Vietnamese) and is overlaid on project cards
        # Priority order: most specific first
        new_project_selectors = [
            # Most specific: Vietnamese text on buttons
            'button:has-text("Dự án mới")',  # Vietnamese "New project" - highest priority
            'button:has-text("Tạo mới")',  # Vietnamese "Create new"
            # English variants
            'button:has-text("New project")',
            'button:has-text("New Project")',
            'button:has-text("Create")',
            'button:has-text("Create project")',
            # Look for buttons within cards/thumbnails (where button appears in screenshot)
            '[class*="card"] button:has-text("Dự án mới")',
            '[class*="thumbnail"] button:has-text("Dự án mới")',
            '[class*="card"] button:has-text("New project")',
            '[class*="thumbnail"] button:has-text("New project")',
            '[class*="project"] button:has-text("Dự án mới")',
            '[class*="project"] button:has-text("New project")',
            # Aria labels (more reliable than class-based)
            '[aria-label*="Dự án mới"]',
            '[aria-label*="New project"]',
            '[aria-label*="New Project"]',
            '[aria-label*="Tạo mới"]',
            # Look for buttons with plus icon (common pattern)
            'button:has(svg[class*="plus"]), button:has(svg[class*="add"])',
            'button:has-text("+")',
            # Class-based selectors (less reliable, but fallback)
            'button[class*="new"]',
            'button[class*="create"]',
        ]
        
        for selector in new_project_selectors:
            try:
                logger.debug(f"Trying new project selector: {selector}")
                button = page.locator(selector).first
                count = await button.count()
                
                if count > 0:
                    # FIX 3: Enhanced visibility and interaction checks
                    is_visible = False
                    is_enabled = False
                    try:
                        is_visible = await button.is_visible()
                        is_enabled = await button.is_enabled()
                    except:
                        # Try alternative visibility check
                        try:
                            bounding_box = await button.bounding_box()
                            is_visible = bounding_box is not None
                        except:
                            pass
                    
                    if is_visible and is_enabled:
                        button_text = ""
                        aria_label = ""
                        try:
                            button_text = (await button.text_content() or "").strip()
                            aria_label = (await button.get_attribute("aria-label") or "").strip()
                        except:
                            pass
                        
                        # Additional check: make sure it's not just a close button or other UI element
                        if button_text and any(skip in button_text.lower() for skip in ['đóng', 'close', 'cancel', 'x']):
                            logger.debug(f"Skipping button with text '{button_text}' (appears to be close/cancel)")
                            continue
                        
                        logger.info(f"Found new project button: '{button_text or aria_label}' (selector: {selector})")
                        
                        # FIX 3: Enhanced scrolling and interaction
                        try:
                            # Scroll into view with more options
                            await button.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                            
                            # Try to get button position for debugging
                            try:
                                box = await button.bounding_box()
                                if box:
                                    logger.debug(f"Button position: x={box['x']:.0f}, y={box['y']:.0f}, width={box['width']:.0f}, height={box['height']:.0f}")
                            except:
                                pass
                        except Exception as scroll_error:
                            logger.debug(f"Scroll failed: {scroll_error}, trying JavaScript scroll...")
                            try:
                                await button.evaluate("el => el.scrollIntoView({behavior: 'smooth', block: 'center'})")
                                await asyncio.sleep(0.5)
                            except:
                                pass
                        
                        # Click the button with retry logic
                        clicked = False
                        for click_attempt in range(3):
                            try:
                                await button.click(timeout=5000)
                                clicked = True
                                logger.info(f"✓ Clicked new project button (attempt {click_attempt + 1})")
                                break
                            except Exception as click_error:
                                if click_attempt < 2:
                                    logger.debug(f"Click attempt {click_attempt + 1} failed: {click_error}, retrying...")
                                    await asyncio.sleep(0.5)
                                else:
                                    # Last attempt: try JavaScript click
                                    try:
                                        await button.evaluate("el => el.click()")
                                        clicked = True
                                        logger.info("✓ Clicked new project button (via JavaScript)")
                                        break
                                    except:
                                        raise click_error
                        
                        if not clicked:
                            raise Exception("Failed to click button after all attempts")
                        
                        # Wait for editor to load (longer wait for React to render)
                        logger.info("Waiting for editor to load after clicking new project...")
                        await asyncio.sleep(3)
                        
                        # FIX 4: Enhanced verification that we're now in the editor
                        editor_found = False
                        for input_selector in ["textarea", "[contenteditable='true']", "[role='textbox']"]:
                            try:
                                input_elem = page.locator(input_selector).first
                                count = await input_elem.count()
                                if count > 0:
                                    is_visible = await input_elem.is_visible()
                                    if is_visible:
                                        # Try to interact with it to confirm
                                        try:
                                            await input_elem.focus()
                                            editor_found = True
                                            logger.info(f"✓ Successfully navigated to editor view (found {input_selector})")
                                            await asyncio.sleep(2)  # Additional wait for UI to settle
                                            return
                                        except:
                                            logger.debug(f"Found {input_selector} but not interactive yet")
                            except:
                                continue
                        
                        if not editor_found:
                            logger.warning("Clicked new project but editor not detected yet - waiting longer...")
                            # Wait a bit more and check again
                            await asyncio.sleep(3)
                            for input_selector in ["textarea", "[contenteditable='true']", "[role='textbox']"]:
                                try:
                                    input_elem = page.locator(input_selector).first
                                    if await input_elem.count() > 0:
                                        logger.info(f"✓ Editor found after additional wait ({input_selector})")
                                        await asyncio.sleep(2)
                                        return
                                except:
                                    continue
                            
                            # FIX 5: Take screenshot if editor still not found
                            logger.warning("Editor still not found after clicking new project - taking screenshot...")
                            try:
                                screenshot_path = get_screenshot_path(f"new_project_clicked_no_editor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                                await page.screenshot(path=screenshot_path, full_page=True)
                                logger.warning(f"Screenshot saved to {screenshot_path}")
                            except:
                                pass
                            
                            logger.warning("Continuing anyway - editor may load later")
                            await asyncio.sleep(2)
                            return
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")
                continue
        
        # If no new project button found, try JavaScript-based search
        logger.info("No new project button found with selectors - trying JavaScript search...")
        try:
            # Use JavaScript to find elements containing "Dự án mới" or "New project"
            found_button = await page.evaluate("""
                () => {
                    const searchTexts = ['Dự án mới', 'New project', 'New Project', 'Tạo mới'];
                    const allElements = document.querySelectorAll('button, a, [role="button"], [onclick]');
                    
                    for (const el of allElements) {
                        const text = (el.textContent || el.innerText || '').trim();
                        const ariaLabel = (el.getAttribute('aria-label') || '').trim();
                        
                        for (const searchText of searchTexts) {
                            if (text.includes(searchText) || ariaLabel.includes(searchText)) {
                                // Make sure it's not a close/cancel button
                                if (!text.toLowerCase().includes('đóng') && 
                                    !text.toLowerCase().includes('close') &&
                                    !text.toLowerCase().includes('cancel')) {
                                    return {
                                        found: true,
                                        tagName: el.tagName,
                                        text: text.substring(0, 50),
                                        id: el.id || '',
                                        className: el.className || ''
                                    };
                                }
                            }
                        }
                    }
                    return {found: false};
                }
            """)
            
            if found_button.get('found'):
                logger.info(f"JavaScript found potential new project button: {found_button.get('text')}")
                # Try to click it using JavaScript directly
                try:
                    clicked = await page.evaluate("""
                        () => {
                            const searchTexts = ['Dự án mới', 'New project', 'New Project', 'Tạo mới'];
                            const allElements = document.querySelectorAll('button, a, [role="button"], [onclick]');
                            
                            for (const el of allElements) {
                                const text = (el.textContent || el.innerText || '').trim();
                                const ariaLabel = (el.getAttribute('aria-label') || '').trim();
                                
                                for (const searchText of searchTexts) {
                                    if (text.includes(searchText) || ariaLabel.includes(searchText)) {
                                        if (!text.toLowerCase().includes('đóng') && 
                                            !text.toLowerCase().includes('close') &&
                                            !text.toLowerCase().includes('cancel')) {
                                            // Scroll into view and click
                                            el.scrollIntoView({behavior: 'smooth', block: 'center'});
                                            el.click();
                                            return true;
                                        }
                                    }
                                }
                            }
                            return false;
                        }
                    """)
                    
                    if clicked:
                        logger.info("✓ Clicked new project button (found via JavaScript)")
                        await asyncio.sleep(3)
                        
                        # Verify editor loaded
                        for input_selector in ["textarea", "[contenteditable='true']", "[role='textbox']"]:
                            try:
                                input_elem = page.locator(input_selector).first
                                if await input_elem.count() > 0:
                                    logger.info("✓ Successfully navigated to editor view")
                                    await asyncio.sleep(2)
                                    return
                            except:
                                continue
                except Exception as js_error:
                    logger.debug(f"JavaScript click failed: {js_error}")
        except Exception as js_search_error:
            logger.debug(f"JavaScript search failed: {js_search_error}")
        
        # FIX 5: Enhanced fallback with better error reporting
        logger.warning("No new project button found with standard selectors - trying enhanced search...")
        
        # Take screenshot for debugging
        try:
            screenshot_path = get_screenshot_path(f"no_new_project_button_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            logger.warning(f"Debug screenshot saved to {screenshot_path}")
        except:
            pass
        
        # Enhanced JavaScript search with more patterns
        try:
            logger.info("Trying enhanced JavaScript search for new project button...")
            found_button = await page.evaluate("""
                () => {
                    const searchTexts = ['Dự án mới', 'New project', 'New Project', 'Tạo mới', 'Create', 'Create project'];
                    const allElements = document.querySelectorAll('button, a, [role="button"], [onclick], div[class*="button"], div[class*="card"]');
                    
                    const results = [];
                    
                    for (const el of allElements) {
                        const text = (el.textContent || el.innerText || '').trim();
                        const ariaLabel = (el.getAttribute('aria-label') || '').trim();
                        const className = (el.className || '').toLowerCase();
                        
                        // Check text content
                        for (const searchText of searchTexts) {
                            if (text.includes(searchText) || ariaLabel.includes(searchText)) {
                                // Make sure it's not a close/cancel button
                                if (!text.toLowerCase().includes('đóng') && 
                                    !text.toLowerCase().includes('close') &&
                                    !text.toLowerCase().includes('cancel') &&
                                    !text.toLowerCase().includes('x')) {
                                    
                                    const rect = el.getBoundingClientRect();
                                    results.push({
                                        found: true,
                                        tagName: el.tagName,
                                        text: text.substring(0, 50),
                                        ariaLabel: ariaLabel.substring(0, 50),
                                        id: el.id || '',
                                        className: className.substring(0, 100),
                                        visible: rect.width > 0 && rect.height > 0,
                                        x: rect.x,
                                        y: rect.y
                                    });
                                }
                            }
                        }
                    }
                    
                    return results.length > 0 ? results[0] : {found: false};
                }
            """)
            
            if found_button.get('found'):
                logger.info(f"JavaScript found potential new project button: {found_button.get('text')} (tag: {found_button.get('tagName')}, visible: {found_button.get('visible')})")
                # Try to click it using a more specific selector
                try:
                    # Build selector from found element
                    selector_parts = []
                    if found_button.get('id'):
                        selector_parts.append(f"#{found_button.get('id')}")
                    if found_button.get('className'):
                        # Use class name if available
                        class_name = found_button.get('className').split(' ')[0]
                        if class_name:
                            selector_parts.append(f".{class_name}")
                    if not selector_parts:
                        # Fallback to text-based selector
                        text = found_button.get('text', '').split('\n')[0].strip()
                        if text:
                            selector_parts.append(f'button:has-text("{text[:20]}")')
                    
                    if selector_parts:
                        selector = selector_parts[0]
                        logger.info(f"Trying to click using selector: {selector}")
                        button = page.locator(selector).first
                        if await button.count() > 0:
                            await button.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                            await button.click(timeout=5000)
                            logger.info("✓ Clicked new project button (found via enhanced JavaScript search)")
                            await asyncio.sleep(3)
                            
                            # Verify editor loaded
                            for input_selector in ["textarea", "[contenteditable='true']", "[role='textbox']"]:
                                try:
                                    input_elem = page.locator(input_selector).first
                                    if await input_elem.count() > 0:
                                        logger.info("✓ Successfully navigated to editor view")
                                        await asyncio.sleep(2)
                                        return
                                except:
                                    continue
                except Exception as js_click_error:
                    logger.debug(f"JavaScript-based click failed: {js_click_error}")
        except Exception as js_search_error:
            logger.debug(f"Enhanced JavaScript search failed: {js_search_error}")
        
        # Final check: are we already in editor?
        logger.info("Final check: verifying if we're already in editor...")
        try:
            for input_selector in ["textarea", "[contenteditable='true']", "[role='textbox']"]:
                try:
                    input_elem = page.locator(input_selector).first
                    count = await input_elem.count()
                    if count > 0:
                        is_visible = await input_elem.is_visible()
                        if is_visible:
                            logger.info(f"✓ Already in editor view (found {input_selector}) - no new project needed")
                            return
                except:
                    continue
        except:
            pass
        
        # FIX 5: Log detailed error with page state
        logger.error("CRITICAL: Could not find or click 'New project' button, and not in editor view")
        logger.error("Current page state:")
        try:
            current_url = page.url
            page_title = await page.title()
            logger.error(f"  URL: {current_url}")
            logger.error(f"  Title: {page_title}")
            
            # Count various elements
            button_count = await page.locator("button").count()
            textarea_count = await page.locator("textarea").count()
            card_count = await page.locator('[class*="card"]').count()
            logger.error(f"  Buttons found: {button_count}")
            logger.error(f"  Textareas found: {textarea_count}")
            logger.error(f"  Cards found: {card_count}")
        except:
            pass
        
        # Don't fail completely - maybe the page will work anyway
        logger.warning("Continuing despite not finding new project button - page may still work")
        await asyncio.sleep(2)
    
    async def inject_prompt(self, page: Page, prompt: str) -> None:
        """Inject prompt text into Flow input field"""
        logger.info(f"Attempting to inject prompt (length: {len(prompt)})")
        
        # Wait longer for React to fully render (Flow is a complex React app)
        logger.info("Waiting for React app to fully render...")
        await asyncio.sleep(5)
        
        # Try to wait for React to finish rendering by checking for interactive elements
        max_wait = 30  # Wait up to 30 seconds
        for i in range(max_wait):
            try:
                # Check if any input elements exist
                textarea_count = await page.locator("textarea").count()
                contenteditable_count = await page.locator("[contenteditable]").count()
                textbox_count = await page.locator("[role='textbox']").count()
                
                if textarea_count > 0 or contenteditable_count > 0 or textbox_count > 0:
                    logger.info(f"Found interactive elements after {i+1} seconds")
                    break
            except:
                pass
            await asyncio.sleep(1)
        
        # First, try to find all possible input elements and log them
        try:
            all_textareas = await page.locator("textarea").all()
            all_contenteditables = await page.locator("[contenteditable]").all()
            all_textboxes = await page.locator("[role='textbox']").all()
            logger.info(f"Found {len(all_textareas)} textareas, {len(all_contenteditables)} contenteditables, {len(all_textboxes)} textboxes")
            
            # Log details of first few elements
            for i, ta in enumerate(all_textareas[:3]):
                try:
                    is_visible = await ta.is_visible()
                    placeholder = await ta.get_attribute("placeholder")
                    logger.debug(f"Textarea {i}: visible={is_visible}, placeholder={placeholder}")
                except:
                    pass
        except Exception as e:
            logger.debug(f"Error finding elements: {e}")
        
        selectors = [
            FLOW_SELECTORS.get("promptInput"),
            "[role='textbox']",
            "[contenteditable='true']",
            "[contenteditable]",
            "textarea[placeholder*='prompt']",
            "textarea[aria-label*='prompt']",
            "textarea[placeholder*='Enter']",
            "textarea[placeholder*='Describe']",
            "textarea[placeholder*='video']",
            "textarea[placeholder*='Create']",
            "textarea",
            "input[type='text']",
            "input[type='search']"
        ]
        
        for selector in selectors:
            try:
                logger.debug(f"Trying selector: {selector}")
                input_element = page.locator(selector).first
                count = await input_element.count()
                
                if count > 0:
                    is_visible = await input_element.is_visible()
                    logger.info(f"Found element with selector '{selector}' (count={count}, visible={is_visible})")
                    
                    if not is_visible:
                        logger.debug("Element not visible, trying multiple strategies to make it visible...")
                        
                        # Strategy 1: Scroll into view
                        try:
                            await input_element.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                            is_visible = await input_element.is_visible()
                        except:
                            pass
                        
                        # Strategy 2: Try to click parent or container to reveal
                        if not is_visible:
                            try:
                                # Look for parent containers that might need clicking
                                parent = input_element.locator("..")
                                if await parent.count() > 0:
                                    await parent.first.click()
                                    await asyncio.sleep(0.5)
                                    is_visible = await input_element.is_visible()
                            except:
                                pass
                        
                        # Strategy 3: Try clicking common "New" or "Create" buttons
                        if not is_visible:
                            try:
                                create_buttons = [
                                    "button:has-text('New')",
                                    "button:has-text('Create')",
                                    "button:has-text('Start')",
                                    "[aria-label*='New']",
                                    "[aria-label*='Create']"
                                ]
                                for btn_sel in create_buttons:
                                    if await page.locator(btn_sel).count() > 0:
                                        await page.locator(btn_sel).first.click()
                                        await asyncio.sleep(1)
                                        is_visible = await input_element.is_visible()
                                        if is_visible:
                                            break
                            except:
                                pass
                        
                        # Strategy 4: Try to make visible via JavaScript
                        if not is_visible:
                            try:
                                await input_element.evaluate("""
                                    el => {
                                        el.style.display = 'block';
                                        el.style.visibility = 'visible';
                                        el.style.opacity = '1';
                                        el.removeAttribute('hidden');
                                        el.removeAttribute('aria-hidden');
                                    }
                                """)
                                await asyncio.sleep(0.5)
                                is_visible = await input_element.is_visible()
                            except:
                                pass
                    
                    # Even if not visible, try to interact with it (some elements work when not "visible")
                    if not is_visible:
                        logger.warning("Element still not visible, but attempting interaction anyway...")
                    
                    # Click to focus
                    try:
                        await input_element.click(timeout=5000)
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        logger.debug(f"Click failed, trying focus: {e}")
                        try:
                            await input_element.focus()
                            await asyncio.sleep(0.3)
                        except:
                            pass
                    
                    # Clear existing text (try multiple methods)
                    try:
                        await input_element.fill("")
                    except:
                        try:
                            await input_element.evaluate("el => el.value = ''")
                        except:
                            try:
                                await input_element.evaluate("el => el.innerText = ''")
                            except:
                                pass
                    
                    # Fill prompt directly (faster and more reliable than typing character-by-character)
                    # Use fill() first for speed, fallback to type() only if fill() doesn't work
                    try:
                        # Try fill() first - it's much faster and more reliable
                        await input_element.fill(prompt)
                        logger.debug("Used fill() method for prompt injection")
                    except Exception as fill_error:
                        logger.debug(f"fill() failed: {fill_error}, trying type()...")
                        # Fallback to type() if fill() doesn't work (for React controlled inputs)
                        try:
                            await input_element.type(prompt, delay=10)  # Reduced delay from 50ms to 10ms
                            logger.debug("Used type() method for prompt injection")
                        except Exception as type_error:
                            logger.debug(f"type() failed: {type_error}, trying JavaScript...")
                            # Fallback to JavaScript direct value setting
                            try:
                                await input_element.evaluate(f"el => el.value = {repr(prompt)}")
                                # Trigger input event for React
                                await input_element.evaluate("el => el.dispatchEvent(new Event('input', { bubbles: true }))")
                                logger.debug("Used JavaScript value assignment")
                            except Exception as js_error:
                                logger.debug(f"JavaScript value failed: {js_error}, trying innerText...")
                                try:
                                    await input_element.evaluate(f"el => el.innerText = {repr(prompt)}")
                                    await input_element.evaluate("el => el.dispatchEvent(new Event('input', { bubbles: true }))")
                                    logger.debug("Used JavaScript innerText assignment")
                                except Exception as inner_error:
                                    logger.error(f"All text input methods failed: fill={fill_error}, type={type_error}, js={js_error}, inner={inner_error}")
                                    raise Exception("All text input methods failed")
                    
                    await asyncio.sleep(0.5)
                    
                    # Verify text was set (try multiple methods)
                    value = None
                    try:
                        value = await input_element.input_value()
                    except:
                        try:
                            value = await input_element.evaluate("el => el.value")
                        except:
                            try:
                                value = await input_element.text_content()
                            except:
                                try:
                                    value = await input_element.evaluate("el => el.innerText")
                                except:
                                    pass
                    
                    if value and (prompt[:20] in str(value) or len(str(value)) > len(prompt) * 0.8):
                        logger.info(f"✓ Prompt injected successfully (verified: {len(str(value))} chars)")
                        # Wait longer to ensure React has processed the input
                        await asyncio.sleep(1.5)
                        return
                    else:
                        logger.warning(f"Prompt verification failed. Expected ~{len(prompt)} chars, got: {len(str(value)) if value else 0}")
                        logger.debug(f"Value preview: {str(value)[:50] if value else 'None'}")
                        # Try one more time with fill
                        try:
                            await input_element.fill(prompt)
                            await asyncio.sleep(1)
                            # Verify again
                            if is_textarea:
                                value = await input_element.input_value()
                            else:
                                value = await input_element.text_content()
                            if value and len(str(value)) > len(prompt) * 0.8:
                                logger.info(f"✓ Prompt re-injected successfully (verified: {len(str(value))} chars)")
                                await asyncio.sleep(1.5)
                                return
                        except:
                            pass
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        # Check for iframes - Flow might load content in iframe
        try:
            iframes = await page.locator("iframe").all()
            if iframes:
                logger.info(f"Found {len(iframes)} iframe(s), checking for input elements inside...")
                for i, iframe in enumerate(iframes):
                    try:
                        iframe_content = await iframe.content_frame()
                        if iframe_content:
                            iframe_textareas = await iframe_content.locator("textarea").all()
                            iframe_contenteditables = await iframe_content.locator("[contenteditable]").all()
                            if iframe_textareas or iframe_contenteditables:
                                logger.info(f"Found input elements in iframe {i}, switching context...")
                                # Try to interact with iframe content
                                target = iframe_textareas[0] if iframe_textareas else iframe_contenteditables[0]
                                await target.click()
                                await target.fill(prompt)
                                # Verify
                                value = await target.input_value() if iframe_textareas else await target.text_content()
                                if value and (prompt[:20] in str(value) or len(str(value)) > len(prompt) * 0.8):
                                    logger.info(f"✓ Prompt injected successfully in iframe (verified: {len(str(value))} chars)")
                                    await asyncio.sleep(0.5)
                                    return
                    except Exception as e:
                        logger.debug(f"Could not access iframe {i}: {e}")
                        continue
        except Exception as e:
            logger.debug(f"Error checking iframes: {e}")
        
        # Last resort: try to find any visible input element using JavaScript
        try:
            logger.warning("Trying JavaScript-based element detection...")
            
            # Use JavaScript to find and interact with input elements
            prompt_escaped = prompt.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            
            result = await page.evaluate("""
                () => {
                    // Count visible input elements
                    let count = 0;
                    
                    // Textareas
                    document.querySelectorAll('textarea').forEach(el => {
                        if (el.offsetParent !== null) count++;
                    });
                    
                    // Contenteditables
                    document.querySelectorAll('[contenteditable]').forEach(el => {
                        if (el.offsetParent !== null) count++;
                    });
                    
                    // Text inputs
                    document.querySelectorAll('input[type="text"]').forEach(el => {
                        if (el.offsetParent !== null) count++;
                    });
                    
                    return {found: count > 0, count: count};
                }
            """)
            
            if result.get('found'):
                logger.info(f"JavaScript found {result.get('count')} visible input elements")
                
                # Try to set value using JavaScript
                set_result = await page.evaluate(f"""
                    () => {{
                        const prompt = "{prompt_escaped}";
                        let success = false;
                        
                        // Try textareas first
                        document.querySelectorAll('textarea').forEach(el => {{
                            if (el.offsetParent !== null && !success) {{
                                try {{
                                    el.focus();
                                    el.value = prompt;
                                    el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                    success = true;
                                }} catch(e) {{
                                    console.log('Textarea error:', e);
                                }}
                            }}
                        }});
                        
                        // Try contenteditables if textarea didn't work
                        if (!success) {{
                            document.querySelectorAll('[contenteditable]').forEach(el => {{
                                if (el.offsetParent !== null && !success) {{
                                    try {{
                                        el.focus();
                                        el.innerText = prompt;
                                        el.textContent = prompt;
                                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                        success = true;
                                    }} catch(e) {{
                                        console.log('Contenteditable error:', e);
                                    }}
                                }}
                            }});
                        }}
                        
                        return success;
                    }}
                """)
                
                if set_result:
                    logger.info("✓ JavaScript-based prompt injection worked!")
                    await asyncio.sleep(1)
                    
                    # Verify it worked
                    verify = await page.evaluate("""
                        () => {
                            let found = false;
                            document.querySelectorAll('textarea, [contenteditable]').forEach(el => {
                                if (el.offsetParent !== null) {
                                    const val = el.value || el.innerText || el.textContent || '';
                                    if (val.length > 10) {
                                        found = true;
                                    }
                                }
                            });
                            return found;
                        }
                    """)
                    
                    if verify:
                        logger.info("✓ Verified: Prompt was set successfully")
                        return
                    else:
                        logger.warning("JavaScript set value but verification failed")
        except Exception as e:
            logger.error(f"JavaScript fallback failed: {e}")
        
        # Try Playwright fallback one more time with longer waits
        try:
            logger.warning("Final fallback: waiting longer and trying all elements...")
            await asyncio.sleep(3)
            
            # Try textareas first
            all_textareas = await page.locator("textarea").all()
            for ta in all_textareas:
                try:
                    if await ta.is_visible():
                        logger.info("Found visible textarea, using as final fallback")
                        await ta.scroll_into_view_if_needed()
                        await asyncio.sleep(1)
                        await ta.click()
                        await asyncio.sleep(0.5)
                        await ta.fill(prompt)
                        await asyncio.sleep(1)
                        
                        # Verify
                        value = await ta.input_value()
                        if prompt[:20] in str(value) or len(str(value)) > 10:
                            logger.info("✓ Final fallback textarea worked!")
                            return
                except:
                    continue
            
            # Try contenteditables
            all_contenteditables = await page.locator("[contenteditable]").all()
            for ce in all_contenteditables:
                try:
                    if await ce.is_visible():
                        logger.info("Found visible contenteditable, using as final fallback")
                        await ce.scroll_into_view_if_needed()
                        await asyncio.sleep(1)
                        await ce.click()
                        await asyncio.sleep(0.5)
                        await ce.fill(prompt)
                        await asyncio.sleep(1)
                        logger.info("✓ Final fallback contenteditable worked!")
                        return
                except:
                    continue
        except Exception as e:
            logger.error(f"Final fallback also failed: {e}")
        
        # Final attempt: Wait longer and try one more time with all elements
        logger.warning("Final fallback: waiting longer and trying all elements...")
        await asyncio.sleep(3)
        
        # Get all possible input elements
        all_inputs = []
        try:
            textareas = await page.locator("textarea").all()
            all_inputs.extend([("textarea", ta) for ta in textareas])
        except:
            pass
        
        try:
            contenteditables = await page.locator("[contenteditable]").all()
            all_inputs.extend([("contenteditable", ce) for ce in contenteditables])
        except:
            pass
        
        try:
            text_inputs = await page.locator("input[type='text']").all()
            all_inputs.extend([("input", ti) for ti in text_inputs])
        except:
            pass
        
        # Try each one with JavaScript
        for input_type, element in all_inputs:
            try:
                logger.info(f"Trying final fallback with {input_type} element...")
                result = await element.evaluate(f"""
                    (prompt) => {{
                        const el = arguments[0];
                        try {{
                            el.focus();
                            if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {{
                                el.value = prompt;
                            }} else {{
                                el.textContent = prompt;
                                el.innerText = prompt;
                            }}
                            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return {{success: true, value: el.value || el.textContent}};
                        }} catch(e) {{
                            return {{success: false, error: e.message}};
                        }}
                    }}
                """, prompt)
                
                if result.get('success'):
                    value = result.get('value', '')
                    if value and (prompt[:20] in str(value) or len(str(value)) > len(prompt) * 0.8):
                        logger.info(f"✓ Prompt injected successfully via final fallback (verified: {len(str(value))} chars)")
                        await asyncio.sleep(1)
                        return
            except Exception as e:
                logger.debug(f"Final fallback attempt failed for {input_type}: {e}")
                continue
        
        # Take screenshot for debugging
        screenshot_path = None
        try:
            screenshot_path = get_screenshot_path(f"flow_inject_prompt_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            logger.error(f"Screenshot saved to {screenshot_path}")
        except:
            pass
        
        # Get page info for debugging
        try:
            page_title = await page.title()
            page_url = page.url
            body_text = await page.locator("body").text_content()
            logger.error(f"Page title: {page_title}")
            logger.error(f"Page URL: {page_url}")
            logger.error(f"Body text preview: {body_text[:200] if body_text else 'None'}...")
        except:
            pass
        
        error_msg = "Could not find or interact with prompt input element after all attempts."
        if screenshot_path:
            error_msg += f" Check screenshot: {screenshot_path}"
        raise Exception(error_msg)
    
    async def trigger_generation(self, page: Page) -> bool:
        """Click the generate button to start video generation.

        Returns:
            bool: True if generation likely started, False otherwise.
        """
        # Get selector from config and split by comma
        config_selector = FLOW_SELECTORS.get("generateButton", "")
        selectors = []
        
        # Split comma-separated selectors
        if config_selector:
            selectors.extend([s.strip() for s in config_selector.split(',')])
        
        # Add fallback selectors (ordered by specificity)
        # Based on image 2, the generate button is a circular button with right-pointing arrow
        selectors.extend([
            # Text-based selectors
            'button:has-text("Generate")',
            'button:has-text("Create")',
            # Arrow/icon-based selectors (circular button with arrow)
            'button:has(svg[class*="arrow"])',
            'button:has(svg[class*="Arrow"])',
            'button:has(svg path[d*="arrow"])',
            'button[class*="arrow"]',
            'button[class*="Arrow"]',
            # Circular button selectors
            'button[class*="circle"]',
            'button[class*="circular"]',
            'button[class*="round"]',
            # Aria labels
            'button[aria-label*="Generate"]',
            'button[aria-label*="Create"]',
            'button[aria-label*="Submit"]',
            'button[aria-label*="Send"]',
            # Type and data attributes
            'button[type="submit"]',
            'button[data-testid*="generate"]',
            'button[data-testid*="create"]',
            'button[data-testid*="submit"]',
            # Class-based selectors
            'button.primary',
            'button[class*="primary"]',
            'button[class*="generate"]',
            'button[class*="create"]',
            'button[class*="submit"]',
            # Look for buttons near the prompt input (usually at bottom right)
            'textarea ~ button',
            '[contenteditable] ~ button',
            '[role="textbox"] ~ button',
        ])
        
        # Exclude help/icon buttons - these are NOT generate buttons
        exclude_texts = ['help', 'Help', 'HELP', 'icon', 'Icon', 'menu', 'Menu', 'settings', 'Settings']
        
        logger.info(f"Trying {len(selectors)} button selectors...")
        
        # FIRST: Try to find and click the generate button (more reliable than Enter key)
        for i, selector in enumerate(selectors):
            try:
                logger.debug(f"Trying selector {i+1}/{len(selectors)}: {selector}")
                button = page.locator(selector).first
                count = await button.count()
                
                logger.debug(f"Found {count} elements with selector: {selector}")
                
                if count > 0:
                    # Check if button is visible and enabled
                    is_visible = await button.is_visible()
                    is_enabled = await button.is_enabled()
                    
                    logger.debug(f"Button visible: {is_visible}, enabled: {is_enabled}")
                    
                    if is_visible and is_enabled:
                        # Get button text for logging and validation
                        button_text = ""
                        try:
                            button_text = (await button.text_content() or "").strip()
                        except:
                            pass
                        
                        # Skip help/icon/menu buttons
                        if any(exclude in button_text for exclude in exclude_texts):
                            logger.debug(f"Skipping button with text '{button_text}' (matches exclude list)")
                            continue
                        
                        # Skip buttons that are too small (likely icons)
                        try:
                            box = await button.bounding_box()
                            if box and (box['width'] < 30 or box['height'] < 30):
                                logger.debug(f"Skipping small button (likely icon): {box['width']}x{box['height']}")
                                continue
                        except:
                            pass
                        
                        logger.info(f"Found generate button: '{button_text}' (selector: {selector})")
                        
                        # CRITICAL: Verify prompt is in textarea before clicking
                        try:
                            textarea = page.locator('textarea, [contenteditable]').first
                            if await textarea.count() > 0:
                                is_textarea = await textarea.get_attribute("tagName") == "TEXTAREA"
                                if is_textarea:
                                    prompt_value = await textarea.input_value()
                                else:
                                    prompt_value = await textarea.text_content()
                                
                                if not prompt_value or len(prompt_value.strip()) < 5:
                                    logger.warning(f"⚠️ Textarea appears empty before clicking generate button!")
                                    logger.warning("Re-injecting prompt before clicking button...")
                                    # Get the original prompt from the page context if possible
                                    # For now, we'll skip this button and try others
                                    continue
                                else:
                                    logger.info(f"✓ Verified prompt in textarea: {len(prompt_value)} chars")
                        except Exception as prompt_check_error:
                            logger.warning(f"Could not verify prompt in textarea: {prompt_check_error}")
                        
                        # Scroll button into view and click
                        await button.scroll_into_view_if_needed()
                        await asyncio.sleep(0.3)
                        await button.click(timeout=5000)
                        logger.info("✓ Generate button clicked successfully")
                        await asyncio.sleep(2)  # Wait longer for UI to respond
                        
                        # Verify prompt is still there after clicking (should be cleared if submission worked)
                        try:
                            if await textarea.count() > 0:
                                if is_textarea:
                                    prompt_after = await textarea.input_value()
                                else:
                                    prompt_after = await textarea.text_content()
                                
                                # If prompt is cleared, that's actually good - it means submission worked
                                if not prompt_after or len(prompt_after.strip()) < 5:
                                    logger.info("✓ Prompt cleared after button click - submission successful")
                                else:
                                    logger.info(f"Prompt still present after click ({len(prompt_after)} chars) - may need to wait")
                        except:
                            pass
                        
                        # Verify rendering started
                        started = await self._wait_for_render_start(page)
                        return bool(started)
                    else:
                        logger.debug(f"Button found but not visible/enabled: visible={is_visible}, enabled={is_enabled}")
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")
                continue
        
        # FALLBACK: Try Enter key only if button click didn't work
        # Note: Enter key is less reliable - it can clear the prompt without submitting
        logger.info("Button click didn't work, trying Enter key as fallback...")
        try:
            textarea = page.locator('textarea, [contenteditable]').first
            if await textarea.count() > 0:
                # Verify prompt is still in textarea
                is_textarea = await textarea.get_attribute("tagName") == "TEXTAREA"
                if is_textarea:
                    prompt_value = await textarea.input_value()
                else:
                    prompt_value = await textarea.text_content()
                
                if prompt_value and len(prompt_value.strip()) >= 5:
                    logger.info(f"✓ Prompt verified in textarea ({len(prompt_value)} chars), pressing Enter...")
                    await textarea.focus()
                    await asyncio.sleep(0.5)  # Wait for focus
                    
                    # Press Enter
                    await textarea.press("Enter")
                    logger.info("✓ Enter key pressed")
                    await asyncio.sleep(2)  # Wait longer for UI to respond
                    
                    # CRITICAL: Verify prompt is still there after Enter
                    # If prompt was cleared, Enter might have worked (or might have failed)
                    if is_textarea:
                        prompt_after = await textarea.input_value()
                    else:
                        prompt_after = await textarea.text_content()
                    
                    logger.info(f"Prompt after Enter: {len(prompt_after) if prompt_after else 0} chars")
                    
                    # Check if prompt was cleared - if so, assume Enter worked
                    if not prompt_after or len(prompt_after.strip()) < 5:
                        logger.info("Prompt cleared after Enter - assuming submission worked")
                        started = await self._wait_for_render_start(page)
                        return bool(started)
                    else:
                        logger.warning(f"⚠️ Prompt still present after Enter ({len(prompt_after)} chars) - Enter may not have worked")
                        # Prompt is still there - Enter might not have worked
                        # But we'll proceed anyway and let wait_for_render_start handle it
                        await self._wait_for_render_start(page)
                        return
                else:
                    logger.warning(f"⚠️ Textarea is empty before pressing Enter! Prompt value: '{prompt_value[:50] if prompt_value else 'None'}'")
        except Exception as enter_error:
            logger.warning(f"Enter key method failed: {enter_error}")
        
        # JavaScript fallback: Try to find and click arrow button (circular button with right arrow)
        logger.info("Trying JavaScript fallback to find arrow/generate button...")
        try:
            # First, get button info for logging
            button_info = await page.evaluate("""
                () => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const textarea = document.querySelector('textarea, [contenteditable]');
                    const results = [];
                    
                    for (const btn of buttons) {
                        if (!btn.offsetParent) continue;
                        const btnRect = btn.getBoundingClientRect();
                        const textareaRect = textarea ? textarea.getBoundingClientRect() : null;
                        
                        // Check if button is near textarea
                        let isNearTextarea = false;
                        if (textareaRect) {
                            isNearTextarea = btnRect.left > textareaRect.right - 100 && 
                                           btnRect.top > textareaRect.top - 50 &&
                                           btnRect.bottom < textareaRect.bottom + 50;
                        }
                        
                        const svg = btn.querySelector('svg');
                        const hasArrow = svg && svg.querySelectorAll('path').length > 0;
                        const isCircular = Math.abs(btnRect.width - btnRect.height) < 10 && btnRect.width > 30;
                        
                        results.push({
                            text: btn.textContent?.trim() || '',
                            ariaLabel: btn.getAttribute('aria-label') || '',
                            visible: btn.offsetParent !== null,
                            enabled: !btn.disabled,
                            isCircular: isCircular,
                            isNearTextarea: isNearTextarea,
                            hasArrow: hasArrow,
                            position: {x: btnRect.x, y: btnRect.y, width: btnRect.width, height: btnRect.height}
                        });
                    }
                    return results;
                }
            """)
            
            logger.info(f"Found {len(button_info)} buttons. Analyzing for generate button...")
            for i, btn_info in enumerate(button_info[:10]):  # Log first 10
                logger.debug(f"Button {i+1}: text='{btn_info['text']}', aria-label='{btn_info['ariaLabel']}', "
                           f"circular={btn_info['isCircular']}, near_textarea={btn_info['isNearTextarea']}, "
                           f"has_arrow={btn_info['hasArrow']}, enabled={btn_info['enabled']}")
            
            clicked = await page.evaluate(r"""
                () => {
                    // Find all buttons
                    const buttons = Array.from(document.querySelectorAll('button'));
                    
                    // Look for buttons with arrow icons (usually the generate button)
                    for (const btn of buttons) {
                        if (!btn.offsetParent) continue; // Skip hidden buttons
                        if (btn.disabled) continue;
                        
                        // Check for arrow icon in SVG
                        const svg = btn.querySelector('svg');
                        if (svg) {
                            const paths = svg.querySelectorAll('path');
                            for (const path of paths) {
                                const d = path.getAttribute('d') || '';
                                // Arrow paths typically have M and L commands pointing right
                                if (d.includes('M') && (d.includes('L') || d.includes('l'))) {
                                    // Check if it's a right-pointing arrow (common pattern)
                                    const isRightArrow = d.match(/M[\d.]+ [\d.]+ L[\d.]+ [\d.]+/);
                                    if (isRightArrow || d.length > 20) { // Arrow paths are usually longer
                                        btn.scrollIntoView({behavior: 'smooth', block: 'center'});
                                        btn.click();
                                        return {success: true, type: 'arrow_icon', buttonInfo: {
                                            text: btn.textContent?.trim() || '',
                                            ariaLabel: btn.getAttribute('aria-label') || '',
                                            position: {x: btn.getBoundingClientRect().x, y: btn.getBoundingClientRect().y}
                                        }};
                                    }
                                }
                            }
                        }
                        
                        // Also check for circular buttons near textarea (usually generate button)
                        const textarea = document.querySelector('textarea, [contenteditable]');
                        if (textarea) {
                            const textareaRect = textarea.getBoundingClientRect();
                            const btnRect = btn.getBoundingClientRect();
                            
                            // Check if button is to the right and near the textarea
                            if (btnRect.left > textareaRect.right - 100 && 
                                btnRect.top > textareaRect.top - 50 &&
                                btnRect.bottom < textareaRect.bottom + 50) {
                                // Check if it's circular (width ≈ height)
                                const isCircular = Math.abs(btnRect.width - btnRect.height) < 10 && btnRect.width > 30;
                                if (isCircular) {
                                    btn.scrollIntoView({behavior: 'smooth', block: 'center'});
                                    btn.click();
                                    return {success: true, type: 'circular_near_input', buttonInfo: {
                                        text: btn.textContent?.trim() || '',
                                        ariaLabel: btn.getAttribute('aria-label') || '',
                                        position: {x: btnRect.x, y: btnRect.y, width: btnRect.width, height: btnRect.height}
                                    }};
                                }
                            }
                        }
                    }
                    
                    return {success: false};
                }
            """)
            
            if clicked.get('success'):
                btn_info = clicked.get('buttonInfo', {})
                logger.info(f"✓ Clicked generate button via JavaScript ({clicked.get('type')})")
                logger.info(f"  Button details: text='{btn_info.get('text', '')}', aria-label='{btn_info.get('ariaLabel', '')}', "
                          f"position=({btn_info.get('position', {}).get('x', '?')}, {btn_info.get('position', {}).get('y', '?')})")
                
                # Verify prompt is in textarea before proceeding
                try:
                    textarea = page.locator('textarea, [contenteditable]').first
                    if await textarea.count() > 0:
                        prompt_value = await textarea.input_value() if await textarea.get_attribute("tagName") == "TEXTAREA" else await textarea.text_content()
                        if not prompt_value or len(prompt_value.strip()) < 5:
                            logger.warning(f"⚠️ Textarea appears empty after clicking generate button!")
                        else:
                            logger.info(f"✓ Verified prompt in textarea: {len(prompt_value)} chars")
                except Exception as prompt_check_error:
                    logger.warning(f"Could not verify prompt in textarea: {prompt_check_error}")
                
                await asyncio.sleep(1)  # Brief wait for UI to respond
                await self._wait_for_render_start(page)
                return
            else:
                logger.debug("JavaScript fallback did not find generate button")
        except Exception as js_error:
            logger.debug(f"JavaScript fallback failed: {js_error}")
        
        # Take screenshot for debugging
        screenshot_path = None
        try:
            screenshot_path = get_screenshot_path(f"flow_generate_button_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            logger.error(f"Screenshot saved to {screenshot_path}")
        except:
            pass
        
        # Get all buttons on page for debugging
        try:
            all_buttons = await page.locator("button").all()
            button_info = []
            for btn in all_buttons[:20]:  # Check more buttons
                try:
                    text = await btn.text_content()
                    aria_label = await btn.get_attribute("aria-label")
                    is_vis = await btn.is_visible()
                    is_en = await btn.is_enabled()
                    # Get button position to identify bottom-right buttons
                    box = await btn.bounding_box()
                    pos_info = f"pos=({int(box['x'])},{int(box['y'])})" if box else "pos=unknown"
                    btn_desc = f"'{text or aria_label or ''}' (visible={is_vis}, enabled={is_en}, {pos_info})"
                    button_info.append(btn_desc)
                except:
                    pass
            logger.error(f"Available buttons on page: {', '.join(button_info)}")
            
            # Also try to find buttons with arrow icons using JavaScript
            try:
                arrow_buttons = await page.evaluate("""
                    () => {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const arrowButtons = buttons.filter(btn => {
                            const svg = btn.querySelector('svg');
                            if (!svg) return false;
                            const paths = svg.querySelectorAll('path');
                            for (const path of paths) {
                                const d = path.getAttribute('d') || '';
                                if (d.includes('arrow') || d.includes('M') && d.includes('L')) {
                                    return true;
                                }
                            }
                            return false;
                        });
                        return arrowButtons.map(btn => ({
                            text: btn.textContent?.trim() || '',
                            ariaLabel: btn.getAttribute('aria-label') || '',
                            visible: btn.offsetParent !== null,
                            enabled: !btn.disabled
                        }));
                    }
                """)
                if arrow_buttons:
                    logger.info(f"Found {len(arrow_buttons)} buttons with arrow icons: {arrow_buttons}")
            except:
                pass
        except:
            pass
        
        error_msg = "Could not find or click generate button."
        if screenshot_path:
            error_msg += f" Check screenshot: {screenshot_path}"
        raise Exception(error_msg)
    
    async def _wait_for_render_start(self, page: Page, timeout: int = 15000) -> None:
        """Wait for rendering UI to appear - verify generation actually started"""
        start_time = asyncio.get_event_loop().time()
        
        logger.info("Verifying video generation started...")
        
        # Take screenshot before checking
        try:
            screenshot_path = get_screenshot_path(f"before_render_start_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            logger.debug(f"Screenshot saved: {screenshot_path}")
        except:
            pass
        
        while (asyncio.get_event_loop().time() - start_time) * 1000 < timeout:
            try:
                # Check for loading indicators
                loading_selectors = [
                    '.loading',
                    '[aria-busy="true"]',
                    '.spinner',
                    '[class*="loading"]',
                    '[class*="Loading"]',
                    '[class*="spinner"]',
                    '[class*="Spinner"]',
                    'svg[class*="spinner"]',
                    'div[class*="progress"]',
                ]
                
                has_loading = False
                for selector in loading_selectors:
                    try:
                        count = await page.locator(selector).count()
                        if count > 0:
                            # Check if at least one is visible
                            for i in range(min(count, 5)):
                                elem = page.locator(selector).nth(i)
                                if await elem.is_visible():
                                    has_loading = True
                                    logger.info(f"✓ Found loading indicator: {selector}")
                                    break
                            if has_loading:
                                break
                    except:
                        continue
                
                # Check for render/video area
                render_selectors = [
                    '.render-area',
                    '.video-preview',
                    '[class*="render"]',
                    '[class*="Render"]',
                    '[class*="video-preview"]',
                    '[class*="VideoPreview"]',
                    'video',
                    'canvas',
                ]
                
                has_render_area = False
                for selector in render_selectors:
                    try:
                        count = await page.locator(selector).count()
                        if count > 0:
                            for i in range(min(count, 5)):
                                elem = page.locator(selector).nth(i)
                                if await elem.is_visible():
                                    has_render_area = True
                                    logger.info(f"✓ Found render area: {selector}")
                                    break
                            if has_render_area:
                                break
                    except:
                        continue
                
                # Check if textarea is disabled (indicates generation started)
                try:
                    textarea = page.locator('textarea, [contenteditable]').first
                    if await textarea.count() > 0:
                        is_disabled = await textarea.is_disabled()
                        is_readonly = await textarea.get_attribute("readonly")
                        if is_disabled or is_readonly:
                            logger.info("✓ Textarea disabled/readonly - generation likely started")
                            has_loading = True
                except:
                    pass
                
                # Check for generation status text
                try:
                    status_texts = [
                        "text=Generating",
                        "text=Creating",
                        "text=Processing",
                        "text=Đang tạo",  # Vietnamese "Creating"
                        "text=Đang xử lý",  # Vietnamese "Processing"
                    ]
                    for status_selector in status_texts:
                        try:
                            status_elem = page.locator(status_selector).first
                            if await status_elem.count() > 0 and await status_elem.is_visible():
                                status_text = await status_elem.text_content()
                                logger.info(f"✓ Found generation status: {status_text}")
                                has_loading = True
                                break
                        except:
                            continue
                except:
                    pass
                
                if has_loading or has_render_area:
                    logger.info("✓ Video generation started successfully")
                    return
            except Exception as e:
                logger.debug(f"Error checking render start: {e}")
            
            await asyncio.sleep(0.5)
        
        # Take screenshot after timeout to see what's on screen
        try:
            screenshot_path = get_screenshot_path(f"render_start_timeout_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            logger.warning(f"Render start timeout - screenshot saved: {screenshot_path}")
            
            # Check if prompt is still in textarea (might not have been sent)
            try:
                textarea = page.locator('textarea, [contenteditable]').first
                if await textarea.count() > 0:
                    prompt_text = await textarea.input_value() if await textarea.get_attribute("tagName") == "TEXTAREA" else await textarea.text_content()
                    logger.warning(f"Textarea still contains: {prompt_text[:100] if prompt_text else 'empty'}")
            except:
                pass
        except:
            pass
        
        logger.warning("Render start timeout - continuing anyway (generation may have started but indicators not detected)")
    
    async def wait_for_completion(
        self,
        page: Page,
        timeout: int = 600000  # 10 minutes (increased from 5 minutes to handle longer generation times)
    ) -> dict:
        """
        Wait for video generation to complete.
        Returns dict with status and result.
        """
        start_time = asyncio.get_event_loop().time()
        poll_interval = POLLING_INTERVAL_MS / 1000
        last_log_time = start_time
        
        logger.info(f"Waiting for video generation to complete (timeout: {timeout/1000:.0f} seconds)...")
        
        while (asyncio.get_event_loop().time() - start_time) * 1000 < timeout:
            try:
                # CRITICAL FIX: Don't check for errors too early - wait for video generation to start
                # If we're checking immediately after trigger_generation, skip error detection entirely
                elapsed_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                skip_error_detection = elapsed_ms < 10000  # First 10 seconds - skip error detection completely
                
                if skip_error_detection:
                    logger.debug(f"Early check (elapsed: {elapsed_ms:.0f}ms) - skipping error detection, only checking for video")
                
                # Check for video element - try multiple selectors and methods
                video_selectors = [
                    "video",
                    "video[src]",
                    "[class*='video']",
                    "[class*='Video']",
                    "iframe[src*='video']",
                ]
                
                # First, try JavaScript-based detection (more reliable)
                try:
                    video_info = await page.evaluate("""
                        () => {
                            const videos = document.querySelectorAll('video');
                            const results = [];
                            
                            for (const video of videos) {
                                if (!video.offsetParent) continue; // Skip hidden videos
                                
                                const src = video.src || video.currentSrc || '';
                                const readyState = video.readyState || 0;
                                const duration = video.duration || 0;
                                const paused = video.paused;
                                
                                // Check if video has content (readyState >= 2 means it has loaded metadata)
                                if (readyState >= 2 || duration > 0 || src) {
                                    results.push({
                                        hasSrc: !!src,
                                        src: src,
                                        readyState: readyState,
                                        duration: duration,
                                        paused: paused,
                                        visible: video.offsetParent !== null,
                                        hasPoster: !!video.poster,
                                        poster: video.poster || ''
                                    });
                                }
                            }
                            
                            // Also check for video containers/players
                            const videoContainers = document.querySelectorAll('[class*="video"], [class*="Video"], [class*="player"], [class*="Player"]');
                            for (const container of videoContainers) {
                                if (container.offsetParent && container.querySelector('video')) {
                                    results.push({
                                        hasContainer: true,
                                        visible: true
                                    });
                                }
                            }
                            
                            return results;
                        }
                    """)
                    
                    if video_info and len(video_info) > 0:
                        logger.debug(f"JavaScript found {len(video_info)} video element(s)")
                        for i, info in enumerate(video_info):
                            logger.debug(f"Video {i+1}: src={bool(info.get('src'))}, readyState={info.get('readyState')}, duration={info.get('duration')}, visible={info.get('visible')}")
                            
                            # If video has src or is ready, consider it complete
                            if info.get('src') or info.get('readyState', 0) >= 2 or info.get('duration', 0) > 0:
                                video_src = info.get('src') or info.get('poster') or ''
                                if video_src:
                                    logger.info(f"Video generation completed (JavaScript detection: src={video_src[:50]}...)")
                                    return {"status": "completed", "video_url": video_src}
                                elif info.get('hasContainer') or info.get('visible'):
                                    # Video element exists and is visible - might be loading, wait a bit more
                                    logger.info("Video element detected but no src yet - waiting for video to load...")
                                    await asyncio.sleep(2)
                                    # Re-check after waiting
                                    video_src = await page.evaluate("""
                                        () => {
                                            const video = document.querySelector('video');
                                            if (video && video.offsetParent) {
                                                return video.src || video.currentSrc || '';
                                            }
                                            return '';
                                        }
                                    """)
                                    if video_src:
                                        logger.info(f"Video src loaded after wait: {video_src[:50]}...")
                                        return {"status": "completed", "video_url": video_src}
                except Exception as js_error:
                    logger.debug(f"JavaScript video detection failed: {js_error}")
                
                # Fallback: Try Playwright selectors
                for video_selector in video_selectors:
                    try:
                        video = page.locator(video_selector).first
                        if await video.count() > 0:
                            # Check if video is visible
                            is_visible = await video.is_visible()
                            if not is_visible:
                                continue
                            
                            # Check if video has src attribute
                            src = await video.get_attribute("src")
                            if src and (src.startswith("http") or src.startswith("blob:") or src.startswith("data:")):
                                logger.info(f"Video generation completed (found via selector: {video_selector})")
                                return {"status": "completed", "video_url": src}
                            
                            # Check video readyState via JavaScript
                            try:
                                ready_state = await video.evaluate("el => el.readyState || 0")
                                duration = await video.evaluate("el => el.duration || 0")
                                if ready_state >= 2 or duration > 0:
                                    # Video has loaded metadata or has duration
                                    current_src = await video.evaluate("el => el.src || el.currentSrc || ''")
                                    if current_src:
                                        logger.info(f"Video generation completed (readyState={ready_state}, duration={duration})")
                                        return {"status": "completed", "video_url": current_src}
                                    else:
                                        logger.info(f"Video element ready (readyState={ready_state}, duration={duration}) but no src - may be loading")
                            except:
                                pass
                            
                            # Try to get video URL from different attributes
                            for attr in ["src", "data-src", "data-url", "poster", "currentSrc"]:
                                try:
                                    attr_value = await video.get_attribute(attr) if attr != "currentSrc" else await video.evaluate("el => el.currentSrc || ''")
                                    if attr_value and (attr_value.startswith("http") or attr_value.startswith("blob:") or attr_value.startswith("data:")):
                                        logger.info(f"Video generation completed (found URL in {attr} attribute)")
                                        return {"status": "completed", "video_url": attr_value}
                                except:
                                    continue
                    except:
                        continue
                
                # Check for download button - try multiple selectors
                download_selectors = [
                    'button:has-text("Download")',
                    'button:has-text("Tải xuống")',  # Vietnamese "Download"
                    'a[download]',
                    '[aria-label*="Download"]',
                    '[aria-label*="download"]',
                    '[class*="download"]',
                    '[class*="Download"]',
                ]
                
                # Also check via JavaScript for download buttons
                try:
                    download_buttons = await page.evaluate("""
                        () => {
                            const buttons = Array.from(document.querySelectorAll('button, a'));
                            const results = [];
                            
                            for (const btn of buttons) {
                                if (!btn.offsetParent) continue;
                                
                                const text = (btn.textContent || '').toLowerCase();
                                const ariaLabel = (btn.getAttribute('aria-label') || '').toLowerCase();
                                const className = (btn.className || '').toLowerCase();
                                const hasDownload = btn.hasAttribute('download') || 
                                                   text.includes('download') || 
                                                   text.includes('tải xuống') ||
                                                   ariaLabel.includes('download') ||
                                                   className.includes('download');
                                
                                if (hasDownload) {
                                    results.push({
                                        text: btn.textContent?.trim() || '',
                                        visible: btn.offsetParent !== null,
                                        hasDownloadAttr: btn.hasAttribute('download')
                                    });
                                }
                            }
                            
                            return results;
                        }
                    """)
                    
                    if download_buttons and len(download_buttons) > 0:
                        logger.info(f"Download button detected via JavaScript: {download_buttons[0].get('text', '')}")
                        return {"status": "completed", "has_download": True}
                except Exception as js_dl_error:
                    logger.debug(f"JavaScript download button detection failed: {js_dl_error}")
                
                # Fallback: Try Playwright selectors
                for download_selector in download_selectors:
                    try:
                        download_btn = page.locator(download_selector).first
                        if await download_btn.count() > 0 and await download_btn.is_visible():
                            logger.info(f"Download button appeared - generation completed (found via selector: {download_selector})")
                            return {"status": "completed", "has_download": True}
                    except:
                        continue
                
                # Check for video preview/thumbnail that indicates completion
                preview_selectors = [
                    '[class*="preview"]',
                    '[class*="Preview"]',
                    '[class*="thumbnail"]',
                    '[class*="Thumbnail"]',
                    'img[alt*="video"]',
                    'img[alt*="Video"]',
                ]
                
                for preview_selector in preview_selectors:
                    try:
                        preview = page.locator(preview_selector).first
                        if await preview.count() > 0 and await preview.is_visible():
                            # Check if it's actually a video preview (has video-related attributes)
                            src = await preview.get_attribute("src")
                            alt = await preview.get_attribute("alt")
                            if src or (alt and "video" in alt.lower()):
                                logger.info(f"Video preview detected - generation may be completed (found via selector: {preview_selector})")
                                # Don't return yet - wait a bit more to ensure video is ready
                                await asyncio.sleep(2)
                                # Re-check for actual video element
                                video = page.locator("video").first
                                if await video.count() > 0:
                                    video_src = await video.get_attribute("src")
                                    if video_src:
                                        logger.info("Video element found after preview detection")
                                        return {"status": "completed", "video_url": video_src}
                    except:
                        continue
                
                # FIX: Skip error detection in early stages to avoid false positives
                if skip_error_detection:
                    # Skip all error detection - just continue polling
                    await asyncio.sleep(poll_interval)
                    continue
                
                # Check for errors - try multiple strategies
                # FIX: Be more specific - only detect actual error messages, not generic UI elements
                error_found = False
                error_text = None
                
                # Strategy 1: Check for specific error messages (not just "Error" text)
                # These are actual error messages that indicate failure
                specific_error_messages = [
                    "text=Something went wrong",
                    "text=You need more AI credits",
                    "text=Không tải được số tín dụng",  # Vietnamese "Could not load credits"
                    "text=Rất tiếc, đã xảy ra lỗi!",  # Vietnamese "Unfortunately, an error occurred!"
                    "text=Unfortunately, an error occurred!",
                    "text=Generation failed",
                    "text=Failed to generate",
                    "text=Error generating video",
                    "text=Unable to generate",
                ]
                
                for error_selector in specific_error_messages:
                    try:
                        error_elem = page.locator(error_selector).first
                        if await error_elem.count() > 0 and await error_elem.is_visible():
                            error_text = await error_elem.text_content()
                            if error_text and len(error_text.strip()) > 10:  # Must be substantial message
                                error_found = True
                                logger.warning(f"Specific error message found: {error_text[:100]}")
                                
                                # Try to close Google account error popup if it's that type of error
                                if "Rất tiếc" in error_text or "Unfortunately, an error occurred" in error_text:
                                    logger.info("Attempting to close Google account error popup...")
                                    try:
                                        close_selectors = [
                                            'button:has-text("Đóng")',
                                            'button:has-text("Close")',
                                            '[aria-label*="Close"]',
                                            '[aria-label*="Đóng"]',
                                            'button[class*="close"]',
                                            'button[class*="Close"]',
                                        ]
                                        for close_sel in close_selectors:
                                            try:
                                                close_btn = page.locator(close_sel).first
                                                if await close_btn.count() > 0 and await close_btn.is_visible():
                                                    await close_btn.click()
                                                    await asyncio.sleep(1)
                                                    logger.info("✓ Closed error popup")
                                                    break
                                            except:
                                                continue
                                    except Exception as close_error:
                                        logger.debug(f"Could not close error popup: {close_error}")
                                
                                break
                    except:
                        continue
                
                # Strategy 2: Check for error dialogs/toasts (more reliable than generic error elements)
                if not error_found:
                    error_dialog_selectors = [
                        '[role="dialog"]:has-text("Rất tiếc")',  # Google account popup error
                        '[role="alertdialog"]:has-text("Rất tiếc")',
                        '[role="dialog"]:has-text("error")',
                        '[role="alert"]:has-text("failed")',
                        '[role="alert"]:has-text("error")',
                        '[aria-live="assertive"]:has-text("error")',
                        '[aria-live="assertive"]:has-text("failed")',
                    ]
                    for selector in error_dialog_selectors:
                        try:
                            error_elem = page.locator(selector).first
                            if await error_elem.count() > 0 and await error_elem.is_visible():
                                error_text = await error_elem.text_content()
                                # Filter out false positives - must be substantial error message
                                if error_text and len(error_text.strip()) > 15:
                                    # Check if it's actually an error (not just UI text)
                                    error_lower = error_text.lower()
                                    if any(keyword in error_lower for keyword in ["error", "failed", "wrong", "lỗi", "tiếc"]):
                                        error_found = True
                                        logger.warning(f"Error dialog found: {error_text[:100]}")
                                        break
                        except:
                            continue
                
                # Strategy 3: Check configured error selector (only if it's a specific error class)
                if not error_found:
                    try:
                        error_selector = FLOW_SELECTORS.get("errorMessage", ".error")
                        # Only check if it's a specific error class, not generic ".error"
                        if error_selector != ".error":  # Skip generic error selector
                            error = page.locator(error_selector).first
                            if await error.count() > 0 and await error.is_visible():
                                error_text = await error.text_content()
                                if error_text and len(error_text.strip()) > 10:
                                    error_found = True
                                    logger.warning(f"Configured error selector found: {error_text[:100]}")
                    except:
                        pass
                
                # Strategy 4: Check page body for specific error patterns (last resort)
                # Only check if we haven't found an error yet and we're looking for specific patterns
                if not error_found:
                    try:
                        body_text = await page.locator("body").text_content() or ""
                        body_lower = body_text.lower()
                        
                        # FIX: Only check for specific error patterns, not generic "error" text
                        # Check for Google account popup errors (specific pattern)
                        if "rất tiếc, đã xảy ra lỗi" in body_lower or "unfortunately, an error occurred" in body_lower:
                            # Try to find the specific error message element
                            google_error_selectors = [
                                "text=Rất tiếc, đã xảy ra lỗi!",
                                "text=Unfortunately, an error occurred!",
                                '[role="dialog"]:has-text("Rất tiếc")',
                                '[role="alertdialog"]:has-text("Rất tiếc")',
                            ]
                            for selector in google_error_selectors:
                                try:
                                    elem = page.locator(selector).first
                                    if await elem.count() > 0 and await elem.is_visible():
                                        error_text = await elem.text_content()
                                        if error_text and len(error_text.strip()) > 10:
                                            error_found = True
                                            error_text = error_text.strip()
                                            logger.error(f"Google account popup error detected: {error_text[:200]}")
                                            break
                                except:
                                    continue
                            
                            if not error_found:
                                error_text = "Google account error: Rất tiếc, đã xảy ra lỗi! (Unfortunately, an error occurred!)"
                                error_found = True
                        
                        # Check for credit loading errors (specific pattern)
                        elif not error_found and "không tải được số tín dụng" in body_lower:
                            # Try to extract the specific error message
                            credit_error_selectors = [
                                "text=Không tải được số tín dụng của bạn",
                                "text=Could not load your credits",
                                '[role="alert"]:has-text("tín dụng")',
                            ]
                            for selector in credit_error_selectors:
                                try:
                                    elem = page.locator(selector).first
                                    if await elem.count() > 0 and await elem.is_visible():
                                        error_text = await elem.text_content()
                                        if error_text and len(error_text.strip()) > 10:
                                            error_found = True
                                            break
                                except:
                                    continue
                            
                            if not error_found:
                                error_text = "Credit loading error: Không tải được số tín dụng của bạn"
                                error_found = True
                        
                        # Check for insufficient credits error (specific pattern)
                        elif not error_found and ("you need more ai credits" in body_lower or "cần thêm tín dụng" in body_lower):
                            credit_error_selectors = [
                                "text=You need more AI credits",
                                "text=Cần thêm tín dụng AI",
                            ]
                            for selector in credit_error_selectors:
                                try:
                                    elem = page.locator(selector).first
                                    if await elem.count() > 0 and await elem.is_visible():
                                        error_text = await elem.text_content()
                                        if error_text and len(error_text.strip()) > 10:
                                            error_found = True
                                            break
                                except:
                                    continue
                            
                            if not error_found:
                                error_text = "Insufficient AI credits"
                                error_found = True
                    except Exception as body_check_error:
                        logger.debug(f"Error checking body text: {body_check_error}")
                        pass
                
                # FIX: Only return error if we found a substantial, specific error message
                # Don't return error for generic UI elements or false positives
                if error_found and error_text:
                    error_text_clean = error_text.strip()
                    
                    # Log what we found for debugging
                    logger.debug(f"Error detection found: error_found={error_found}, error_text='{error_text_clean[:100]}'")
                    
                    # Filter out very short or generic error messages (likely false positives)
                    if len(error_text_clean) < 10:
                        logger.debug(f"Ignoring short/generic error text: '{error_text_clean}' (likely false positive)")
                        error_found = False  # Don't treat as error
                    elif error_text_clean.lower() in ["flow", "error", "failed", "loading", "insufficient ai credits"]:
                        logger.debug(f"Ignoring generic error text: '{error_text_clean}' (likely false positive)")
                        error_found = False  # Don't treat as error
                    elif "error detected on flow page" in error_text_clean.lower():
                        # This is the generic fallback message - don't treat as error
                        logger.debug(f"Ignoring generic fallback error message: '{error_text_clean}' (likely false positive)")
                        error_found = False  # Don't treat as error
                    else:
                        # Valid error message found - check if it's actually an error
                        # Only return error if it's a known error pattern
                        known_error_patterns = [
                            "something went wrong",
                            "generation failed",
                            "failed to generate",
                            "error generating",
                            "unable to generate",
                            "rất tiếc",
                            "đã xảy ra lỗi",
                            "unfortunately, an error occurred",
                            "không tải được số tín dụng",
                            "could not load your credits",
                            "you need more ai credits",
                            "cần thêm tín dụng"
                        ]
                        
                        error_lower = error_text_clean.lower()
                        is_known_error = any(pattern in error_lower for pattern in known_error_patterns)
                        
                        if is_known_error:
                            # Valid error message found
                            logger.error(f"Render error detected on page: {error_text_clean[:200]}")
                            return {"status": "error", "error": error_text_clean[:500]}  # Limit length
                        else:
                            # Not a known error pattern - likely false positive
                            logger.debug(f"Ignoring error text that doesn't match known patterns: '{error_text_clean[:100]}' (likely false positive)")
                            error_found = False  # Don't treat as error
                
                # If error_found but no text, it's likely a false positive - don't treat as error
                # (We already filtered these out above, but just in case)
                if error_found and not error_text:
                    logger.debug("Error element found but no text - likely false positive, ignoring")
                    error_found = False
                
            except Exception as e:
                logger.debug(f"Error checking completion: {e}")
            
            # Log progress every 30 seconds
            current_time = asyncio.get_event_loop().time()
            if current_time - last_log_time >= 30:
                elapsed_seconds = (current_time - start_time)
                remaining_seconds = (timeout / 1000) - elapsed_seconds
                logger.info(f"Still waiting for video generation... (elapsed: {elapsed_seconds:.0f}s, remaining: {remaining_seconds:.0f}s)")
                last_log_time = current_time
            
            await asyncio.sleep(poll_interval)
        
        elapsed_seconds = (asyncio.get_event_loop().time() - start_time)
        logger.error(f"Render timeout exceeded after {elapsed_seconds:.0f} seconds")
        return {"status": "timeout", "error": f"Render timeout exceeded after {elapsed_seconds:.0f} seconds"}
    
    async def download_video(
        self,
        page: Page,
        output_path: str,
        scene_id: str
    ) -> str:
        """Download video from Flow UI"""
        try:
            # Ensure output directory exists
            Path(output_path).mkdir(parents=True, exist_ok=True)
            
            # First, try to get video URL directly from video element (faster and more reliable)
            video = page.locator(FLOW_SELECTORS.get("videoElement", "video")).first
            if await video.count() > 0:
                video_src = await video.get_attribute("src")
                if video_src and video_src.startswith("http"):
                    logger.info(f"Found video URL: {video_src}")
                    # Download from URL directly
                    import httpx
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        response = await client.get(video_src)
                        response.raise_for_status()
                        
                        output_file = Path(output_path) / f"scene_{scene_id}.mp4"
                        with open(output_file, "wb") as f:
                            f.write(response.content)
                        
                        logger.info(f"Video downloaded to {output_file}")
                        return str(output_file.absolute())
            
            # Fallback: Try download button with download event
            logger.info("Video URL not found, trying download button...")
            try:
                async with page.expect_download(timeout=10000) as download_info:
                    download_btn = page.locator(FLOW_SELECTORS.get("downloadButton", "button")).first
                    if await download_btn.count() > 0 and await download_btn.is_visible():
                        await download_btn.click()
                    else:
                        # Try to find any download link
                        download_link = page.locator("a[download], button:has-text('Download')").first
                        if await download_link.count() > 0:
                            await download_link.click()
                        else:
                            raise Exception("No download button found")
                
                download = await download_info.value
                output_file = Path(output_path) / f"scene_{scene_id}.mp4"
                await download.save_as(output_file)
                logger.info(f"Video downloaded to {output_file}")
                return str(output_file.absolute())
            except Exception as download_error:
                logger.warning(f"Download button method failed: {download_error}")
                # If download button fails, try to get video URL again (might have appeared)
                video = page.locator(FLOW_SELECTORS.get("videoElement", "video")).first
                if await video.count() > 0:
                    video_src = await video.get_attribute("src")
                    if video_src and video_src.startswith("http"):
                        logger.info(f"Retrying with video URL: {video_src}")
                        import httpx
                        async with httpx.AsyncClient(timeout=60.0) as client:
                            response = await client.get(video_src)
                            response.raise_for_status()
                            
                            output_file = Path(output_path) / f"scene_{scene_id}.mp4"
                            with open(output_file, "wb") as f:
                                f.write(response.content)
                            
                            logger.info(f"Video downloaded to {output_file}")
                            return str(output_file.absolute())
                
                raise download_error
        except Exception as e:
            logger.error(f"Failed to download video: {e}")
            raise
