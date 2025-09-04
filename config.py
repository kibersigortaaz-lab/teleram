import os
from dataclasses import dataclass

@dataclass
class Config:
    # Bot Configuration
    BOT_TOKEN: str = "8492122796:AAHTB3-EVBPWtLOdjo2aJXOxcqm18K3jkkM"
    LOG_CHANNEL_ID: int = -1002939137169
    OWNER_ID: int = 7121280299
    
    # API Keys
    IPINFO_TOKEN: str = "7e5ce118942708"
    
    # Domain Configuration
    DOMAIN: str = "takipciaz.com"
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///bot_data.db")
    
    # Web Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = int(os.getenv("PORT", 8000))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        return cls(
            BOT_TOKEN=os.getenv("BOT_TOKEN", cls.BOT_TOKEN),
            LOG_CHANNEL_ID=int(os.getenv("LOG_CHANNEL_ID", cls.LOG_CHANNEL_ID)),
            OWNER_ID=int(os.getenv("OWNER_ID", cls.OWNER_ID)),
            IPINFO_TOKEN=os.getenv("IPINFO_TOKEN", cls.IPINFO_TOKEN),
            DOMAIN=os.getenv("DOMAIN", cls.DOMAIN),
            DATABASE_URL=os.getenv("DATABASE_URL", cls.DATABASE_URL),
            HOST=os.getenv("HOST", cls.HOST),
            PORT=int(os.getenv("PORT", cls.PORT)),
            SECRET_KEY=os.getenv("SECRET_KEY", cls.SECRET_KEY)
        )
