import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import secrets

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with the given name"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Create console handler if not already exists
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def validate_username(username: str) -> Dict[str, Any]:
    """Validate username format and return result"""
    if not username:
        return {"valid": False, "message": "Username cannot be empty"}
    
    if len(username) < 3:
        return {"valid": False, "message": "Username must be at least 3 characters"}
    
    if len(username) > 20:
        return {"valid": False, "message": "Username must be no more than 20 characters"}
    
    # Only allow letters, numbers, and underscores
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return {"valid": False, "message": "Username can only contain letters, numbers, and underscores"}
    
    return {"valid": True, "message": "Username is valid"}

def validate_email(email: str) -> Dict[str, Any]:
    """Validate email format and return result"""
    if not email:
        return {"valid": False, "message": "Email cannot be empty"}
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return {"valid": False, "message": "Invalid email format"}
    
    if len(email) > 255:
        return {"valid": False, "message": "Email is too long"}
    
    return {"valid": True, "message": "Email is valid"}

def validate_bet_amount(amount: float, min_amount: float, max_amount: float) -> Dict[str, Any]:
    """Validate bet amount and return result"""
    if amount < min_amount:
        return {"valid": False, "message": f"Minimum bet amount is ${min_amount}"}
    
    if amount > max_amount:
        return {"valid": False, "message": f"Maximum bet amount is ${max_amount}"}
    
    # Check for reasonable decimal places (max 2)
    if round(amount, 2) != amount:
        return {"valid": False, "message": "Amount can have at most 2 decimal places"}
    
    return {"valid": True, "message": "Bet amount is valid"}

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\';\\]', '', text)
    
    # Limit length
    sanitized = sanitized[:1000]
    
    # Strip whitespace
    sanitized = sanitized.strip()
    
    return sanitized

def format_currency(amount: float) -> str:
    """Format currency amount for display"""
    return f"${amount:.2f}"

def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

def format_game_duration(start_time: datetime, end_time: Optional[datetime] = None) -> str:
    """Format game duration for display"""
    if not end_time:
        end_time = datetime.utcnow()
    
    duration = end_time - start_time
    
    total_seconds = int(duration.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def generate_session_id() -> str:
    """Generate a unique session ID"""
    timestamp = str(int(datetime.utcnow().timestamp()))
    random_part = secrets.token_hex(8)
    return f"game_{timestamp}_{random_part}"

def hash_password(password: str) -> str:
    """Hash a password using SHA-256 (for demo purposes)"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == hashed

def create_error_response(message: str, code: str = "ERROR") -> Dict[str, Any]:
    """Create a standardized error response"""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
    }

def create_success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Create a standardized success response"""
    response = {
        "success": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    return response

def format_leaderboard(users: list, title: str = "Leaderboard") -> str:
    """Format a leaderboard for display"""
    if not users:
        return f"📊 {title}\n\nNo data available."
    
    message = f"📊 {title}\n\n"
    
    for i, user in enumerate(users[:10], 1):  # Top 10
        if i == 1:
            emoji = "🥇"
        elif i == 2:
            emoji = "🥈"
        elif i == 3:
            emoji = "🥉"
        else:
            emoji = f"{i}."
        
        win_rate = 0
        if hasattr(user, 'total_games_played') and user.total_games_played > 0:
            win_rate = (user.total_games_won / user.total_games_played) * 100
        
        message += f"{emoji} {user.username}\n"
        message += f"   🏆 {user.total_games_won} wins ({win_rate:.1f}%)\n"
        message += f"   💰 ${user.total_winnings:.2f} earned\n\n"
    
    return message

def format_transaction_history(transactions: list) -> str:
    """Format transaction history for display"""
    if not transactions:
        return "💳 Transaction History\n\nNo transactions found."
    
    message = "💳 Recent Transactions\n\n"
    
    for tx in transactions:
        # Format transaction type
        tx_type = tx.transaction_type.value.replace('_', ' ').title()
        
        # Format amount with + or - prefix
        if tx.amount > 0:
            amount_str = f"+${tx.amount:.2f}"
            emoji = "💰"
        else:
            amount_str = f"-${abs(tx.amount):.2f}"
            emoji = "💸"
        
        # Format date
        date_str = tx.timestamp.strftime("%m/%d %H:%M")
        
        message += f"{emoji} {amount_str} - {tx_type}\n"
        message += f"   📅 {date_str}\n"
        
        if tx.description:
            # Truncate long descriptions
            desc = tx.description[:50] + "..." if len(tx.description) > 50 else tx.description
            message += f"   📝 {desc}\n"
        
        message += "\n"
    
    return message

def format_game_stats(user) -> str:
    """Format user game statistics for display"""
    message = f"📊 Game Statistics for {user.username}\n\n"
    
    message += f"🎮 Games Played: {user.total_games_played}\n"
    message += f"🏆 Games Won: {user.total_games_won}\n"
    
    if user.total_games_played > 0:
        win_rate = (user.total_games_won / user.total_games_played) * 100
        message += f"📈 Win Rate: {win_rate:.1f}%\n"
    else:
        message += f"📈 Win Rate: 0.0%\n"
    
    message += f"💰 Total Winnings: ${user.total_winnings:.2f}\n"
    message += f"💳 Current Balance: ${user.balance:.2f}\n"
    message += f"📅 Member Since: {user.registration_date.strftime('%Y-%m-%d')}\n"
    
    return message

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def escape_markdown(text: str) -> str:
    """Escape special characters for Telegram markdown"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def format_help_message() -> str:
    """Format the help message with all available commands"""
    help_text = """
🎮 **Crypto Gaming Bot - Help**

**👤 Account Commands:**
/start - Start the bot and register
/register - Manual registration
/profile - View your profile and stats
/balance - Check your current balance

**💰 Crypto Commands:**
/deposit <amount> - Deposit cryptocurrency
/withdraw <amount> <address> - Withdraw crypto
/transactions - View transaction history

**🎮 Game Commands:**
/games - List available games
/play - Start/resume active games
/status - Check current game status
/challenge <username> <game> <amount> - Challenge a player
/search <username> - Search for players
/accept - Accept game invitations
/decline - Decline game invitations

**🎯 Game Controls:**
*Tetris:* /left, /right, /down, /rotate, /drop
*Snake:* /up, /down, /left, /right, /tick
*Ping Pong:* /up, /down, /tick

**📊 Other Commands:**
/help - Show this help message
/leaderboard - View top players

**💡 Tips:**
• Minimum bet: $1.00
• Maximum bet: $1000.00
• Winner takes all the bet money!
• Games have time limits
• Use /status to check your current game
"""
    return help_text

class MessageFormatter:
    """Helper class for formatting Telegram messages"""
    
    @staticmethod
    def bold(text: str) -> str:
        """Make text bold"""
        return f"**{text}**"
    
    @staticmethod
    def italic(text: str) -> str:
        """Make text italic"""
        return f"*{text}*"
    
    @staticmethod
    def code(text: str) -> str:
        """Format text as code"""
        return f"`{text}`"
    
    @staticmethod
    def code_block(text: str, language: str = "") -> str:
        """Format text as code block"""
        return f"```{language}\n{text}\n```"
    
    @staticmethod
    def link(text: str, url: str) -> str:
        """Create a link"""
        return f"[{text}]({url})"

# Global logger instance
logger = setup_logger(__name__)
