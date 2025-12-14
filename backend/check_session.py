#!/usr/bin/env python3
"""
Diagnostic script to check Chrome profile session/cookie state
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.browser_manager import BrowserManager
from app.services.profile_manager import ProfileManager
from app.config import config_manager, settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_profile_session():
    """Check if profile has valid session/cookies"""
    try:
        # Get active profile
        profile_manager = ProfileManager()
        active_profile = profile_manager.get_active_profile()
        
        if not active_profile:
            logger.error("No active profile found!")
            return
        
        logger.info(f"Checking profile: {active_profile.name}")
        logger.info(f"Profile path: {active_profile.profile_path}")
        
        profile_path = Path(active_profile.profile_path)
        
        # Check profile structure
        default_dir = profile_path / "Default"
        if not default_dir.exists():
            logger.warning("Default directory does not exist!")
            return
        
        # Check for cookies file
        cookies_file = default_dir / "Cookies"
        if cookies_file.exists():
            cookie_size = cookies_file.stat().st_size
            logger.info(f"✓ Cookies file exists ({cookie_size} bytes)")
        else:
            logger.warning("✗ Cookies file NOT found - session will not be restored")
        
        # Check for Login Data
        login_data = default_dir / "Login Data"
        if login_data.exists():
            logger.info("✓ Login Data file exists")
        else:
            logger.warning("✗ Login Data file NOT found")
        
        # Initialize browser and check cookies
        logger.info("\nInitializing browser...")
        browser_manager = BrowserManager()
        await browser_manager.initialize_with_profile_path(profile_path)
        
        # Create a page and check cookies
        page = await browser_manager.new_page()
        
        try:
            # Navigate to Flow
            flow_url = config_manager.get("flow.url", settings.FLOW_URL)
            logger.info(f"Navigating to {flow_url}...")
            await page.goto(flow_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            # Check cookies after navigation
            cookies = await page.context.cookies()
            logger.info(f"\nTotal cookies in context: {len(cookies)}")
            
            # Filter Google cookies
            google_cookies = [c for c in cookies if "google.com" in c.get("domain", "")]
            logger.info(f"Google cookies: {len(google_cookies)}")
            
            if google_cookies:
                logger.info("\nGoogle cookie domains:")
                for cookie in google_cookies[:10]:  # Show first 10
                    domain = cookie.get("domain", "")
                    name = cookie.get("name", "")
                    logger.info(f"  - {domain}: {name[:30]}...")
            
            # Check current URL
            current_url = page.url
            logger.info(f"\nCurrent URL: {current_url}")
            
            if "accounts.google.com" in current_url or "/signin" in current_url:
                logger.error("✗ REDIRECTED TO LOGIN - Session not valid!")
            elif "labs.google" in current_url and "flow" in current_url:
                logger.info("✓ On Flow page - Session appears valid")
            else:
                logger.warning(f"? Unknown page: {current_url}")
            
            # Take screenshot
            screenshot_path = profile_path.parent.parent / "logs" / "session_check.png"
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            await page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info(f"\nScreenshot saved to: {screenshot_path}")
            
        finally:
            await page.close()
            await browser_manager.close()
        
    except Exception as e:
        logger.error(f"Error checking session: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(check_profile_session())

