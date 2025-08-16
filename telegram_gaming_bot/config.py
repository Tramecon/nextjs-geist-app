import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///gaming_bot.db')
    
    # Cryptocurrency API Configuration
    COINBASE_API_KEY = os.getenv('COINBASE_API_KEY')
    COINBASE_WEBHOOK_SECRET = os.getenv('COINBASE_WEBHOOK_SECRET')
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
    
    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    
    # Security
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default_jwt_secret_change_in_production')
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'default_encryption_key_change_in_production')
    
    # Game Configuration
    SUPPORTED_CRYPTOS = os.getenv('SUPPORTED_CRYPTOS', 'BTC,ETH,USDT,USDC').split(',')
    MIN_BET_AMOUNT = float(os.getenv('MIN_BET_AMOUNT', '1.0'))
    MAX_BET_AMOUNT = float(os.getenv('MAX_BET_AMOUNT', '1000.0'))
    
    # Game Settings
    GAME_TIMEOUT = 300  # 5 minutes
    INVITATION_TIMEOUT = 60  # 1 minute
    
    # Crypto API URLs
    COINBASE_API_URL = "https://api.commerce.coinbase.com"
    BINANCE_API_URL = "https://api.binance.com"
    
    @classmethod
    def validate_config(cls):
        """Validate that required configuration is present"""
        required_vars = [
            'TELEGRAM_BOT_TOKEN'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True

# Validate configuration on import
Config.validate_config()
