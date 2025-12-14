#!/usr/bin/env python3
"""
Test script to verify Google account popup error detection and ULTRA badge verification
"""
import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.profile_manager import ProfileManager
from app.services.browser_manager import BrowserManager
from app.services.flow_controller import FlowController

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_error_detection():
    """Test Google account popup error detection and ULTRA badge verification"""
    logger.info("=" * 80)
    logger.info("TESTING ERROR DETECTION AND ULTRA BADGE VERIFICATION")
    logger.info("=" * 80)
    
    # Check active profile
    logger.info("\n[STEP 1] Checking active profile...")
    profile_manager = ProfileManager()
    active_profile = profile_manager.get_active_profile()
    if not active_profile:
        logger.error("✗ No active profile found. Please set one using the API or setup_chrome_profile.sh")
        return False
    logger.info(f"✓ Active profile: {active_profile.name} ({active_profile.id})")
    logger.info(f"✓ Profile path: {active_profile.profile_path}")
    
    # Initialize browser
    logger.info("\n[STEP 2] Initializing browser with active profile...")
    browser_manager = BrowserManager()
    try:
        from pathlib import Path
        profile_path = Path(active_profile.profile_path)
        await browser_manager.initialize_with_profile_path(profile_path)
        logger.info("✓ Browser initialized successfully")
    except Exception as e:
        logger.error(f"✗ Failed to initialize browser: {e}")
        return False
    
    # Create page and flow controller
    logger.info("\n[STEP 3] Creating page and flow controller...")
    page = None
    try:
        page = await browser_manager.new_page()
        flow_controller = FlowController(browser_manager)
        logger.info("✓ Page and flow controller created")
    except Exception as e:
        logger.error(f"✗ Failed to create page/controller: {e}")
        await browser_manager.close()
        return False
    
    # Test navigation and error detection
    logger.info("\n[STEP 4] Testing navigation to Flow and error detection...")
    logger.info("This will test:")
    logger.info("  1. Google account popup error detection")
    logger.info("  2. ULTRA badge verification")
    logger.info("  3. Enhanced error detection in wait_for_completion")
    
    try:
        # Navigate to Flow - this should detect any Google account popup errors
        await flow_controller.navigate_to_flow(page)
        logger.info("✓ Navigation completed successfully")
        
        # Check current URL
        current_url = page.url
        logger.info(f"Current URL: {current_url}")
        
        # Check if we're on Flow page
        if "labs.google" in current_url and ("flow" in current_url or "/fx/" in current_url):
            logger.info("✓ Successfully on Flow page")
            
            # Take a screenshot to verify page state
            try:
                from app.services.flow_controller import get_screenshot_path
                from datetime import datetime
                screenshot_path = get_screenshot_path(f"test_error_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"✓ Screenshot saved to {screenshot_path}")
            except Exception as e:
                logger.warning(f"Could not take screenshot: {e}")
            
            # Check for ULTRA badge
            logger.info("\n[STEP 5] Checking for ULTRA badge...")
            ultra_selectors = [
                'text=ULTRA',
                '[class*="ultra"]',
                '[class*="Ultra"]',
                '[aria-label*="ULTRA"]',
                'div:has-text("ULTRA")',
            ]
            
            has_ultra = False
            for selector in ultra_selectors:
                try:
                    ultra_elem = page.locator(selector).first
                    if await ultra_elem.count() > 0 and await ultra_elem.is_visible():
                        ultra_text = await ultra_elem.text_content() or ""
                        if "ULTRA" in ultra_text.upper():
                            has_ultra = True
                            logger.info(f"✓ ULTRA badge found: {ultra_text[:50]}")
                            break
                except:
                    continue
            
            if not has_ultra:
                logger.warning("⚠ ULTRA badge not found - account may not have ULTRA subscription")
            
            # Check for Google account popup errors
            logger.info("\n[STEP 6] Checking for Google account popup errors...")
            google_error_selectors = [
                'text=Rất tiếc, đã xảy ra lỗi!',
                'text=Unfortunately, an error occurred!',
                '[role="dialog"]:has-text("Rất tiếc")',
                '[role="alertdialog"]:has-text("Rất tiếc")',
            ]
            
            has_error = False
            for selector in google_error_selectors:
                try:
                    error_elem = page.locator(selector).first
                    if await error_elem.count() > 0 and await error_elem.is_visible():
                        error_text = await error_elem.text_content() or ""
                        if error_text:
                            has_error = True
                            logger.error(f"✗ Google account popup error detected: {error_text[:200]}")
                            break
                except:
                    continue
            
            if not has_error:
                logger.info("✓ No Google account popup errors detected")
            
            logger.info("\n" + "=" * 80)
            logger.info("TEST SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Navigation: ✓ Success")
            logger.info(f"ULTRA Badge: {'✓ Found' if has_ultra else '⚠ Not found'}")
            logger.info(f"Google Account Errors: {'✗ Detected' if has_error else '✓ None detected'}")
            logger.info("=" * 80)
            
            return True
            
        else:
            logger.warning(f"⚠ Not on Flow page - current URL: {current_url}")
            return False
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"✗ Error during navigation/test: {error_msg}")
        
        # Check if it's a Google account error (which is what we're testing for)
        if "Google account error" in error_msg or "Rất tiếc" in error_msg:
            logger.info("✓ Google account error was correctly detected and reported!")
            return True  # This is actually a success - error detection worked
        
        # Take screenshot on error
        try:
            from app.services.flow_controller import get_screenshot_path
            from datetime import datetime
            screenshot_path = get_screenshot_path(f"test_error_detection_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            logger.error(f"Error screenshot saved to {screenshot_path}")
        except:
            pass
        
        return False
        
    finally:
        # Cleanup
        if page:
            try:
                await page.close()
            except:
                pass
        try:
            await browser_manager.close()
        except:
            pass


if __name__ == "__main__":
    try:
        success = asyncio.run(test_error_detection())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

