import random
import json
from typing import List, Tuple, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PingPongGame:
    """Ping Pong game implementation for multiplayer Telegram bot"""
    
    def __init__(self, session_id: str, player1_id: int, player2_id: int):
        self.session_id = session_id
        self.player1_id = player1_id
        self.player2_id = player2_id
        
        # Game field dimensions
        self.field_width = 20
        self.field_height = 10
        
        # Initialize game state
        self.reset_game()
        
    def reset_game(self):
        """Reset the game to initial state"""
        # Paddle positions (y-coordinate, paddles are 3 units tall)
        self.player1_paddle_y = self.field_height // 2 - 1  # Left paddle
        self.player2_paddle_y = self.field_height // 2 - 1  # Right paddle
        self.paddle_height = 3
        
        # Ball position and velocity
        self.ball_x = self.field_width // 2
        self.ball_y = self.field_height // 2
        self.ball_vel_x = random.choice([-1, 1])  # Start moving left or right
        self.ball_vel_y = random.choice([-1, 0, 1])  # Start with random y velocity
        
        # Scores
        self.player1_score = 0
        self.player2_score = 0
        
        # Game state
        self.game_over = False
        self.winner = None
        self.rally_count = 0
        self.max_score = 11  # First to 11 points wins
        self.turn_count = 0
        
        logger.info(f"Ping Pong game {self.session_id} reset")
    
    def move_paddle(self, player_id: int, direction: str) -> Dict[str, Any]:
        """Move a player's paddle"""
        if self.game_over:
            return {"success": False, "message": "Game is over"}
        
        if player_id == self.player1_id:
            current_y = self.player1_paddle_y
        elif player_id == self.player2_id:
            current_y = self.player2_paddle_y
        else:
            return {"success": False, "message": "Invalid player"}
        
        # Calculate new position
        if direction == "up":
            new_y = max(0, current_y - 1)
        elif direction == "down":
            new_y = min(self.field_height - self.paddle_height, current_y + 1)
        else:
            return {"success": False, "message": "Invalid direction. Use 'up' or 'down'"}
        
        # Update paddle position
        if player_id == self.player1_id:
            self.player1_paddle_y = new_y
        else:
            self.player2_paddle_y = new_y
        
        return {"success": True, "message": f"Paddle moved {direction}"}
    
    def update_ball(self) -> Dict[str, Any]:
        """Update ball position and handle collisions"""
        if self.game_over:
            return {"success": False, "message": "Game is over"}
        
        # Move ball
        new_x = self.ball_x + self.ball_vel_x
        new_y = self.ball_y + self.ball_vel_y
        
        # Handle top and bottom wall collisions
        if new_y <= 0:
            new_y = 0
            self.ball_vel_y = abs(self.ball_vel_y)  # Bounce down
        elif new_y >= self.field_height - 1:
            new_y = self.field_height - 1
            self.ball_vel_y = -abs(self.ball_vel_y)  # Bounce up
        
        # Handle paddle collisions
        collision_result = self.check_paddle_collision(new_x, new_y)
        
        if collision_result["collision"]:
            # Ball hit a paddle
            self.ball_vel_x = collision_result["new_vel_x"]
            self.ball_vel_y = collision_result["new_vel_y"]
            new_x = collision_result["new_x"]
            new_y = collision_result["new_y"]
            self.rally_count += 1
            message = f"Paddle hit! Rally: {self.rally_count}"
        else:
            # Check for scoring
            if new_x <= 0:
                # Player 2 scores
                self.player2_score += 1
                message = f"Player 2 scores! ({self.player1_score}-{self.player2_score})"
                self.reset_ball()
                self.check_game_over()
            elif new_x >= self.field_width - 1:
                # Player 1 scores
                self.player1_score += 1
                message = f"Player 1 scores! ({self.player1_score}-{self.player2_score})"
                self.reset_ball()
                self.check_game_over()
            else:
                # Normal ball movement
                self.ball_x = new_x
                self.ball_y = new_y
                message = "Ball moved"
        
        self.turn_count += 1
        
        return {"success": True, "message": message}
    
    def check_paddle_collision(self, ball_x: int, ball_y: int) -> Dict[str, Any]:
        """Check if ball collides with paddles"""
        # Player 1 paddle (left side, x = 1)
        if (ball_x <= 1 and self.ball_vel_x < 0 and
            self.player1_paddle_y <= ball_y < self.player1_paddle_y + self.paddle_height):
            
            # Calculate new velocity based on where ball hits paddle
            paddle_center = self.player1_paddle_y + self.paddle_height // 2
            hit_position = ball_y - paddle_center  # -1, 0, or 1
            
            return {
                "collision": True,
                "new_x": 2,  # Bounce ball away from paddle
                "new_y": ball_y,
                "new_vel_x": 1,  # Reverse x direction
                "new_vel_y": hit_position  # Y velocity based on hit position
            }
        
        # Player 2 paddle (right side, x = field_width - 2)
        elif (ball_x >= self.field_width - 2 and self.ball_vel_x > 0 and
              self.player2_paddle_y <= ball_y < self.player2_paddle_y + self.paddle_height):
            
            # Calculate new velocity based on where ball hits paddle
            paddle_center = self.player2_paddle_y + self.paddle_height // 2
            hit_position = ball_y - paddle_center  # -1, 0, or 1
            
            return {
                "collision": True,
                "new_x": self.field_width - 3,  # Bounce ball away from paddle
                "new_y": ball_y,
                "new_vel_x": -1,  # Reverse x direction
                "new_vel_y": hit_position  # Y velocity based on hit position
            }
        
        return {"collision": False}
    
    def reset_ball(self):
        """Reset ball to center after a score"""
        self.ball_x = self.field_width // 2
        self.ball_y = self.field_height // 2
        
        # Random starting direction
        self.ball_vel_x = random.choice([-1, 1])
        self.ball_vel_y = random.choice([-1, 0, 1])
        
        self.rally_count = 0
    
    def check_game_over(self):
        """Check if the game should end"""
        if self.player1_score >= self.max_score:
            self.game_over = True
            self.winner = self.player1_id
        elif self.player2_score >= self.max_score:
            self.game_over = True
            self.winner = self.player2_id
        
        # Also end game after 500 turns to prevent infinite games
        if self.turn_count >= 500:
            self.game_over = True
            if self.player1_score > self.player2_score:
                self.winner = self.player1_id
            elif self.player2_score > self.player1_score:
                self.winner = self.player2_id
            else:
                self.winner = None  # Tie (very unlikely in ping pong)
    
    def get_field_display(self) -> str:
        """Get a text representation of the ping pong field"""
        # Create empty field
        field = [[' ' for _ in range(self.field_width)] for _ in range(self.field_height)]
        
        # Draw borders
        for y in range(self.field_height):
            field[y][0] = '│'  # Left border
            field[y][self.field_width - 1] = '│'  # Right border
        
        # Draw top and bottom borders
        for x in range(self.field_width):
            if x == 0:
                field[0][x] = '┌'
                field[self.field_height - 1][x] = '└'
            elif x == self.field_width - 1:
                field[0][x] = '┐'
                field[self.field_height - 1][x] = '┘'
            else:
                field[0][x] = '─'
                field[self.field_height - 1][x] = '─'
        
        # Draw center line
        center_x = self.field_width // 2
        for y in range(1, self.field_height - 1):
            field[y][center_x] = '┊'
        
        # Draw Player 1 paddle (left side)
        for i in range(self.paddle_height):
            paddle_y = self.player1_paddle_y + i
            if 1 <= paddle_y < self.field_height - 1:
                field[paddle_y][1] = '█'
        
        # Draw Player 2 paddle (right side)
        for i in range(self.paddle_height):
            paddle_y = self.player2_paddle_y + i
            if 1 <= paddle_y < self.field_height - 1:
                field[paddle_y][self.field_width - 2] = '█'
        
        # Draw ball
        if 1 <= self.ball_y < self.field_height - 1 and 1 <= self.ball_x < self.field_width - 1:
            field[self.ball_y][self.ball_x] = '●'
        
        # Convert to string
        result = "```\n"
        for row in field:
            result += ''.join(row) + '\n'
        result += "```"
        
        return result
    
    def get_game_state(self) -> Dict[str, Any]:
        """Get the current game state"""
        return {
            "session_id": self.session_id,
            "player1_id": self.player1_id,
            "player2_id": self.player2_id,
            "player1_score": self.player1_score,
            "player2_score": self.player2_score,
            "player1_paddle_y": self.player1_paddle_y,
            "player2_paddle_y": self.player2_paddle_y,
            "ball_x": self.ball_x,
            "ball_y": self.ball_y,
            "ball_vel_x": self.ball_vel_x,
            "ball_vel_y": self.ball_vel_y,
            "rally_count": self.rally_count,
            "turn_count": self.turn_count,
            "game_over": self.game_over,
            "winner": self.winner,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_game_display(self) -> str:
        """Get a formatted display of the game"""
        if self.game_over:
            if self.winner:
                winner_name = "Player 1" if self.winner == self.player1_id else "Player 2"
                result = f"🏓 PING PONG - GAME OVER! 🏓\n"
                result += f"🏆 Winner: {winner_name}\n\n"
            else:
                result = f"🏓 PING PONG - TIE GAME! 🏓\n\n"
        else:
            result = f"🏓 PING PONG - MULTIPLAYER 🏓\n\n"
        
        result += f"📊 Score: Player 1: {self.player1_score} | Player 2: {self.player2_score}\n"
        result += f"🎯 Rally: {self.rally_count} hits\n"
        result += f"⏱️ Turn: {self.turn_count}\n"
        result += f"🎮 First to {self.max_score} wins!\n\n"
        
        if not self.game_over:
            result += "🎯 Commands:\n"
            result += "/up - Move paddle up\n"
            result += "/down - Move paddle down\n"
            result += "/tick - Advance ball (auto-moves)\n\n"
            
            result += "🏓 Ball Info:\n"
            result += f"Position: ({self.ball_x}, {self.ball_y})\n"
            result += f"Velocity: ({self.ball_vel_x}, {self.ball_vel_y})\n\n"
        
        return result
    
    def auto_move_paddle(self, player_id: int) -> Dict[str, Any]:
        """Auto-move paddle towards ball (AI behavior)"""
        if self.game_over:
            return {"success": False, "message": "Game is over"}
        
        if player_id == self.player1_id:
            paddle_y = self.player1_paddle_y
        elif player_id == self.player2_id:
            paddle_y = self.player2_paddle_y
        else:
            return {"success": False, "message": "Invalid player"}
        
        # Calculate paddle center
        paddle_center = paddle_y + self.paddle_height // 2
        
        # Move towards ball
        if self.ball_y < paddle_center:
            return self.move_paddle(player_id, "up")
        elif self.ball_y > paddle_center:
            return self.move_paddle(player_id, "down")
        else:
            return {"success": True, "message": "Paddle in optimal position"}
    
    def simulate_turn(self) -> Dict[str, Any]:
        """Simulate one complete turn (ball movement + optional AI)"""
        if self.game_over:
            return {"success": False, "message": "Game is over"}
        
        # Update ball position
        ball_result = self.update_ball()
        
        # Optional: Add simple AI for paddles if no recent player input
        # This could be enhanced to make paddles move towards the ball automatically
        
        return ball_result
    
    def get_ball_prediction(self) -> Tuple[int, int]:
        """Predict where the ball will be in the next few moves (for AI)"""
        # Simple prediction: assume ball continues in current direction
        future_x = self.ball_x + (self.ball_vel_x * 3)
        future_y = self.ball_y + (self.ball_vel_y * 3)
        
        # Clamp to field boundaries
        future_x = max(1, min(self.field_width - 2, future_x))
        future_y = max(1, min(self.field_height - 2, future_y))
        
        return future_x, future_y
    
    def to_json(self) -> str:
        """Convert game state to JSON for storage"""
        state = {
            "session_id": self.session_id,
            "player1_id": self.player1_id,
            "player2_id": self.player2_id,
            "player1_score": self.player1_score,
            "player2_score": self.player2_score,
            "player1_paddle_y": self.player1_paddle_y,
            "player2_paddle_y": self.player2_paddle_y,
            "ball_x": self.ball_x,
            "ball_y": self.ball_y,
            "ball_vel_x": self.ball_vel_x,
            "ball_vel_y": self.ball_vel_y,
            "rally_count": self.rally_count,
            "turn_count": self.turn_count,
            "max_score": self.max_score,
            "game_over": self.game_over,
            "winner": self.winner
        }
        return json.dumps(state)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'PingPongGame':
        """Create game instance from JSON"""
        state = json.loads(json_str)
        
        game = cls(state["session_id"], state["player1_id"], state["player2_id"])
        
        # Restore state
        game.player1_score = state["player1_score"]
        game.player2_score = state["player2_score"]
        game.player1_paddle_y = state["player1_paddle_y"]
        game.player2_paddle_y = state["player2_paddle_y"]
        game.ball_x = state["ball_x"]
        game.ball_y = state["ball_y"]
        game.ball_vel_x = state["ball_vel_x"]
        game.ball_vel_y = state["ball_vel_y"]
        game.rally_count = state["rally_count"]
        game.turn_count = state["turn_count"]
        game.max_score = state["max_score"]
        game.game_over = state["game_over"]
        game.winner = state["winner"]
        
        return game
