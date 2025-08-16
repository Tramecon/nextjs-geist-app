import random
import json
from typing import List, Tuple, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SnakeGame:
    """Snake game implementation for multiplayer Telegram bot"""
    
    def __init__(self, session_id: str, player1_id: int, player2_id: int):
        self.session_id = session_id
        self.player1_id = player1_id
        self.player2_id = player2_id
        
        # Game board dimensions
        self.board_width = 15
        self.board_height = 15
        
        # Initialize game state
        self.reset_game()
        
    def reset_game(self):
        """Reset the game to initial state"""
        # Player 1 snake (starts from left side)
        self.player1_snake = [(7, 2), (7, 1), (7, 0)]  # Head at (7, 2)
        self.player1_direction = "right"
        self.player1_score = 0
        self.player1_alive = True
        
        # Player 2 snake (starts from right side)
        self.player2_snake = [(7, 12), (7, 13), (7, 14)]  # Head at (7, 12)
        self.player2_direction = "left"
        self.player2_score = 0
        self.player2_alive = True
        
        # Food positions
        self.food_positions = []
        self.spawn_food()
        self.spawn_food()  # Start with 2 food items
        
        self.game_over = False
        self.winner = None
        self.turn_count = 0
        
        logger.info(f"Snake game {self.session_id} reset")
    
    def spawn_food(self):
        """Spawn a new food item at a random empty position"""
        max_attempts = 50
        attempts = 0
        
        while attempts < max_attempts:
            x = random.randint(0, self.board_width - 1)
            y = random.randint(0, self.board_height - 1)
            
            # Check if position is empty
            if ((x, y) not in self.player1_snake and 
                (x, y) not in self.player2_snake and 
                (x, y) not in self.food_positions):
                self.food_positions.append((x, y))
                return True
            
            attempts += 1
        
        return False  # Could not spawn food
    
    def is_valid_position(self, x: int, y: int) -> bool:
        """Check if a position is within the board boundaries"""
        return 0 <= x < self.board_height and 0 <= y < self.board_width
    
    def move_snake(self, player_id: int, direction: str) -> Dict[str, Any]:
        """Move a player's snake in the specified direction"""
        if self.game_over:
            return {"success": False, "message": "Game is over"}
        
        if player_id == self.player1_id:
            if not self.player1_alive:
                return {"success": False, "message": "Player 1 is eliminated"}
            snake = self.player1_snake
            current_direction = self.player1_direction
        elif player_id == self.player2_id:
            if not self.player2_alive:
                return {"success": False, "message": "Player 2 is eliminated"}
            snake = self.player2_snake
            current_direction = self.player2_direction
        else:
            return {"success": False, "message": "Invalid player"}
        
        # Validate direction change (can't reverse directly)
        opposite_directions = {
            "up": "down", "down": "up",
            "left": "right", "right": "left"
        }
        
        if direction == opposite_directions.get(current_direction):
            return {"success": False, "message": "Cannot reverse direction"}
        
        # Update direction
        if player_id == self.player1_id:
            self.player1_direction = direction
        else:
            self.player2_direction = direction
        
        return {"success": True, "message": f"Direction changed to {direction}"}
    
    def update_game_state(self) -> Dict[str, Any]:
        """Update the game state for one turn"""
        if self.game_over:
            return {"success": False, "message": "Game is over"}
        
        results = []
        
        # Move Player 1
        if self.player1_alive:
            result1 = self.move_player_snake(self.player1_id)
            results.append(f"P1: {result1['message']}")
        
        # Move Player 2
        if self.player2_alive:
            result2 = self.move_player_snake(self.player2_id)
            results.append(f"P2: {result2['message']}")
        
        # Check game over conditions
        self.check_game_over()
        
        self.turn_count += 1
        
        return {
            "success": True,
            "message": " | ".join(results),
            "turn": self.turn_count
        }
    
    def move_player_snake(self, player_id: int) -> Dict[str, Any]:
        """Move a specific player's snake"""
        if player_id == self.player1_id:
            snake = self.player1_snake
            direction = self.player1_direction
        elif player_id == self.player2_id:
            snake = self.player2_snake
            direction = self.player2_direction
        else:
            return {"success": False, "message": "Invalid player"}
        
        # Calculate new head position
        head_x, head_y = snake[0]
        
        if direction == "up":
            new_head = (head_x - 1, head_y)
        elif direction == "down":
            new_head = (head_x + 1, head_y)
        elif direction == "left":
            new_head = (head_x, head_y - 1)
        elif direction == "right":
            new_head = (head_x, head_y + 1)
        else:
            return {"success": False, "message": "Invalid direction"}
        
        # Check wall collision
        if not self.is_valid_position(new_head[0], new_head[1]):
            if player_id == self.player1_id:
                self.player1_alive = False
            else:
                self.player2_alive = False
            return {"success": False, "message": "Hit wall - eliminated!"}
        
        # Check self collision
        if new_head in snake:
            if player_id == self.player1_id:
                self.player1_alive = False
            else:
                self.player2_alive = False
            return {"success": False, "message": "Hit self - eliminated!"}
        
        # Check collision with other snake
        other_snake = self.player2_snake if player_id == self.player1_id else self.player1_snake
        if new_head in other_snake:
            if player_id == self.player1_id:
                self.player1_alive = False
            else:
                self.player2_alive = False
            return {"success": False, "message": "Hit opponent - eliminated!"}
        
        # Move snake
        snake.insert(0, new_head)
        
        # Check food collision
        food_eaten = False
        if new_head in self.food_positions:
            self.food_positions.remove(new_head)
            food_eaten = True
            
            # Increase score
            if player_id == self.player1_id:
                self.player1_score += 10
            else:
                self.player2_score += 10
            
            # Spawn new food
            self.spawn_food()
        
        # Remove tail if no food eaten
        if not food_eaten:
            snake.pop()
        
        message = "Moved"
        if food_eaten:
            message += " and ate food (+10 points)"
        
        return {"success": True, "message": message}
    
    def check_game_over(self):
        """Check if the game should end"""
        if not self.player1_alive and not self.player2_alive:
            self.game_over = True
            # Winner is the one with higher score, or tie
            if self.player1_score > self.player2_score:
                self.winner = self.player1_id
            elif self.player2_score > self.player1_score:
                self.winner = self.player2_id
            else:
                self.winner = None  # Tie
        elif not self.player1_alive:
            self.game_over = True
            self.winner = self.player2_id
        elif not self.player2_alive:
            self.game_over = True
            self.winner = self.player1_id
        
        # Game also ends after 200 turns to prevent infinite games
        if self.turn_count >= 200:
            self.game_over = True
            if self.player1_score > self.player2_score:
                self.winner = self.player1_id
            elif self.player2_score > self.player1_score:
                self.winner = self.player2_id
            else:
                self.winner = None  # Tie
    
    def get_board_display(self) -> str:
        """Get a text representation of the game board"""
        # Create empty board
        board = [['.' for _ in range(self.board_width)] for _ in range(self.board_height)]
        
        # Place food
        for x, y in self.food_positions:
            board[x][y] = '🍎'
        
        # Place Player 1 snake (blue)
        if self.player1_alive:
            for i, (x, y) in enumerate(self.player1_snake):
                if i == 0:  # Head
                    board[x][y] = '🔵'
                else:  # Body
                    board[x][y] = '🟦'
        
        # Place Player 2 snake (red)
        if self.player2_alive:
            for i, (x, y) in enumerate(self.player2_snake):
                if i == 0:  # Head
                    board[x][y] = '🔴'
                else:  # Body
                    board[x][y] = '🟥'
        
        # Convert to string
        result = "```\n"
        result += "┌" + "─" * (self.board_width * 2) + "┐\n"
        
        for row in board:
            result += "│"
            for cell in row:
                if cell == '.':
                    result += "  "
                elif cell == '🍎':
                    result += "🍎"
                elif cell == '🔵':
                    result += "🔵"
                elif cell == '🔴':
                    result += "🔴"
                elif cell == '🟦':
                    result += "🟦"
                elif cell == '🟥':
                    result += "🟥"
            result += "│\n"
        
        result += "└" + "─" * (self.board_width * 2) + "┘\n"
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
            "player1_alive": self.player1_alive,
            "player2_alive": self.player2_alive,
            "player1_length": len(self.player1_snake),
            "player2_length": len(self.player2_snake),
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
                result = f"🐍 SNAKE - GAME OVER! 🐍\n"
                result += f"🏆 Winner: {winner_name}\n\n"
            else:
                result = f"🐍 SNAKE - TIE GAME! 🐍\n\n"
        else:
            result = f"🐍 SNAKE - MULTIPLAYER 🐍\n\n"
        
        p1_status = "🔵 Alive" if self.player1_alive else "💀 Eliminated"
        p2_status = "🔴 Alive" if self.player2_alive else "💀 Eliminated"
        
        result += f"👤 Player 1: {self.player1_score} pts, Length: {len(self.player1_snake)} {p1_status}\n"
        result += f"👤 Player 2: {self.player2_score} pts, Length: {len(self.player2_snake)} {p2_status}\n"
        result += f"🎯 Turn: {self.turn_count}/200\n"
        result += f"🍎 Food: {len(self.food_positions)} items\n\n"
        
        if not self.game_over:
            result += "🎯 Commands:\n"
            result += "/up - Move up\n"
            result += "/down - Move down\n"
            result += "/left - Move left\n"
            result += "/right - Move right\n"
            result += "/tick - Advance one turn\n\n"
        
        return result
    
    def auto_move(self, player_id: int) -> Dict[str, Any]:
        """Auto-move for AI or when player doesn't respond"""
        if player_id == self.player1_id:
            snake = self.player1_snake
            direction = self.player1_direction
        elif player_id == self.player2_id:
            snake = self.player2_snake
            direction = self.player2_direction
        else:
            return {"success": False, "message": "Invalid player"}
        
        # Try to continue in current direction
        head_x, head_y = snake[0]
        
        if direction == "up":
            new_head = (head_x - 1, head_y)
        elif direction == "down":
            new_head = (head_x + 1, head_y)
        elif direction == "left":
            new_head = (head_x, head_y - 1)
        elif direction == "right":
            new_head = (head_x, head_y + 1)
        
        # Check if current direction is safe
        if (self.is_valid_position(new_head[0], new_head[1]) and
            new_head not in snake and
            new_head not in (self.player2_snake if player_id == self.player1_id else self.player1_snake)):
            return {"success": True, "message": "Continued in current direction"}
        
        # Try other directions
        directions = ["up", "down", "left", "right"]
        opposite = {"up": "down", "down": "up", "left": "right", "right": "left"}
        
        for new_direction in directions:
            if new_direction == opposite.get(direction):
                continue  # Can't reverse
            
            if new_direction == "up":
                test_head = (head_x - 1, head_y)
            elif new_direction == "down":
                test_head = (head_x + 1, head_y)
            elif new_direction == "left":
                test_head = (head_x, head_y - 1)
            elif new_direction == "right":
                test_head = (head_x, head_y + 1)
            
            if (self.is_valid_position(test_head[0], test_head[1]) and
                test_head not in snake and
                test_head not in (self.player2_snake if player_id == self.player1_id else self.player1_snake)):
                
                # Change direction
                if player_id == self.player1_id:
                    self.player1_direction = new_direction
                else:
                    self.player2_direction = new_direction
                
                return {"success": True, "message": f"Changed direction to {new_direction}"}
        
        # No safe direction found
        return {"success": False, "message": "No safe direction available"}
    
    def to_json(self) -> str:
        """Convert game state to JSON for storage"""
        state = {
            "session_id": self.session_id,
            "player1_id": self.player1_id,
            "player2_id": self.player2_id,
            "player1_snake": self.player1_snake,
            "player2_snake": self.player2_snake,
            "player1_direction": self.player1_direction,
            "player2_direction": self.player2_direction,
            "player1_score": self.player1_score,
            "player2_score": self.player2_score,
            "player1_alive": self.player1_alive,
            "player2_alive": self.player2_alive,
            "food_positions": self.food_positions,
            "turn_count": self.turn_count,
            "game_over": self.game_over,
            "winner": self.winner
        }
        return json.dumps(state)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'SnakeGame':
        """Create game instance from JSON"""
        state = json.loads(json_str)
        
        game = cls(state["session_id"], state["player1_id"], state["player2_id"])
        
        # Restore state
        game.player1_snake = state["player1_snake"]
        game.player2_snake = state["player2_snake"]
        game.player1_direction = state["player1_direction"]
        game.player2_direction = state["player2_direction"]
        game.player1_score = state["player1_score"]
        game.player2_score = state["player2_score"]
        game.player1_alive = state["player1_alive"]
        game.player2_alive = state["player2_alive"]
        game.food_positions = state["food_positions"]
        game.turn_count = state["turn_count"]
        game.game_over = state["game_over"]
        game.winner = state["winner"]
        
        return game
