import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    filters,
    ContextTypes
)

# Import handlers
from auth_handler import auth_handler
from crypto_handler import crypto_handler
from game_handler import game_handler
from matchmaking_handler import matchmaking_handler
from database import DatabaseManager
from config import Config
from utils import setup_logger, sanitize_input

# Set up logging
logger = setup_logger(__name__)

class TelegramGamingBot:
    """Main Telegram Gaming Bot class"""
    
    def __init__(self):
        self.application = None
        self.setup_application()
    
    def setup_application(self):
        """Set up the Telegram application with handlers"""
        # Create application
        self.application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Add command handlers
        self.add_command_handlers()
        
        # Add message handlers
        self.add_message_handlers()
        
        # Add callback query handler
        self.add_callback_handlers()
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        logger.info("Telegram bot application set up successfully")
    
    def add_command_handlers(self):
        """Add all command handlers"""
        # Authentication commands
        self.application.add_handler(CommandHandler("start", auth_handler.start_command))
        self.application.add_handler(CommandHandler("register", auth_handler.register_manual_command))
        self.application.add_handler(CommandHandler("profile", auth_handler.profile_command))
        self.application.add_handler(CommandHandler("help", auth_handler.help_command))
        
        # Crypto commands
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("deposit", self.deposit_command))
        self.application.add_handler(CommandHandler("withdraw", self.withdraw_command))
        self.application.add_handler(CommandHandler("transactions", self.transactions_command))
        
        # Game commands
        self.application.add_handler(CommandHandler("games", game_handler.games_command))
        self.application.add_handler(CommandHandler("play", game_handler.play_command))
        self.application.add_handler(CommandHandler("status", game_handler.status_command))
        
        # Matchmaking commands
        self.application.add_handler(CommandHandler("search", matchmaking_handler.search_command))
        self.application.add_handler(CommandHandler("challenge", matchmaking_handler.challenge_command))
        self.application.add_handler(CommandHandler("accept", matchmaking_handler.accept_command))
        self.application.add_handler(CommandHandler("decline", matchmaking_handler.decline_command))
        
        # Game control commands
        self.application.add_handler(CommandHandler("left", lambda u, c: game_handler.handle_game_move(u, c, "left")))
        self.application.add_handler(CommandHandler("right", lambda u, c: game_handler.handle_game_move(u, c, "right")))
        self.application.add_handler(CommandHandler("up", lambda u, c: game_handler.handle_game_move(u, c, "up")))
        self.application.add_handler(CommandHandler("down", lambda u, c: game_handler.handle_game_move(u, c, "down")))
        self.application.add_handler(CommandHandler("rotate", lambda u, c: game_handler.handle_game_move(u, c, "rotate")))
        self.application.add_handler(CommandHandler("drop", lambda u, c: game_handler.handle_game_move(u, c, "drop")))
        self.application.add_handler(CommandHandler("tick", lambda u, c: game_handler.handle_game_move(u, c, "tick")))
        
        # Additional commands
        self.application.add_handler(CommandHandler("leaderboard", self.leaderboard_command))
        
        logger.info("Command handlers added successfully")
    
    def add_message_handlers(self):
        """Add message handlers for text input"""
        # Handle registration input
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, 
                self.handle_text_message
            )
        )
        
        logger.info("Message handlers added successfully")
    
    def add_callback_handlers(self):
        """Add callback query handlers for inline keyboards"""
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        logger.info("Callback handlers added successfully")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages (for registration, bet amounts, etc.)"""
        try:
            # Sanitize input
            text = sanitize_input(update.message.text)
            
            # Check if user is in registration process
            if 'registration_step' in context.user_data:
                await auth_handler.handle_registration_input(update, context)
                return
            
            # Check if user is entering bet amount for challenge
            if context.user_data.get('awaiting_bet_amount'):
                await matchmaking_handler.handle_bet_amount_input(update, context)
                return
            
            # Default response for unhandled text
            await update.message.reply_text(
                "🤖 I didn't understand that command. Use /help to see available commands."
            )
            
        except Exception as e:
            logger.error(f"Error handling text message: {e}")
            await update.message.reply_text("❌ An error occurred. Please try again.")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        try:
            query = update.callback_query
            
            # Route callback to appropriate handler
            if query.data.startswith("register_"):
                await auth_handler.button_callback(update, context)
            elif query.data.startswith("challenge_"):
                await matchmaking_handler.handle_challenge_callback(update, context)
            elif query.data.startswith("accept_invite_") or query.data.startswith("decline_invite_"):
                await matchmaking_handler.handle_challenge_callback(update, context)
            elif query.data.startswith("play_game_"):
                await self.handle_play_game_callback(update, context)
            elif query.data in ["deposit", "withdraw", "games", "search", "help"]:
                await auth_handler.button_callback(update, context)
            else:
                await query.answer("Unknown action")
                
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            await update.callback_query.answer("❌ An error occurred")
    
    async def handle_play_game_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle play game callback"""
        try:
            query = update.callback_query
            game_session_id = int(query.data.split("_")[2])
            
            # Get game session and start it
            session = DatabaseManager.db.get_session()
            try:
                from models import GameSession
                game_session = session.query(GameSession).filter(GameSession.id == game_session_id).first()
                
                if game_session:
                    await game_handler.start_game_session(update, context, game_session)
                else:
                    await query.edit_message_text("❌ Game session not found.")
                    
            finally:
                DatabaseManager.db.close_session(session)
                
        except Exception as e:
            logger.error(f"Error handling play game callback: {e}")
            await update.callback_query.answer("❌ Error starting game")
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        try:
            user = update.effective_user
            telegram_id = str(user.id)
            
            db_user = DatabaseManager.get_user_by_telegram_id(telegram_id)
            if not db_user:
                await update.message.reply_text("❌ You need to register first. Use /start to register.")
                return
            
            balance_message = f"💰 Your Balance\n\n"
            balance_message += f"💳 Current Balance: ${db_user.balance:.2f}\n"
            balance_message += f"🏆 Total Winnings: ${db_user.total_winnings:.2f}\n"
            balance_message += f"🎮 Games Played: {db_user.total_games_played}\n\n"
            balance_message += "Use /deposit to add funds or /withdraw to cash out!"
            
            await update.message.reply_text(balance_message)
            
        except Exception as e:
            logger.error(f"Error in balance command: {e}")
            await update.message.reply_text("❌ Error retrieving balance.")
    
    async def deposit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /deposit command"""
        try:
            user = update.effective_user
            telegram_id = str(user.id)
            
            db_user = DatabaseManager.get_user_by_telegram_id(telegram_id)
            if not db_user:
                await update.message.reply_text("❌ You need to register first. Use /start to register.")
                return
            
            if not context.args:
                await update.message.reply_text(
                    "💰 Deposit Cryptocurrency\n\n"
                    "Usage: /deposit <amount>\n"
                    "Example: /deposit 50\n\n"
                    "Supported currencies: BTC, ETH, USDT, USDC"
                )
                return
            
            try:
                amount = float(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ Invalid amount. Please enter a valid number.")
                return
            
            if amount < 1:
                await update.message.reply_text("❌ Minimum deposit amount is $1.00")
                return
            
            if amount > 10000:
                await update.message.reply_text("❌ Maximum deposit amount is $10,000.00")
                return
            
            # Create deposit charge
            result = crypto_handler.create_deposit_charge(db_user.id, amount)
            
            if result.get("success"):
                deposit_message = f"💰 Deposit Created!\n\n"
                deposit_message += f"💵 Amount: ${amount:.2f}\n"
                deposit_message += f"🆔 Charge ID: {result['charge_id']}\n\n"
                deposit_message += f"🔗 Payment URL: {result['hosted_url']}\n\n"
                deposit_message += "Send cryptocurrency to complete the deposit. "
                deposit_message += "Funds will be credited automatically once confirmed."
                
                await update.message.reply_text(deposit_message)
            else:
                await update.message.reply_text(f"❌ Failed to create deposit: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error in deposit command: {e}")
            await update.message.reply_text("❌ Error processing deposit request.")
    
    async def withdraw_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /withdraw command"""
        try:
            user = update.effective_user
            telegram_id = str(user.id)
            
            db_user = DatabaseManager.get_user_by_telegram_id(telegram_id)
            if not db_user:
                await update.message.reply_text("❌ You need to register first. Use /start to register.")
                return
            
            if len(context.args) < 2:
                await update.message.reply_text(
                    "💸 Withdraw Cryptocurrency\n\n"
                    "Usage: /withdraw <amount> <crypto_address>\n"
                    "Example: /withdraw 25 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa\n\n"
                    "⚠️ Make sure your address is correct!\n"
                    "Minimum withdrawal: $10.00"
                )
                return
            
            try:
                amount = float(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ Invalid amount. Please enter a valid number.")
                return
            
            crypto_address = context.args[1]
            
            if amount < 10:
                await update.message.reply_text("❌ Minimum withdrawal amount is $10.00")
                return
            
            if amount > db_user.balance:
                await update.message.reply_text(f"❌ Insufficient balance. You have ${db_user.balance:.2f}")
                return
            
            # Process withdrawal
            result = crypto_handler.process_withdrawal(db_user.id, amount, crypto_address, "BTC")
            
            if result.get("success"):
                withdraw_message = f"💸 Withdrawal Processed!\n\n"
                withdraw_message += f"💵 Amount: ${amount:.2f}\n"
                withdraw_message += f"📍 Address: {crypto_address}\n"
                withdraw_message += f"🆔 Transaction ID: {result['transaction_id']}\n\n"
                withdraw_message += "Your withdrawal is being processed. "
                withdraw_message += "It may take a few minutes to complete."
                
                await update.message.reply_text(withdraw_message)
            else:
                await update.message.reply_text(f"❌ Withdrawal failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Error in withdraw command: {e}")
            await update.message.reply_text("❌ Error processing withdrawal request.")
    
    async def transactions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /transactions command"""
        try:
            user = update.effective_user
            telegram_id = str(user.id)
            
            db_user = DatabaseManager.get_user_by_telegram_id(telegram_id)
            if not db_user:
                await update.message.reply_text("❌ You need to register first. Use /start to register.")
                return
            
            transactions = DatabaseManager.get_user_transactions(db_user.id, limit=10)
            
            if not transactions:
                await update.message.reply_text("💳 No transactions found.")
                return
            
            from utils import format_transaction_history
            message = format_transaction_history(transactions)
            
            await update.message.reply_text(message)
            
        except Exception as e:
            logger.error(f"Error in transactions command: {e}")
            await update.message.reply_text("❌ Error retrieving transactions.")
    
    async def leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /leaderboard command"""
        try:
            # Get top players by winnings
            session = DatabaseManager.db.get_session()
            try:
                from models import User
                top_players = session.query(User).filter(
                    User.total_games_played > 0
                ).order_by(User.total_winnings.desc()).limit(10).all()
                
                if not top_players:
                    await update.message.reply_text("📊 No players found on the leaderboard yet.")
                    return
                
                from utils import format_leaderboard
                message = format_leaderboard(top_players, "🏆 Top Players by Winnings")
                
                await update.message.reply_text(message)
                
            finally:
                DatabaseManager.db.close_session(session)
                
        except Exception as e:
            logger.error(f"Error in leaderboard command: {e}")
            await update.message.reply_text("❌ Error retrieving leaderboard.")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        # Try to send error message to user if possible
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ An unexpected error occurred. Please try again or contact support."
                )
            except Exception:
                pass  # Ignore if we can't send the error message
    
    async def start_webhook(self, webhook_url: str, port: int = 8443):
        """Start the bot with webhook"""
        await self.application.bot.set_webhook(url=webhook_url)
        await self.application.start()
        await self.application.updater.start_webhook(
            listen="0.0.0.0",
            port=port,
            url_path="webhook"
        )
        logger.info(f"Bot started with webhook: {webhook_url}")
    
    async def start_polling(self):
        """Start the bot with polling"""
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("Bot started with polling")
        
        # Keep the bot running
        await self.application.updater.idle()
    
    async def stop(self):
        """Stop the bot"""
        await self.application.stop()
        logger.info("Bot stopped")

async def main():
    """Main function to run the bot"""
    try:
        # Initialize the bot
        bot = TelegramGamingBot()
        
        # Start the bot with polling (for development)
        # For production, use webhook instead
        await bot.start_polling()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        raise

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
