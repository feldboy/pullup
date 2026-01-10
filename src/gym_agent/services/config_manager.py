"""
System Configuration Service.
Handles dynamic loading/saving of global settings like System Prompts.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from gym_agent.services.database import get_database, DatabaseService

class SystemConfig(BaseModel):
    """Model for dynamic system configuration."""
    key: str = Field(..., description="Unique key for the config, e.g., 'system_prompt'")
    value: str = Field(..., description="Configuration value")
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str = Field(default="system")

class ConfigManager:
    """Service to manage system configurations."""
    
    COLLECTION = "system_config"
    
    def __init__(self, db: DatabaseService):
        self.db = db
        
    async def get_config(self, key: str, default: Optional[str] = None) -> str:
        """Get a config value by key, returning default if not found."""
        try:
            doc = await self.db.db[self.COLLECTION].find_one({"key": key})
            if doc:
                return doc["value"]
        except Exception:
            # Fallback if DB not ready or collection missing
            pass
            
        return default or ""

    async def set_config(self, key: str, value: str, user: str = "admin") -> None:
        """Set a config value."""
        await self.db.db[self.COLLECTION].update_one(
            {"key": key},
            {"$set": {
                "value": value,
                "updated_at": datetime.utcnow(),
                "updated_by": user
            }},
            upsert=True
        )

# Global instance pattern
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """Get singleton config manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(get_database())
    return _config_manager
