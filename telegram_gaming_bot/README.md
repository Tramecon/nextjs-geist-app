# Telegram Crypto Gaming Bot

A multiplayer gaming platform on Telegram with real cryptocurrency betting. Play Tetris, Snake, and Ping Pong games against other players and win cryptocurrency!

## Features

- 🎮 **Multiplayer Games**: Tetris, Snake, Ping Pong
- 💰 **Cryptocurrency Integration**: Real crypto deposits and withdrawals
- 🔐 **User Authentication**: Manual registration or Google OAuth
- 🎯 **Matchmaking**: Search players by username and challenge them
- 💳 **Betting System**: Winner takes all wagered cryptocurrency
- 📊 **Statistics**: Track wins, losses, and earnings
- 🏆 **Leaderboards**: Compete with other players

## Supported Games

### 🧩 Tetris
- Classic block-stacking puzzle game
- Score points by clearing lines
- Real-time multiplayer competition

### 🐍 Snake
- Control your snake to eat food
- Avoid walls and other snakes
- Grow longer and score more points

### 🏓 Ping Pong
- Classic paddle ball game
- First to 11 points wins
- Real-time ball physics

## Setup Instructions

### Prerequisites
- Python 3.8+
- Telegram Bot Token (from @BotFather)
- Cryptocurrency API credentials (Coinbase Commerce or Binance)
- Google OAuth credentials (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd telegram_gaming_bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Copy `.env` file and fill in your credentials:
   ```bash
   cp .env .env.local
   ```
   
   Edit `.env.local` with your actual values:
   ```env
   # Required
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   
   # Cryptocurrency API (choose one)
   COINBASE_API_KEY=your_coinbase_api_key_here
   COINBASE_WEBHOOK_SECRET=your_coinbase_webhook_secret_here
   
   # OR
   BINANCE_API_KEY=your_binance_api_key_here
   BINANCE_SECRET_KEY=your_binance_secret_key_here
   
   # Optional
   GOOGLE_CLIENT_ID=your_google_client_id_here
   GOOGLE_CLIENT_SECRET=your_google_client_secret_here
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

## Getting API Credentials

### Telegram Bot Token
1. Message @BotFather on Telegram
2. Create a new bot with `/newbot`
3. Follow the instructions to get your bot token
4. Add the token to your `.env` file

### Coinbase Commerce API
1. Sign up at [Coinbase Commerce](https://commerce.coinbase.com/)
2. Go to Settings > API Keys
3. Create a new API key
4. Add the API key and webhook secret to your `.env` file

### Google OAuth (Optional)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add the client ID and secret to your `.env` file

## Bot Commands

### Account Commands
- `/start` - Start the bot and register
- `/register` - Manual registration
- `/profile` - View your profile and stats
- `/balance` - Check your current balance
- `/help` - Show help message

### Crypto Commands
- `/deposit <amount>` - Deposit cryptocurrency
- `/withdraw <amount> <address>` - Withdraw crypto
- `/transactions` - View transaction history

### Game Commands
- `/games` - List available games
- `/play` - Start/resume active games
- `/status` - Check current game status
- `/challenge <username> <game> <amount>` - Challenge a player
- `/search <username>` - Search for players
- `/accept` - Accept game invitations
- `/decline` - Decline game invitations

### Game Controls
**Tetris:**
- `/left` - Move piece left
- `/right` - Move piece right
- `/down` - Move piece down
- `/rotate` - Rotate piece
- `/drop` - Drop piece to bottom

**Snake:**
- `/up` - Move up
- `/down` - Move down
- `/left` - Move left
- `/right` - Move right
- `/tick` - Advance one turn

**Ping Pong:**
- `/up` - Move paddle up
- `/down` - Move paddle down
- `/tick` - Advance ball

### Other Commands
- `/leaderboard` - View top players

## Usage Examples

### Register and Deposit
```
/start
/register
/deposit 50
```

### Challenge a Player
```
/search john_doe
/challenge john_doe tetris 25
```

### Play a Game
```
/play
/left
/right
/rotate
/drop
```

## Game Rules

### Betting
- Minimum bet: $1.00
- Maximum bet: $1000.00
- Winner takes all wagered cryptocurrency
- Tie games refund both players

### Game Limits
- Games timeout after 5 minutes of inactivity
- Invitations expire after 1 minute
- Maximum 200 turns for Snake games
- Maximum 500 turns for Ping Pong games

## Development

### Project Structure
```
telegram_gaming_bot/
├── main.py                 # Main bot application
├── config.py              # Configuration management
├── models.py              # Database models
├── database.py            # Database operations
├── auth_handler.py        # User authentication
├── crypto_handler.py      # Cryptocurrency operations
├── game_handler.py        # Game management
├── matchmaking_handler.py # Player matchmaking
├── utils.py               # Utility functions
├── games/                 # Game implementations
│   ├── __init__.py
│   ├── tetris.py
│   ├── snake.py
│   └── ping_pong.py
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables template
└── README.md             # This file
```

### Adding New Games
1. Create a new game class in `games/` directory
2. Implement required methods: `get_game_display()`, `to_json()`, `from_json()`
3. Add game controls in `game_handler.py`
4. Update `games/__init__.py` to export the new game

### Database Schema
The bot uses SQLAlchemy with the following main tables:
- `users` - User accounts and statistics
- `transactions` - Cryptocurrency transactions
- `game_sessions` - Active and completed games
- `game_invites` - Game invitations between players
- `crypto_addresses` - User cryptocurrency addresses

## Security Considerations

- All user inputs are sanitized
- Cryptocurrency operations use secure APIs
- Database queries use parameterized statements
- Session management with secure tokens
- Rate limiting on commands (recommended for production)

## Production Deployment

### Using Webhooks
For production, use webhooks instead of polling:

```python
# In main.py, replace start_polling() with:
await bot.start_webhook(
    webhook_url="https://yourdomain.com/webhook",
    port=8443
)
```

### Environment Variables
Set these additional variables for production:
```env
DATABASE_URL=postgresql://user:pass@host:port/dbname
WEBHOOK_URL=https://yourdomain.com/webhook
PORT=8443
```

### Scaling
- Use Redis for game state storage
- Implement database connection pooling
- Add rate limiting and anti-spam measures
- Use load balancers for multiple bot instances

## Legal Considerations

⚠️ **Important**: Real money gambling may be subject to legal restrictions in your jurisdiction. Please ensure compliance with local laws and regulations before deploying this bot with real cryptocurrency.

Consider implementing:
- Age verification
- Responsible gaming features
- Jurisdiction restrictions
- Proper licensing and compliance

## Support

For issues and questions:
1. Check the logs for error messages
2. Verify your API credentials are correct
3. Ensure your bot has proper permissions
4. Test with small amounts first

## License

This project is for educational purposes. Please ensure compliance with local laws and regulations before using with real cryptocurrency.
