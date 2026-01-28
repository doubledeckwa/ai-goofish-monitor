"""
Feature Toggle Management System
Provides dynamic feature control with rollout management
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import hashlib
import os
from pydantic import BaseModel

class FeatureToggle(str, Enum):
    """Feature toggle enumeration"""
    # User Management
    USER_REGISTRATION = "user_registration"
    USER_LOGIN = "user_login"
    USER_SESSIONS = "user_sessions"
    
    # AI Features
    AI_ANALYSIS = "ai_analysis"
    AI_IMAGE_ANALYSIS = "ai_image_analysis"
    AI_ENHANCED_FILTERING = "ai_enhanced_filtering"
    
    # Scraper Features
    ADVANCED_BLOCKING = "advanced_blocking"
    DYNAMIC_ROTATION = "dynamic_rotation"
    BEHAVIORAL_SIMULATION = "behavioral_simulation"
    
    # Marketplace Features
    PUBLIC_MARKETPLACE = "public_marketplace"
    FAVORITES_SYSTEM = "favorites_system"
    REAL_TIME_NOTIFICATIONS = "real_time_notifications"

@dataclass
class FeatureConfig:
    """Feature configuration"""
    enabled: bool = False
    rollout_percentage: float = 0.0  # 0.0 - 1.0
    whitelist_users: List[int] = None
    blacklist_users: List[int] = None
    description: str = ""
    depends_on: List[FeatureToggle] = None
    
    def __post_init__(self):
        if self.whitelist_users is None:
            self.whitelist_users = []
        if self.blacklist_users is None:
            self.blacklist_users = []
        if self.depends_on is None:
            self.depends_on = []

class FeatureToggleManager:
    """Central feature toggle management"""
    
    def __init__(self):
        self.features: Dict[FeatureToggle, FeatureConfig] = {}
        self._load_default_configuration()
    
    def _load_default_configuration(self):
        """Load default feature configuration from environment"""
        # User Management
        self.features[FeatureToggle.USER_REGISTRATION] = FeatureConfig(
            enabled=self._get_env_bool("ENABLE_USER_REGISTRATION", True),
            description="User registration functionality"
        )
        
        self.features[FeatureToggle.USER_LOGIN] = FeatureConfig(
            enabled=self._get_env_bool("ENABLE_USER_LOGIN", True),
            description="User authentication functionality"
        )
        
        # AI Features
        self.features[FeatureToggle.AI_ANALYSIS] = FeatureConfig(
            enabled=self._get_env_bool("ENABLE_AI_ANALYSIS", True),
            description="AI-powered product analysis"
        )
        
        self.features[FeatureToggle.AI_IMAGE_ANALYSIS] = FeatureConfig(
            enabled=self._get_env_bool("ENABLE_AI_IMAGE_ANALYSIS", True),
            description="AI analysis of product images"
        )
        
        # Scraper Features
        self.features[FeatureToggle.ADVANCED_BLOCKING] = FeatureConfig(
            enabled=self._get_env_bool("ENABLE_ADVANCED_BLOCKING", False),
            description="Enhanced anti-blocking mechanisms"
        )
        
        # Marketplace Features
        self.features[FeatureToggle.PUBLIC_MARKETPLACE] = FeatureConfig(
            enabled=self._get_env_bool("ENABLE_PUBLIC_MARKETPLACE", True),
            description="Public marketplace access"
        )
        
        self.features[FeatureToggle.FAVORITES_SYSTEM] = FeatureConfig(
            enabled=self._get_env_bool("ENABLE_FAVORITES_SYSTEM", True),
            description="User favorites functionality"
        )
    
    def _get_env_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable"""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on", "enabled")
    
    def is_enabled(self, feature: FeatureToggle, user_id: Optional[int] = None) -> bool:
        """Check if feature is enabled for user"""
        config = self.features.get(feature)
        if not config or not config.enabled:
            return False
        
        # Check user whitelist/blacklist
        if user_id:
            if user_id in config.blacklist_users:
                return False
            if config.whitelist_users and user_id not in config.whitelist_users:
                return False
        
        # Check dependencies
        for dep in config.depends_on:
            if not self.is_enabled(dep, user_id):
                return False
        
        # Rollout percentage logic
        if config.rollout_percentage < 1.0 and user_id:
            user_hash = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16)
            return (user_hash % 100) / 100.0 < config.rollout_percentage
        
        return True
    
    def get_feature_status(self) -> Dict[str, Dict[str, Any]]:
        """Get all feature statuses for API"""
        return {
            feature.value: {
                "enabled": config.enabled,
                "rollout_percentage": config.rollout_percentage,
                "description": config.description,
                "whitelist_users": len(config.whitelist_users),
                "blacklist_users": len(config.blacklist_users),
                "depends_on": [dep.value for dep in config.depends_on]
            }
            for feature, config in self.features.items()
        }

# Global instance
feature_toggle_manager = FeatureToggleManager()