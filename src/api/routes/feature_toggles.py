"""
Feature Toggle Management API
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from src.infrastructure.config.feature_toggles import feature_toggle_manager, FeatureToggle
from src.services.user_service import UserService
from src.domain.models.user import User
from src.api.dependencies import get_current_user

router = APIRouter(prefix="/api/admin/features", tags=["feature-toggles"])

@router.get("/status")
async def get_feature_status(current_user: User = Depends(get_current_user)):
    """Get all feature toggle statuses"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return feature_toggle_manager.get_feature_status()

@router.get("/check/{feature}")
async def check_feature(
    feature: str, 
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """Check if feature is enabled"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        feature_enum = FeatureToggle(feature)
        enabled = feature_toggle_manager.is_enabled(feature_enum, user_id)
        return {"feature": feature, "enabled": enabled, "user_id": user_id}
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Feature {feature} not found")