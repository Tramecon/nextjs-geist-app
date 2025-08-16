import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import DatabaseManager
from models import GameType, InviteStatus
from config import Config
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MatchmakingHandler:
    """Handle player matchmaking and game invitations"""
    
    def __init__(self):
        pass
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command"""
        user = update.effective_user
        telegram_id = str(user.id)
        
        # Check if user is registered
        db_user = DatabaseManager.get_user_by_telegram_id(telegram_id)
        if not db_user:
            await update.message.reply_text("❌ You need to register first. Use /start to register.")
            return
        
        # Check if username is provided
        if not context.args:
            message = "🔍 Search for Players\n\n"
            message += "Usage: /search <username>\n\n"
            message += "Example: /search john_doe\n\n"
            message += "💡 Tip: You can also use /challenge <username> <game> <amount> to directly challenge a player!"
            
            await update.message.reply_text(message)
            return
        
        search_username = context.args[0].strip()
        
        # Search for the user
        target_user = DatabaseManager.get_user_by_username(search_username)
        
        if not target_user:
            await update.message.reply_text(f"❌ Player '{search_username}' not found.")
            return
        
        if target_user.telegram_id == telegram_id:
            await update.message.reply_text("❌ You cannot challenge yourself!")
            return
        
        # Display user info and challenge options
        user_info = f"👤 Player Found: {target_user.username}\n\n"
        user_info += f"🎮 Games Played: {target_user.total_games_played}\n"
        user_info += f"🏆 Games Won: {target_user.total_games_won}\n"
        
        if target_user.total_games_played > 0:
            win_rate = (target_user.total_games_won / target_user.total_games_played) * 100
            user_info += f"📊 Win Rate: {win_rate:.1f}%\n"
        
        user_info += f"📅 Member Since: {target_user.registration_date.strftime('%Y-%m-%d')}\n\n"
        user_info += "Choose a game to challenge this player:"
        
        # Create challenge buttons
        keyboard = [
            [InlineKeyboardButton("🧩 Tetris", callback_data=f"challenge_{target_user.id}_tetris")],
            [InlineKeyboardButton("🐍 Snake", callback_data=f"challenge_{target_user.id}_snake")],
            [InlineKeyboardButton("🏓 Ping Pong", callback_data=f"challenge_{target_user.id}_pingpong")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_challenge")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(user_info, reply_markup=reply_markup)
    
    async def challenge_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /challenge command"""
        user = update.effective_user
        telegram_id = str(user.id)
        
        # Check if user is registered
        db_user = DatabaseManager.get_user_by_telegram_id(telegram_id)
        if not db_user:
            await update.message.reply_text("❌ You need to register first. Use /start to register.")
            return
        
        # Check command arguments
        if len(context.args) < 3:
            message = "🎯 Challenge a Player\n\n"
            message += "Usage: /challenge <username> <game> <amount>\n\n"
            message += "Games: tetris, snake, pingpong\n"
            message += f"Amount: ${Config.MIN_BET_AMOUNT} - ${Config.MAX_BET_AMOUNT}\n\n"
            message += "Example: /challenge john_doe tetris 25"
            
            await update.message.reply_text(message)
            return
        
        target_username = context.args[0].strip()
        game_type = context.args[1].strip().lower()
        
        try:
            bet_amount = float(context.args[2])
        except ValueError:
            await update.message.reply_text("❌ Invalid bet amount. Please enter a valid number.")
            return
        
        # Validate game type
        valid_games = ["tetris", "snake", "pingpong"]
        if game_type not in valid_games:
            await update.message.reply_text(f"❌ Invalid game type. Choose from: {', '.join(valid_games)}")
            return
        
        # Validate bet amount
        if bet_amount < Config.MIN_BET_AMOUNT or bet_amount > Config.MAX_BET_AMOUNT:
            await update.message.reply_text(f"❌ Bet amount must be between ${Config.MIN_BET_AMOUNT} and ${Config.MAX_BET_AMOUNT}")
            return
        
        # Check user balance
        if db_user.balance < bet_amount:
            await update.message.reply_text(f"❌ Insufficient balance. You have ${db_user.balance:.2f}, need ${bet_amount:.2f}")
            return
        
        # Find target user
        target_user = DatabaseManager.get_user_by_username(target_username)
        if not target_user:
            await update.message.reply_text(f"❌ Player '{target_username}' not found.")
            return
        
        if target_user.telegram_id == telegram_id:
            await update.message.reply_text("❌ You cannot challenge yourself!")
            return
        
        # Check target user balance
        if target_user.balance < bet_amount:
            await update.message.reply_text(f"❌ {target_username} has insufficient balance for this bet amount.")
            return
        
        # Create game invitation
        invite = DatabaseManager.create_game_invite(
            from_user_id=db_user.id,
            to_user_id=target_user.id,
            game_type=game_type,
            bet_amount=bet_amount
        )
        
        if invite:
            # Send challenge message to challenger
            challenge_message = f"🎯 Challenge Sent!\n\n"
            challenge_message += f"👤 Opponent: {target_username}\n"
            challenge_message += f"🎮 Game: {game_type.title()}\n"
            challenge_message += f"💰 Bet Amount: ${bet_amount:.2f}\n\n"
            challenge_message += f"⏰ Expires in {Config.INVITATION_TIMEOUT} minutes"
            
            await update.message.reply_text(challenge_message)
            
            # Send invitation to target user (if they have a chat with the bot)
            try:
                invite_message = f"🎯 Game Challenge Received!\n\n"
                invite_message += f"👤 From: {db_user.username}\n"
                invite_message += f"🎮 Game: {game_type.title()}\n"
                invite_message += f"💰 Bet Amount: ${bet_amount:.2f}\n\n"
                invite_message += f"⏰ Expires in {Config.INVITATION_TIMEOUT} minutes\n\n"
                invite_message += "Use /accept to accept or /decline to decline"
                
                keyboard = [
                    [InlineKeyboardButton("✅ Accept", callback_data=f"accept_invite_{invite.id}")],
                    [InlineKeyboardButton("❌ Decline", callback_data=f"decline_invite_{invite.id}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.send_message(
                    chat_id=int(target_user.telegram_id),
                    text=invite_message,
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.warning(f"Could not send invitation to user {target_user.telegram_id}: {e}")
                await update.message.reply_text("⚠️ Challenge sent, but the player may not receive the notification immediately.")
        else:
            await update.message.reply_text("❌ Failed to send challenge. Please try again.")
    
    async def accept_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /accept command"""
        user = update.effective_user
        telegram_id = str(user.id)
        
        # Check if user is registered
        db_user = DatabaseManager.get_user_by_telegram_id(telegram_id)
        if not db_user:
            await update.message.reply_text("❌ You need to register first. Use /start to register.")
            return
        
        # Get pending invitations
        pending_invites = DatabaseManager.get_pending_invites(db_user.id)
        
        if not pending_invites:
            await update.message.reply_text("❌ You have no pending game invitations.")
            return
        
        # Show pending invitations
        if len(pending_invites) == 1:
            invite = pending_invites[0]
            await self.process_invite_acceptance(update, context, invite.id)
        else:
            # Multiple invitations - show list
            message = "🎯 Pending Game Invitations:\n\n"
            keyboard = []
            
            for i, invite in enumerate(pending_invites, 1):
                sender = DatabaseManager.get_user_by_telegram_id(str(invite.sender.telegram_id))
                message += f"{i}. {sender.username} - {invite.game_type.value.title()} - ${invite.bet_amount:.2f}\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"Accept #{i}", 
                    callback_data=f"accept_invite_{invite.id}"
                )])
            
            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_accept")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(message, reply_markup=reply_markup)
    
    async def decline_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /decline command"""
        user = update.effective_user
        telegram_id = str(user.id)
        
        # Check if user is registered
        db_user = DatabaseManager.get_user_by_telegram_id(telegram_id)
        if not db_user:
            await update.message.reply_text("❌ You need to register first. Use /start to register.")
            return
        
        # Get pending invitations
        pending_invites = DatabaseManager.get_pending_invites(db_user.id)
        
        if not pending_invites:
            await update.message.reply_text("❌ You have no pending game invitations.")
            return
        
        # Decline all pending invitations
        session = DatabaseManager.db.get_session()
        try:
            for invite in pending_invites:
                invite.status = InviteStatus.DECLINED
                invite.responded_at = datetime.utcnow()
            
            session.commit()
            await update.message.reply_text(f"❌ Declined {len(pending_invites)} game invitation(s).")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error declining invitations: {e}")
            await update.message.reply_text("❌ Failed to decline invitations. Please try again.")
        finally:
            DatabaseManager.db.close_session(session)
    
    async def process_invite_acceptance(self, update: Update, context: ContextTypes.DEFAULT_TYPE, invite_id: int):
        """Process invitation acceptance"""
        user = update.effective_user
        telegram_id = str(user.id)
        
        db_user = DatabaseManager.get_user_by_telegram_id(telegram_id)
        
        # Get the invitation
        session = DatabaseManager.db.get_session()
        try:
            from models import GameInvite
            invite = session.query(GameInvite).filter(GameInvite.id == invite_id).first()
            
            if not invite:
                await update.message.reply_text("❌ Invitation not found.")
                return
            
            if invite.to_user_id != db_user.id:
                await update.message.reply_text("❌ This invitation is not for you.")
                return
            
            if invite.status != InviteStatus.PENDING:
                await update.message.reply_text("❌ This invitation has already been responded to.")
                return
            
            if invite.is_expired():
                invite.status = InviteStatus.EXPIRED
                session.commit()
                await update.message.reply_text("❌ This invitation has expired.")
                return
            
            # Check balance
            if db_user.balance < invite.bet_amount:
                await update.message.reply_text(f"❌ Insufficient balance. You need ${invite.bet_amount:.2f}")
                return
            
            # Accept the invitation
            invite.status = InviteStatus.ACCEPTED
            invite.responded_at = datetime.utcnow()
            session.commit()
            
            # Create game session
            game_session = DatabaseManager.create_game_session(
                player1_id=invite.from_user_id,
                player2_id=invite.to_user_id,
                game_type=invite.game_type.value,
                bet_amount=invite.bet_amount
            )
            
            if game_session:
                # Deduct bet amounts from both players
                DatabaseManager.update_user_balance(
                    invite.from_user_id, 
                    -invite.bet_amount, 
                    "bet_placed",
                    f"Bet placed for {invite.game_type.value} game"
                )
                DatabaseManager.update_user_balance(
                    invite.to_user_id, 
                    -invite.bet_amount, 
                    "bet_placed",
                    f"Bet placed for {invite.game_type.value} game"
                )
                
                # Send confirmation messages
                accept_message = f"✅ Challenge Accepted!\n\n"
                accept_message += f"🎮 Game: {invite.game_type.value.title()}\n"
                accept_message += f"💰 Bet Amount: ${invite.bet_amount:.2f}\n"
                accept_message += f"🆔 Game ID: {game_session.session_id}\n\n"
                accept_message += f"Use /play to start the game!"
                
                await update.message.reply_text(accept_message)
                
                # Notify the challenger
                try:
                    challenger = session.query(User).filter(User.id == invite.from_user_id).first()
                    notify_message = f"🎉 Challenge Accepted!\n\n"
                    notify_message += f"👤 {db_user.username} accepted your challenge!\n"
                    notify_message += f"🎮 Game: {invite.game_type.value.title()}\n"
                    notify_message += f"🆔 Game ID: {game_session.session_id}\n\n"
                    notify_message += f"Use /play to start the game!"
                    
                    await context.bot.send_message(
                        chat_id=int(challenger.telegram_id),
                        text=notify_message
                    )
                except Exception as e:
                    logger.warning(f"Could not notify challenger: {e}")
            else:
                await update.message.reply_text("❌ Failed to create game session. Please try again.")
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error processing invite acceptance: {e}")
            await update.message.reply_text("❌ Failed to accept invitation. Please try again.")
        finally:
            DatabaseManager.db.close_session(session)
    
    async def handle_challenge_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle challenge button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("challenge_"):
            parts = query.data.split("_")
            target_user_id = int(parts[1])
            game_type = parts[2]
            
            # Ask for bet amount
            context.user_data['challenge_target_id'] = target_user_id
            context.user_data['challenge_game'] = game_type
            context.user_data['awaiting_bet_amount'] = True
            
            message = f"💰 Enter Bet Amount\n\n"
            message += f"🎮 Game: {game_type.title()}\n"
            message += f"💵 Range: ${Config.MIN_BET_AMOUNT} - ${Config.MAX_BET_AMOUNT}\n\n"
            message += f"Enter the amount you want to bet:"
            
            await query.edit_message_text(message)
        
        elif query.data.startswith("accept_invite_"):
            invite_id = int(query.data.split("_")[2])
            await self.process_invite_acceptance(update, context, invite_id)
        
        elif query.data.startswith("decline_invite_"):
            invite_id = int(query.data.split("_")[2])
            await self.process_invite_decline(update, context, invite_id)
    
    async def process_invite_decline(self, update: Update, context: ContextTypes.DEFAULT_TYPE, invite_id: int):
        """Process invitation decline"""
        query = update.callback_query
        
        session = DatabaseManager.db.get_session()
        try:
            from models import GameInvite
            invite = session.query(GameInvite).filter(GameInvite.id == invite_id).first()
            
            if invite and invite.status == InviteStatus.PENDING:
                invite.status = InviteStatus.DECLINED
                invite.responded_at = datetime.utcnow()
                session.commit()
                
                await query.edit_message_text("❌ Game invitation declined.")
            else:
                await query.edit_message_text("❌ Invitation not found or already responded to.")
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error declining invitation: {e}")
            await query.edit_message_text("❌ Failed to decline invitation.")
        finally:
            DatabaseManager.db.close_session(session)
    
    async def handle_bet_amount_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bet amount input for challenges"""
        if not context.user_data.get('awaiting_bet_amount'):
            return
        
        try:
            bet_amount = float(update.message.text.strip())
        except ValueError:
            await update.message.reply_text("❌ Invalid amount. Please enter a valid number.")
            return
        
        # Validate bet amount
        if bet_amount < Config.MIN_BET_AMOUNT or bet_amount > Config.MAX_BET_AMOUNT:
            await update.message.reply_text(f"❌ Bet amount must be between ${Config.MIN_BET_AMOUNT} and ${Config.MAX_BET_AMOUNT}")
            return
        
        # Get challenge data
        target_user_id = context.user_data.get('challenge_target_id')
        game_type = context.user_data.get('challenge_game')
        
        if not target_user_id or not game_type:
            await update.message.reply_text("❌ Challenge data not found. Please try again.")
            context.user_data.clear()
            return
        
        # Process the challenge
        user = update.effective_user
        telegram_id = str(user.id)
        db_user = DatabaseManager.get_user_by_telegram_id(telegram_id)
        
        # Check user balance
        if db_user.balance < bet_amount:
            await update.message.reply_text(f"❌ Insufficient balance. You have ${db_user.balance:.2f}, need ${bet_amount:.2f}")
            context.user_data.clear()
            return
        
        # Get target user
        session = DatabaseManager.db.get_session()
        try:
            target_user = session.query(User).filter(User.id == target_user_id).first()
            
            if not target_user:
                await update.message.reply_text("❌ Target user not found.")
                context.user_data.clear()
                return
            
            # Check target user balance
            if target_user.balance < bet_amount:
                await update.message.reply_text(f"❌ {target_user.username} has insufficient balance for this bet amount.")
                context.user_data.clear()
                return
            
            # Create game invitation
            invite = DatabaseManager.create_game_invite(
                from_user_id=db_user.id,
                to_user_id=target_user.id,
                game_type=game_type,
                bet_amount=bet_amount
            )
            
            if invite:
                # Send success message
                success_message = f"🎯 Challenge Sent!\n\n"
                success_message += f"👤 Opponent: {target_user.username}\n"
                success_message += f"🎮 Game: {game_type.title()}\n"
                success_message += f"💰 Bet Amount: ${bet_amount:.2f}\n\n"
                success_message += f"⏰ Expires in {Config.INVITATION_TIMEOUT} minutes"
                
                await update.message.reply_text(success_message)
                
                # Send invitation to target user
                try:
                    invite_message = f"🎯 Game Challenge Received!\n\n"
                    invite_message += f"👤 From: {db_user.username}\n"
                    invite_message += f"🎮 Game: {game_type.title()}\n"
                    invite_message += f"💰 Bet Amount: ${bet_amount:.2f}\n\n"
                    invite_message += f"⏰ Expires in {Config.INVITATION_TIMEOUT} minutes\n\n"
                    invite_message += "Use /accept to accept or /decline to decline"
                    
                    keyboard = [
                        [InlineKeyboardButton("✅ Accept", callback_data=f"accept_invite_{invite.id}")],
                        [InlineKeyboardButton("❌ Decline", callback_data=f"decline_invite_{invite.id}")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await context.bot.send_message(
                        chat_id=int(target_user.telegram_id),
                        text=invite_message,
                        reply_markup=reply_markup
                    )
                except Exception as e:
                    logger.warning(f"Could not send invitation to user {target_user.telegram_id}: {e}")
                    await update.message.reply_text("⚠️ Challenge sent, but the player may not receive the notification immediately.")
            else:
                await update.message.reply_text("❌ Failed to send challenge. Please try again.")
            
        finally:
            DatabaseManager.db.close_session(session)
            context.user_data.clear()

# Global matchmaking handler instance
matchmaking_handler = MatchmakingHandler()
