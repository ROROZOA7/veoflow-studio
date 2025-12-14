#!/usr/bin/env python3
"""
Test profile API endpoints to verify profile loading works
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.api.setup import get_profile, get_login_status, list_profiles
from app.services.profile_manager import ProfileManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_profile_api():
    """Test profile API endpoints"""
    try:
        logger.info("=" * 80)
        logger.info("PROFILE API TEST")
        logger.info("=" * 80)
        
        # Get active profile
        profile_manager = ProfileManager()
        active_profile = profile_manager.get_active_profile()
        
        if not active_profile:
            logger.error("✗ No active profile found!")
            return False
        
        logger.info(f"\n[TEST 1] Testing list_profiles()...")
        try:
            result = await list_profiles()
            if result.get("success"):
                profiles = result.get("profiles", [])
                logger.info(f"✓ List profiles: Found {len(profiles)} profiles")
                for p in profiles:
                    logger.info(f"  - {p.get('name')} (active: {p.get('is_active', False)})")
            else:
                logger.error("✗ List profiles failed")
                return False
        except Exception as e:
            logger.error(f"✗ List profiles error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        
        logger.info(f"\n[TEST 2] Testing get_profile({active_profile.id})...")
        try:
            result = await get_profile(active_profile.id)
            if result.get("success"):
                profile = result.get("profile", {})
                logger.info(f"✓ Get profile: {profile.get('name')}")
                
                # Check profile validation
                profile_valid = profile.get("profile_valid", False)
                has_cookies = profile.get("has_cookies", False)
                cookie_size = profile.get("cookie_file_size", 0)
                login_status = profile.get("login_status", {})
                
                logger.info(f"  Profile valid: {profile_valid}")
                logger.info(f"  Has cookies: {has_cookies} ({cookie_size} bytes)")
                logger.info(f"  Login status: {login_status.get('status', 'unknown')}")
                
                if login_status.get("flow_logged_in"):
                    logger.info(f"  ✓ Flow logged in: {login_status.get('cookies_count', 0)} cookies")
                elif login_status.get("error"):
                    logger.warning(f"  ⚠ Login check error: {login_status.get('error')}")
                else:
                    logger.warning(f"  ⚠ Flow not logged in")
                
                if not profile_valid or not has_cookies:
                    logger.error("✗ Profile validation failed!")
                    return False
            else:
                logger.error("✗ Get profile failed")
                return False
        except Exception as e:
            logger.error(f"✗ Get profile error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        
        logger.info(f"\n[TEST 3] Testing get_login_status({active_profile.id})...")
        try:
            result = await get_login_status(active_profile.id)
            if result.get("success"):
                flow_logged_in = result.get("flow_logged_in", False)
                cookies_count = result.get("cookies_count", 0)
                google_cookies = result.get("google_cookies_count", 0)
                
                logger.info(f"✓ Login status check:")
                logger.info(f"  Flow logged in: {flow_logged_in}")
                logger.info(f"  Total cookies: {cookies_count}")
                logger.info(f"  Google cookies: {google_cookies}")
                
                if flow_logged_in:
                    logger.info("  ✓ Profile is logged in and working correctly!")
                else:
                    error = result.get("error")
                    if error:
                        logger.warning(f"  ⚠ Not logged in: {error}")
                    else:
                        logger.warning("  ⚠ Not logged in (no error message)")
            else:
                logger.error("✗ Login status check failed")
                return False
        except Exception as e:
            logger.error(f"✗ Login status error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        
        logger.info("\n" + "=" * 80)
        logger.info("✓ ALL PROFILE API TESTS PASSED")
        logger.info("=" * 80)
        return True
        
    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = asyncio.run(test_profile_api())
    sys.exit(0 if success else 1)

