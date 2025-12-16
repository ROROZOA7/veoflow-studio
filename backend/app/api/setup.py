"""
Setup API endpoints - For Google Flow login and browser profile setup
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import asyncio
import logging
from pathlib import Path
from shutil import copytree
from app.services.browser_manager import BrowserManager
from app.services.flow_controller import FlowController
from app.services.profile_manager import ProfileManager
from app.services.guided_login import GuidedLoginService
from app.core.database import SessionLocal
from app.config import config_manager, settings, IMAGES_PATH

logger = logging.getLogger(__name__)
router = APIRouter()

# Global guided login service instance
guided_login_service = GuidedLoginService()


class SetupStatusResponse(BaseModel):
    """Response model for setup status"""
    chrome_profile_exists: bool
    chrome_profile_path: str
    is_logged_in: Optional[bool] = None
    login_test_error: Optional[str] = None
    needs_setup: bool


class TestConnectionResponse(BaseModel):
    """Response model for connection test"""
    success: bool
    message: str
    is_logged_in: bool
    screenshot_path: Optional[str] = None


@router.get("/status")
async def get_setup_status() -> SetupStatusResponse:
    """
    Get current setup status:
    - Chrome profile exists?
    - Is user logged in to Google Flow?
    - What needs to be configured?
    """
    chrome_profile_path = config_manager.get(
        "browser.chromeProfilePath",
        settings.CHROME_PROFILE_PATH
    )
    profile_path = Path(chrome_profile_path)
    profile_exists = profile_path.exists() and any(profile_path.iterdir())
    
    # Try to check login status (non-blocking quick check)
    is_logged_in = None
    login_test_error = None
    
    if profile_exists:
        try:
            # FIX: Use a cloned copy of the active profile to avoid conflicts with render workers
            profile_manager = ProfileManager()
            active_profile = profile_manager.get_active_profile()
            
            if active_profile:
                # Use active profile path as base
                base_profile_path = Path(active_profile.profile_path)
                logger.info(f"Checking login status with active profile: {active_profile.name} ({base_profile_path})")
                
                # Clone active profile into a setup-specific directory to avoid interfering
                # with render workers or other browser sessions
                worker_profiles_root = profile_manager.profiles_dir / "worker_profiles"
                worker_profiles_root.mkdir(parents=True, exist_ok=True)
                setup_profile_path = worker_profiles_root / f"{active_profile.id}_setup_status"
                
                if not setup_profile_path.exists():
                    logger.info(f"Creating setup-specific profile by copying active profile to: {setup_profile_path}")
                    try:
                        copytree(base_profile_path, setup_profile_path, dirs_exist_ok=True)
                    except TypeError:
                        # Older Python fallback without dirs_exist_ok
                        try:
                            copytree(base_profile_path, setup_profile_path)
                        except FileExistsError:
                            logger.info(f"Setup profile already exists: {setup_profile_path}")
                    except Exception as copy_error:
                        logger.warning(f"Could not clone active profile for setup status: {copy_error}")
                        # Fallback: use base profile directly (may have more conflicts)
                        setup_profile_path = base_profile_path
                
                browser_manager = BrowserManager()
                await browser_manager.initialize_with_profile_path(setup_profile_path)
                page = await browser_manager.new_page()
            else:
                # Fallback to default initialization
                logger.warning("No active profile found, using default initialization")
                browser_manager = BrowserManager()
                await browser_manager.initialize()
                page = await browser_manager.new_page()
            
            try:
                flow_controller = FlowController(browser_manager)
                await flow_controller.navigate_to_flow(page)
                
                # Check if we're logged in (look for prompt input or login button)
                login_text = await page.locator('text=Sign in').count()
                login_google = await page.locator('text=Sign in with Google').count()
                login_link = await page.locator('a[href*="accounts.google.com"]').count()
                login_indicators = login_text + login_google + login_link
                
                prompt_inputs = await page.locator(
                    'textarea, [contenteditable], [role="textbox"]'
                ).count()
                
                is_logged_in = prompt_inputs > 0 and login_indicators == 0
                
                logger.info(f"Login status check: is_logged_in={is_logged_in}, prompt_inputs={prompt_inputs}, login_indicators={login_indicators}")
                
            except Exception as e:
                logger.warning(f"Login check failed: {e}", exc_info=True)
                login_test_error = str(e)
            finally:
                try:
                    await page.close()
                except:
                    pass
                try:
                    await browser_manager.close()
                except:
                    pass
                
        except Exception as e:
            logger.error(f"Failed to check login status: {e}", exc_info=True)
            login_test_error = str(e)
    
    needs_setup = not profile_exists or is_logged_in is False
    
    return SetupStatusResponse(
        chrome_profile_exists=profile_exists,
        chrome_profile_path=str(profile_path.absolute()),
        is_logged_in=is_logged_in,
        login_test_error=login_test_error,
        needs_setup=needs_setup
    )


@router.post("/test-connection")
async def test_connection(background_tasks: BackgroundTasks) -> TestConnectionResponse:
    """
    Open browser window and test Google Flow connection.
    User can manually log in if needed.
    Browser stays open for user interaction.
    """
    try:
        # FIX: Use active profile path directly
        profile_manager = ProfileManager()
        active_profile = profile_manager.get_active_profile()
        
        browser_manager = BrowserManager()
        if active_profile:
            profile_path = Path(active_profile.profile_path)
            logger.info(f"Using active profile for connection test: {active_profile.name}")
            await browser_manager.initialize_with_profile_path(profile_path)
        else:
            logger.warning("No active profile, using default initialization")
            await browser_manager.initialize()
        
        page = await browser_manager.new_page()
        
        try:
            flow_controller = FlowController(browser_manager)
            await flow_controller.navigate_to_flow(page)
            
            # Wait a bit for page to fully load
            await asyncio.sleep(3)
            
            # Check login status
            login_text = await page.locator('text=Sign in').count()
            login_google = await page.locator('text=Sign in with Google').count()
            login_link = await page.locator('a[href*="accounts.google.com"]').count()
            login_indicators = login_text + login_google + login_link
            
            prompt_inputs = await page.locator(
                'textarea, [contenteditable], [role="textbox"]'
            ).count()
            
            is_logged_in = prompt_inputs > 0 and login_indicators == 0
            
            # Take screenshot for debugging
            from datetime import datetime
            images_dir = Path(IMAGES_PATH)
            images_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = str(images_dir / f"flow_connection_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            await page.screenshot(path=screenshot_path)
            
            if is_logged_in:
                message = "✓ Successfully connected! You are logged in to Google Flow."
            else:
                message = "⚠️ Please log in to Google Flow in the browser window. The browser will stay open for you to complete login."
            
            # Don't close the page - let user interact with it
            # The page will be cleaned up when browser manager is cleaned up
            
            return TestConnectionResponse(
                success=True,
                message=message,
                is_logged_in=is_logged_in,
                screenshot_path=screenshot_path
            )
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            from datetime import datetime
            images_dir = Path(IMAGES_PATH)
            images_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = str(images_dir / f"flow_connection_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            try:
                await page.screenshot(path=screenshot_path)
            except:
                pass
            
            return TestConnectionResponse(
                success=False,
                message=f"Connection test failed: {str(e)}",
                is_logged_in=False,
                screenshot_path=screenshot_path
            )
            
    except Exception as e:
        logger.error(f"Failed to initialize browser for connection test: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to test connection: {str(e)}"
        )


@router.post("/open-browser")
async def open_browser_for_login() -> dict:
    """
    Open a browser window navigated to Google Flow for manual login.
    Browser stays open until user closes it or calls close-browser endpoint.
    """
    try:
        # FIX: Use active profile path directly
        profile_manager = ProfileManager()
        active_profile = profile_manager.get_active_profile()
        
        browser_manager = BrowserManager()
        if active_profile:
            profile_path = Path(active_profile.profile_path)
            logger.info(f"Using active profile for browser open: {active_profile.name}")
            await browser_manager.initialize_with_profile_path(profile_path)
        else:
            logger.warning("No active profile, using default initialization")
            await browser_manager.initialize()
        
        page = await browser_manager.new_page()
        
        flow_controller = FlowController(browser_manager)
        await flow_controller.navigate_to_flow(page)
        
        # Keep browser open - don't close it
        # Store page reference somewhere (in production, use a session manager)
        
        return {
            "success": True,
            "message": "Browser opened. Please log in to Google Flow. The browser will stay open.",
            "note": "After logging in, your session will be saved automatically."
        }
        
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to open browser: {str(e)}"
        )


@router.get("/chrome-profile")
async def get_chrome_profile_info() -> dict:
    """Get information about Chrome profile configuration"""
    chrome_profile_path = config_manager.get(
        "browser.chromeProfilePath",
        settings.CHROME_PROFILE_PATH
    )
    use_existing = config_manager.get("browser.useExistingProfile", False)
    existing_path = config_manager.get("browser.existingProfilePath", "")
    
    profile_path = Path(chrome_profile_path)
    exists = profile_path.exists() and any(profile_path.iterdir())
    
    return {
        "chrome_profile_path": str(profile_path.absolute()),
        "profile_exists": exists,
        "use_existing_profile": use_existing,
        "existing_profile_path": existing_path,
        "file_count": len(list(profile_path.glob("*"))) if exists else 0
    }


# Profile Management Endpoints

class CreateProfileRequest(BaseModel):
    name: str

@router.post("/profiles")
async def create_profile(request: CreateProfileRequest) -> dict:
    """Create a new Chrome profile"""
    try:
        profile_manager = ProfileManager()
        profile = profile_manager.create_profile(request.name)
        return {
            "success": True,
            "profile": profile.to_dict()
        }
    except Exception as e:
        logger.error(f"Failed to create profile: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/profiles")
async def list_profiles() -> dict:
    """List all profiles with basic status"""
    try:
        profile_manager = ProfileManager()
        profiles = profile_manager.list_profiles()
        active_profile = profile_manager.get_active_profile()
        active_profile_id = active_profile.id if active_profile else None
        
        profiles_list = []
        for p in profiles:
            profile_dict = p.to_dict()
            profile_dict["is_active"] = (p.id == active_profile_id)
            
            # Quick validation: check if profile path exists
            profile_path = Path(p.profile_path)
            default_dir = profile_path / "Default"
            cookies_file = default_dir / "Cookies"
            
            profile_dict["profile_valid"] = default_dir.exists()
            profile_dict["has_cookies"] = cookies_file.exists() if default_dir.exists() else False
            
            profiles_list.append(profile_dict)
        
        return {
            "success": True,
            "profiles": profiles_list,
            "active_profile_id": active_profile_id
        }
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{profile_id}")
async def get_profile(profile_id: str) -> dict:
    """Get profile details with login status"""
    try:
        profile_manager = ProfileManager()
        profile = profile_manager.get_profile(profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        profile_dict = profile.to_dict()
        
        # FIX: Add login status check using profile path directly (like check_session.py)
        try:
            profile_path = Path(profile.profile_path)
            
            # Quick check: verify profile structure
            default_dir = profile_path / "Default"
            cookies_file = default_dir / "Cookies"
            
            profile_dict["profile_valid"] = default_dir.exists()
            profile_dict["has_cookies"] = cookies_file.exists() if default_dir.exists() else False
            
            if cookies_file.exists():
                cookie_size = cookies_file.stat().st_size
                profile_dict["cookie_file_size"] = cookie_size
            else:
                profile_dict["cookie_file_size"] = 0
            
            # Try to check login status (non-blocking, quick check)
            try:
                browser_manager = BrowserManager()
                await browser_manager.initialize_with_profile_path(profile_path)
                page = await browser_manager.new_page()
                
                try:
                    flow_controller = FlowController(browser_manager)
                    await flow_controller.navigate_to_flow(page)
                    await asyncio.sleep(2)  # Quick wait
                    
                    # Check login status
                    from app.services.cookie_extractor import CookieExtractor
                    cookie_extractor = CookieExtractor(browser_manager)
                    flow_logged_in = await cookie_extractor.verify_login_status(page)
                    
                    cookies = await page.context.cookies()
                    google_cookies = [c for c in cookies if "google.com" in c.get("domain", "")]
                    
                    profile_dict["login_status"] = {
                        "flow_logged_in": flow_logged_in,
                        "cookies_count": len(cookies),
                        "google_cookies_count": len(google_cookies),
                        "status": "logged_in" if flow_logged_in else "not_logged_in"
                    }
                    
                except Exception as login_check_error:
                    logger.warning(f"Login status check failed: {login_check_error}")
                    profile_dict["login_status"] = {
                        "flow_logged_in": None,
                        "error": str(login_check_error),
                        "status": "check_failed"
                    }
                finally:
                    try:
                        await page.close()
                    except:
                        pass
                    try:
                        await browser_manager.close()
                    except:
                        pass
            except Exception as init_error:
                logger.warning(f"Failed to initialize browser for profile check: {init_error}")
                profile_dict["login_status"] = {
                    "flow_logged_in": None,
                    "error": str(init_error),
                    "status": "initialization_failed"
                }
        except Exception as profile_check_error:
            logger.warning(f"Profile validation failed: {profile_check_error}")
            profile_dict["login_status"] = {
                "flow_logged_in": None,
                "error": str(profile_check_error),
                "status": "validation_failed"
            }
        
        return {
            "success": True,
            "profile": profile_dict
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/profiles/{profile_id}")
async def delete_profile(profile_id: str) -> dict:
    """Delete a profile"""
    try:
        profile_manager = ProfileManager()
        
        # Close browser if open
        try:
            await guided_login_service.close_profile_browser(profile_id)
        except:
            pass
        
        profile_manager.delete_profile(profile_id)
        return {
            "success": True,
            "message": "Profile deleted successfully"
        }
    except Exception as e:
        logger.error(f"Failed to delete profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profiles/{profile_id}/set-active")
async def set_active_profile(profile_id: str) -> dict:
    """Set profile as active"""
    try:
        profile_manager = ProfileManager()
        profile_manager.set_active_profile(profile_id)
        return {
            "success": True,
            "message": "Profile set as active"
        }
    except Exception as e:
        logger.error(f"Failed to set active profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Guided Login Endpoints

@router.post("/profiles/{profile_id}/open")
async def open_profile_browser(profile_id: str) -> dict:
    """Open browser with specific profile"""
    try:
        result = await guided_login_service.open_browser_with_profile(profile_id)
        return result
    except Exception as e:
        logger.error(f"Failed to open profile browser: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profiles/{profile_id}/open-gmail")
async def open_gmail_tab(profile_id: str) -> dict:
    """Open Gmail login tab"""
    try:
        result = await guided_login_service.open_gmail_tab(profile_id)
        return result
    except Exception as e:
        logger.error(f"Failed to open Gmail tab: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profiles/{profile_id}/open-flow")
async def open_flow_tab(profile_id: str) -> dict:
    """Open Flow login tab"""
    try:
        result = await guided_login_service.open_flow_tab(profile_id)
        return result
    except Exception as e:
        logger.error(f"Failed to open Flow tab: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{profile_id}/login-status")
async def get_login_status(profile_id: str) -> dict:
    """Check login status for profile"""
    try:
        # FIX: If profile has browser open, use that. Otherwise, initialize with profile path directly
        profile_manager = ProfileManager()
        profile = profile_manager.get_profile(profile_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Check if browser is already open for this profile
        if profile_id in guided_login_service.browser_contexts:
            # Use existing browser context
            result = await guided_login_service.check_login_status(profile_id)
        else:
            # Browser not open - initialize with profile path directly (like check_session.py)
            logger.info(f"Profile browser not open, initializing with profile path: {profile.profile_path}")
            profile_path = Path(profile.profile_path)
            
            browser_manager = BrowserManager()
            await browser_manager.initialize_with_profile_path(profile_path)
            page = None
            
            try:
                # Create a page and check login status
                page = await browser_manager.new_page()
                flow_controller = FlowController(browser_manager)
                await flow_controller.navigate_to_flow(page)
                
                # Use cookie extractor to verify login status
                from app.services.cookie_extractor import CookieExtractor
                cookie_extractor = CookieExtractor(browser_manager)
                flow_logged_in = await cookie_extractor.verify_login_status(page)
                
                # Check cookies
                cookies = await page.context.cookies()
                google_cookies = [c for c in cookies if "google.com" in c.get("domain", "")]
                
                result = {
                    "gmail_logged_in": False,  # Can't check Gmail without opening it
                    "flow_logged_in": flow_logged_in,
                    "both_logged_in": flow_logged_in,
                    "cookies_count": len(cookies),
                    "google_cookies_count": len(google_cookies)
                }
                
                logger.info(f"Profile login status check: flow_logged_in={flow_logged_in}, cookies={len(cookies)}")
                
            except Exception as check_error:
                logger.error(f"Failed to check login status for profile: {check_error}", exc_info=True)
                result = {
                    "gmail_logged_in": False,
                    "flow_logged_in": False,
                    "both_logged_in": False,
                    "error": str(check_error)
                }
            finally:
                if page:
                    try:
                        await page.close()
                    except:
                        pass
                try:
                    await browser_manager.close()
                except:
                    pass
        
        return {
            "success": True,
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check login status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profiles/{profile_id}/confirm-login")
async def confirm_login(profile_id: str) -> dict:
    """Confirm login and save cookies"""
    try:
        result = await guided_login_service.confirm_login_and_save(profile_id)
        return result
    except Exception as e:
        logger.error(f"Failed to confirm login: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/profiles/{profile_id}/close")
async def close_profile_browser(profile_id: str) -> dict:
    """Close browser for profile"""
    try:
        await guided_login_service.close_profile_browser(profile_id)
        return {
            "success": True,
            "message": "Browser closed"
        }
    except Exception as e:
        logger.error(f"Failed to close browser: {e}")
        raise HTTPException(status_code=500, detail=str(e))

