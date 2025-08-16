import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import DatabaseManager
from models import GameStatus, TransactionType
from games import TetrisGame, SnakeGame, PingPongGame
from config import Config
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class GameHandler:
    """Handle game operations and gameplay"""
    
    def __init__(self):
        # Store active games in memory (in production, use Redis or database)
        self.active_games = {}
    
    async def games_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /games command - show available games"""
        user = update.effective_user
        telegram_id = str(user.id)
        
        # Check if user is registered
        db_user = DatabaseManager.get_user_by_telegram_id(telegram_id)
        if not db_user:
            await update.message.reply_text("❌ You need to register first. Use /start to register.")
            return
        
        games_message = "🎮 Available Games\n\n"
        games_message += "Choose a game to play:\n\n"
        
        games_message += "🧩 **Tetris**\n"
        games_message += "Classic block-stacking puzzle game\n"
        games_message += "Score points by clearing lines\n\n"
        
        games_message += "🐍 **Snake**\n"
        games_message += "Control your snake to eat food\n"
        games_message += "Avoid walls and other snakes\n\n"
        
        games_message += "🏓 **Ping Pong**\n"
        games_message += "Classic paddle ball game\n"
        games_message += "First to 11 points wins\n\n"
        
        games_message += f"💰 Bet Range: ${Config.MIN_BET_AMOUNT} - ${Config.MAX_BET_AMOUNT}\n"
        games_message += f"💳 Your Balance: ${db_user.balance:.2f}\n\n"
        
        games_message += "To challenge someone:\n"
        games_message += "/challenge <username> <game> <amount>\n\n"
        games_message += "Example: /challenge john_doe tetris 25"
        
        keyboard = [
            [InlineKeyboardButton("🔍 Search Players", callback_data="search_players")],
            [InlineKeyboardButton("📊 My Stats", callback_data="my_stats")],
            [InlineKeyboardButton("🎯 Active Games", callback_data="active_games")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(games_message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def play_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /play command - start or resume a game"""
        user = update.effective_user
        telegram_id = str(user.id)
        
        # Check if user is registered
        db_user = DatabaseManager.get_user_by_telegram_id(telegram_id)
        if not db_user:
            await update.message.reply_text("❌ You need to register first. Use /start to register.")
            return
        
        # Find active game sessions for this user
        session = DatabaseManager.db.get_session()
        try:
            from models import GameSession
            active_sessions = session.query(GameSession).filter(
                ((GameSession.player1_id == db_user.id) | (GameSession.player2_id == db_user.id)),
                GameSession.status == GameStatus.ACCEPTED
            ).all()
            
            if not active_sessions:
                await update.message.reply_text("❌ You have no active games. Use /challenge to start a new game.")
                return
            
            if len(active_sessions) == 1:
                # Start the single active game
                game_session = active_sessions[0]
                await self.start_game_session(update, context, game_session)
            else:
                # Multiple active games - let user choose
                message = "🎮 Active Games:\n\n"
                keyboard = []
                
                for i, game_session in enumerate(active_sessions, 1):
                    opponent_id = game_session.player2_id if game_session.player1_id == db_user.id else game_session.player1_id
                    opponent = session.query(User).filter(User.id == opponent_id).first()
                    
                    message += f"{i}. {game_session.game_type.value.title()} vs {opponent.username} - ${game_session.bet_amount:.2f}\n"
                    
                    keyboard.append([InlineKeyboardButton(
                        f"Play Game #{i}", 
                        callback_data=f"play_game_{game_session.id}"
                    )])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(message, reply_markup=reply_markup)
                
        finally:
            DatabaseManager.db.close_session(session)
    
    async def start_game_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game_session):
        """Start a specific game session"""
        # Create game instance based on type
        if game_session.game_type.value == "tetris":
            game = TetrisGame(game_session.session_id, game_session.player1_id, game_session.player2_id)
        elif game_session.game_type.value == "snake":
            game = SnakeGame(game_session.session_id, game_session.player1_id, game_session.player2_id)
        elif game_session.game_type.value == "pingpong":
            game = PingPongGame(game_session.session_id, game_session.player1_id, game_session.player2_id)
        else:
            await update.message.reply_text("❌ Unknown game type.")
            return
        
        # Store game in active games
        self.active_games[game_session.session_id] = game
        
        # Update game session status
        session = DatabaseManager.db.get_session()
        try:
            game_session.status = GameStatus.ACTIVE
            game_session.started_at = datetime.utcnow()
            game_session.game_data = game.to_json()
            session.commit()
        finally:
            DatabaseManager.db.close_session(session)
        
        # Send game start message
        start_message = f"🎮 {game_session.game_type.value.title()} Game Started!\n\n"
        start_message += f"🆔 Game ID: {game_session.session_id}\n"
        start_message += f"💰 Bet Amount: ${game_session.bet_amount:.2f}\n\n"
        start_message += game.get_game_display()
        
        # Show game board
        if hasattr(game, 'get_board_display'):
            start_message += game.get_board_display()
        elif hasattr(game, 'get_field_display'):
            start_message += game.get_field_display()
        
        await update.message.reply_text(start_message)
        
        # Notify both players
        try:
            player1 = DatabaseManager.get_user_by_telegram_id(str(game_session.player1_id))
            player2 = DatabaseManager.get_user_by_telegram_id(str(game_session.player2_id))
            
            for player in [player1, player2]:
                if player and str(player.telegram_id) != str(update.effective_user.id):
                    try:
                        await context.bot.send_message(
                            chat_id=int(player.telegram_id),
                            text=f"🎮 Your {game_session.game_type.value.title()} game has started!\n"
                                 f"Game ID: {game_session.session_id}\n"
                                 f"Use /play to join the game!"
                        )
                    except Exception as e:
                        logger.warning(f"Could not notify player {player.telegram_id}: {e}")
        except Exception as e:
            logger.error(f"Error notifying players: {e}")
    
    async def handle_game_move(self, update: Update, context: ContextTypes.DEFAULT_TYPE, move_type: str):
        """Handle game moves (left, right, up, down, etc.)"""
        user = update.effective_user
        telegram_id = str(user.id)
        
        # Find user's active game
        db_user = DatabaseManager.get_user_by_telegram_id(telegram_id)
        if not db_user:
            await update.message.reply_text("❌ You need to register first.")
            return
        
        # Find active game session
        active_game = None
        game_session_id = None
        
        for session_id, game in self.active_games.items():
            if game.player1_id == db_user.id or game.player2_id == db_user.id:
                if not game.game_over:
                    active_game = game
                    game_session_id = session_id
                    break
        
        if not active_game:
            await update.message.reply_text("❌ You have no active games. Use /play to start a game.")
            return
        
        # Handle move based on game type
        result = None
        
        if isinstance(active_game, TetrisGame):
            if move_type in ["left", "right", "down", "rotate"]:
                result = active_game.move_piece(db_user.id, move_type)
            elif move_type == "drop":
                result = active_game.drop_piece(db_user.id)
        
        elif isinstance(active_game, SnakeGame):
            if move_type in ["up", "down", "left", "right"]:
                result = active_game.move_snake(db_user.id, move_type)
            elif move_type == "tick":
                result = active_game.update_game_state()
        
        elif isinstance(active_game, PingPongGame):
            if move_type in ["up", "down"]:
                result = active_game.move_paddle(db_user.id, move_type)
            elif move_type == "tick":
                result = active_game.simulate_turn()
        
        if result:
            # Send move result
            response_message = f"🎮 {result['message']}\n\n"
            
            # Add game display
            response_message += active_game.get_game_display()
            
            # Add board/field display
            if hasattr(active_game, 'get_board_display'):
                response_message += active_game.get_board_display()
            elif hasattr(active_game, 'get_field_display'):
                response_message += active_game.get_field_display()
            
            await update.message.reply_text(response_message)
            
            # Check if game is over
            if active_game.game_over:
                await self.handle_game_over(update, context, active_game, game_session_id)
            else:
                # Save game state
                await self.save_game_state(game_session_id, active_game)
        else:
            await update.message.reply_text("❌ Invalid move for this game.")
    
    async def handle_game_over(self, update: Update, context: ContextTypes.DEFAULT_TYPE, game, session_id: str):
        """Handle game completion"""
        try:
            # Get game session from database
            session = DatabaseManager.db.get_session()
            try:
                from models import GameSession
                game_session = session.query(GameSession).filter(
                    GameSession.session_id == session_id
                ).first()
                
                if not game_session:
                    logger.error(f"Game session {session_id} not found")
                    return
                
                # Update game session
                game_session.status = GameStatus.COMPLETED
                game_session.completed_at = datetime.utcnow()
                game_session.player1_score = game.player1_score
                game_session.player2_score = game.player2_score
                game_session.winner_id = game.winner
                game_session.game_data = game.to_json()
                
                # Calculate winnings
                total_pot = game_session.bet_amount * 2
                
                if game.winner:
                    # Someone won - transfer winnings
                    winner_id = game.winner
                    loser_id = game_session.player2_id if winner_id == game_session.player1_id else game_session.player1_id
                    
                    # Add winnings to winner
                    DatabaseManager.update_user_balance(
                        winner_id,
                        total_pot,
                        TransactionType.BET_WON.value,
                        f"Won {game_session.game_type.value} game - Session: {session_id}"
                    )
                    
                    # Update winner stats
                    winner = session.query(User).filter(User.id == winner_id).first()
                    if winner:
                        winner.total_games_played += 1
                        winner.total_games_won += 1
                        winner.total_winnings += total_pot
                    
                    # Update loser stats
                    loser = session.query(User).filter(User.id == loser_id).first()
                    if loser:
                        loser.total_games_played += 1
                    
                    winner_name = winner.username if winner else "Unknown"
                    loser_name = loser.username if loser else "Unknown"
                    
                    game_over_message = f"🎉 Game Over! 🎉\n\n"
                    game_over_message += f"🏆 Winner: {winner_name}\n"
                    game_over_message += f"💰 Winnings: ${total_pot:.2f}\n"
                    game_over_message += f"📊 Final Score: {game.player1_score} - {game.player2_score}\n\n"
                    game_over_message += f"🎮 Game: {game_session.game_type.value.title()}\n"
                    game_over_message += f"🆔 Session: {session_id}"
                    
                else:
                    # Tie game - refund bets
                    DatabaseManager.update_user_balance(
                        game_session.player1_id,
                        game_session.bet_amount,
                        TransactionType.BET_WON.value,
                        f"Tie game refund - Session: {session_id}"
                    )
                    DatabaseManager.update_user_balance(
                        game_session.player2_id,
                        game_session.bet_amount,
                        TransactionType.BET_WON.value,
                        f"Tie game refund - Session: {session_id}"
                    )
                    
                    # Update stats for both players
                    player1 = session.query(User).filter(User.id == game_session.player1_id).first()
                    player2 = session.query(User).filter(User.id == game_session.player2_id).first()
                    
                    if player1:
                        player1.total_games_played += 1
                    if player2:
                        player2.total_games_played += 1
                    
                    game_over_message = f"🤝 Tie Game! 🤝\n\n"
                    game_over_message += f"💰 Bets Refunded: ${game_session.bet_amount:.2f} each\n"
                    game_over_message += f"📊 Final Score: {game.player1_score} - {game.player2_score}\n\n"
                    game_over_message += f"🎮 Game: {game_session.game_type.value.title()}\n"
                    game_over_message += f"🆔 Session: {session_id}"
                
                session.commit()
                
                # Send game over message
                await update.message.reply_text(game_over_message)
                
                # Notify both players
                try:
                    player1 = DatabaseManager.get_user_by_telegram_id(str(game_session.player1_id))
                    player2 = DatabaseManager.get_user_by_telegram_id(str(game_session.player2_id))
                    
                    for player in [player1, player2]:
                        if player and str(player.telegram_id) != str(update.effective_user.id):
                            try:
                                await context.bot.send_message(
                                    chat_id=int(player.telegram_id),
                                    text=game_over_message
                                )
                            except Exception as e:
                                logger.warning(f"Could not notify player {player.telegram_id}: {e}")
                except Exception as e:
                    logger.error(f"Error notifying players about game over: {e}")
                
                # Remove game from active games
                if session_id in self.active_games:
                    del self.active_games[session_id]
                
            finally:
                DatabaseManager.db.close_session(session)
                
        except Exception as e:
            logger.error(f"Error handling game over: {e}")
            await update.message.reply_text("❌ Error processing game completion. Please contact support.")
    
    async def save_game_state(self, session_id: str, game):
        """Save current game state to database"""
        try:
            session = DatabaseManager.db.get_session()
            try:
                from models import GameSession
                game_session = session.query(GameSession).filter(
                    GameSession.session_id == session_id
                ).first()
                
                if game_session:
                    game_session.game_data = game.to_json()
                    game_session.player1_score = game.player1_score
                    game_session.player2_score = game.player2_score
                    session.commit()
                    
            finally:
                DatabaseManager.db.close_session(session)
                
        except Exception as e:
            logger.error(f"Error saving game state: {e}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command - show current game status"""
        user = update.effective_user
        telegram_id = str(user.id)
        
        db_user = DatabaseManager.get_user_by_telegram_id(telegram_id)
        if not db_user:
            await update.message.reply_text("❌ You need to register first.")
            return
        
        # Find user's active game
        active_game = None
        for session_id, game in self.active_games.items():
            if game.player1_id == db_user.id or game.player2_id == db_user.id:
                if not game.game_over:
                    active_game = game
                    break
        
        if not active_game:
            await update.message.reply_text("❌ You have no active games.")
            return
        
        # Show game status
        status_message = active_game.get_game_display()
        
        if hasattr(active_game, 'get_board_display'):
            status_message += active_game.get_board_display()
        elif hasattr(active_game, 'get_field_display'):
            status_message += active_game.get_field_display()
        
        await update.message.reply_text(status_message)

# Global game handler instance
game_handler = GameHandler()
