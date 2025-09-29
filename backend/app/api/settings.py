from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger

from app.core.auth import require_auth
from app.core.sending_policy import SENDING_POLICY
from app.schemas.common import DataResponse
from app.schemas.settings import SettingsOut, SettingsUpdate, SettingsResponse
from app.schemas.inbox import MailAccountOut, MailAccountUpsert, MailAccountTestResponseWrapped
from app.services.settings import settings_service
from app.services.inbox.accounts import MailAccountService

router = APIRouter(tags=["settings"])

# Initialize IMAP accounts service
imap_accounts_service = MailAccountService()




@router.get("", response_model=DataResponse[SettingsOut])
async def get_settings(user: Dict[str, Any] = Depends(require_auth)):
    """Get current settings configuration with hard-coded sending policy"""
    try:
        logger.info("settings_viewed", user_id=user.get("sub", "unknown"))
        
        # Get base settings (editable fields only)
        settings = settings_service.get_settings()
        
        # Add hard-coded sending policy
        settings_dict = settings.model_dump()
        settings_dict.update({
            "timezone": SENDING_POLICY.timezone,
            "window": {
                "days": SENDING_POLICY.days,
                "from": SENDING_POLICY.window_from,
                "to": SENDING_POLICY.window_to,
                "editable": False
            },
            "throttle": {
                "emailsPer": 1,
                "minutes": SENDING_POLICY.slot_every_minutes,
                "editable": False
            },
            "timezoneEditable": False,
            "dailyCapPerDomain": SENDING_POLICY.daily_cap_per_domain,
            "gracePeriodTo": SENDING_POLICY.grace_to
        })
        
        return DataResponse(data=settings_dict, error=None)
        
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("", response_model=DataResponse[SettingsOut])
async def update_settings(
    updates: SettingsUpdate,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Update settings (only non-sending policy fields allowed)"""
    try:
        logger.info("settings_update_attempt", user_id=user.get("sub", "unknown"), updates=updates.model_dump(exclude_none=True))
        
        # Check for sending policy fields - these are forbidden
        update_dict = updates.model_dump(exclude_none=True)
        sending_policy_fields = {
            "timezone", "sending_window_start", "sending_window_end", 
            "sending_days", "throttle_minutes", "window", "throttle"
        }
        
        forbidden_fields = set(update_dict.keys()) & sending_policy_fields
        if forbidden_fields:
            logger.warning(f"Attempt to update sending policy fields: {forbidden_fields}")
            raise HTTPException(
                status_code=405,
                detail={"error": "settings_hard_coded"}
            )
        
        # Only allow editable fields
        allowed_fields = {"unsubscribe_text", "tracking_pixel_enabled", "unsubscribeText", "trackingPixelEnabled"}
        invalid_fields = set(update_dict.keys()) - allowed_fields
        if invalid_fields:
            logger.warning(f"Attempt to update invalid fields: {invalid_fields}")
            raise HTTPException(
                status_code=400,
                detail={"error": "invalid_payload"}
            )
        
        # Validate unsubscribe text if provided
        unsubscribe_text = updates.unsubscribe_text
        if unsubscribe_text is not None:
            if not settings_service.validate_unsubscribe_text(unsubscribe_text):
                raise HTTPException(
                    status_code=422,
                    detail={"error": "invalid_payload"}
                )
        
        # Update settings
        updated_settings = settings_service.update_settings(updates)
        
        logger.info("settings_updated", user_id=user.get("sub", "unknown"))
        return DataResponse(data=updated_settings, error=None)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("")
async def put_settings_forbidden():
    """PUT method not allowed for settings"""
    raise HTTPException(
        status_code=405,
        detail={"error": "settings_hard_coded"}
    )


@router.patch("")
async def patch_settings_forbidden():
    """PATCH method not allowed for settings"""
    raise HTTPException(
        status_code=405,
        detail={"error": "settings_hard_coded"}
    )


# IMAP Account Management Endpoints

@router.get("/inbox/accounts", response_model=DataResponse[List[MailAccountOut]])
async def get_imap_accounts(user: Dict[str, Any] = Depends(require_auth)):
    """Get all IMAP accounts with masked usernames"""
    try:
        accounts = imap_accounts_service.get_all_accounts()
        return DataResponse(data=accounts, error=None)
    except Exception as e:
        logger.error(f"Error getting IMAP accounts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve IMAP accounts")


@router.post("/inbox/accounts", response_model=DataResponse[MailAccountOut])
async def create_imap_account(
    account_data: MailAccountUpsert,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Create or update IMAP account (without plain password)"""
    try:
        account = imap_accounts_service.create_account(account_data.model_dump())
        
        # Mask username for response
        account['username_masked'] = imap_accounts_service.store.mask_username(account['username'])
        
        logger.info(f"IMAP account created: {account['label']}")
        return DataResponse(data=account, error=None)
    except Exception as e:
        logger.error(f"Error creating IMAP account: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create IMAP account")


@router.post("/inbox/accounts/{account_id}/test", response_model=MailAccountTestResponseWrapped)
async def test_imap_account(
    account_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Test IMAP account connection"""
    try:
        result = imap_accounts_service.test_account(account_id)
        return DataResponse(data=result, error=None)
    except Exception as e:
        logger.error(f"Error testing IMAP account {account_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to test IMAP account")


@router.post("/inbox/accounts/{account_id}/toggle", response_model=DataResponse[MailAccountOut])
async def toggle_imap_account(
    account_id: str,
    user: Dict[str, Any] = Depends(require_auth)
):
    """Toggle IMAP account active status"""
    try:
        account = imap_accounts_service.toggle_account(account_id)
        
        if not account:
            raise HTTPException(status_code=404, detail="IMAP account not found")
        
        # Mask username for response
        account['username_masked'] = imap_accounts_service.store.mask_username(account['username'])
        
        status = "activated" if account['active'] else "deactivated"
        logger.info(f"IMAP account {status}: {account['label']}")
        
        return DataResponse(data=account, error=None)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling IMAP account {account_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to toggle IMAP account")
