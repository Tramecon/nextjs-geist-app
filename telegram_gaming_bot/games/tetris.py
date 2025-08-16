import random
import json
from typing import List, Tuple, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TetrisGame:
    """Tetris game implementation for multiplayer Telegram bot"""
    
    # Tetris pieces (tetrominoes) represented as 4x4 grids
    PIECES = {
        'I': [
            ['....', '####', '....', '....'],
            ['..#.', '..#.', '..#.', '..#.'],
            ['....', '####', '....', '....'],
            ['..#.', '..#.', '..#.', '..#.']
        ],
        'O': [
            ['....', '.##.', '.##.', '....']
        ],
        'T': [
            ['....', '.#..', '###.', '....'],
            ['....', '.#..', '.##.', '.#..'],
            ['....', '....', '###.', '.#..'],
            ['....', '.#..', '##..', '.#..']
        ],
        'S': [
            ['....', '.##.', '##..', '....'],
            ['....', '.#..', '.##.', '..#.']
        ],
        'Z': [
            ['....', '##..', '.##.', '....'],
            ['....', '..#.', '.##.', '.#..']
        ],
        'J': [
            ['....', '.#..', '.#..', '##..'],
            ['....', '....', '#...', '###.'],
            ['....', '.##.', '.#..', '.#..'],
            ['....', '....', '###.', '..#.']
        ],
        'L': [
            ['....', '.#..', '.#..', '.##.'],
            ['....', '....', '###.', '#...'],
            ['....', '##..', '.#..', '.#..'],
            ['....', '....', '..#.', '###.']
        ]
    }
    
    def __init__(self, session_id: str, player1_id: int, player2_id: int):
        self.session_id = session_id
        self.player1_id = player1_id
        self.player2_id = player2_id
        
        # Game boards (10x20 for each player)
        self.board_width = 10
        self.board_height = 20
        
        # Initialize game state
        self.reset_game()
        
    def reset_game(self):
        """Reset the game to initial state"""
        self.player1_board = [['.' for _ in range(self.board_width)] for _ in range(self.board_height)]
        self.player2_board = [['.' for _ in range(self.board_width)] for _ in range(self.board_height)]
        
        self.player1_score = 0
        self.player2_score = 0
        
        self.player1_lines_cleared = 0
        self.player2_lines_cleared = 0
        
        self.player1_level = 1
        self.player2_level = 1
        
        # Current pieces
        self.player1_current_piece = self.get_random_piece()
        self.player2_current_piece = self.get_random_piece()
        
        # Next pieces
        self.player1_next_piece = self.get_random_piece()
        self.player2_next_piece = self.get_random_piece()
        
        # Piece positions
        self.player1_piece_pos = [0, 4]  # [row, col]
        self.player2_piece_pos = [0, 4]
        
        # Piece rotations
        self.player1_piece_rotation = 0
        self.player2_piece_rotation = 0
        
        self.game_over = False
        self.winner = None
        
        logger.info(f"Tetris game {self.session_id} reset")
    
    def get_random_piece(self) -> Dict[str, Any]:
        """Get a random tetris piece"""
        piece_type = random.choice(list(self.PIECES.keys()))
        return {
            'type': piece_type,
            'shapes': self.PIECES[piece_type]
        }
    
    def get_piece_shape(self, piece: Dict[str, Any], rotation: int) -> List[str]:
        """Get the shape of a piece at a specific rotation"""
        shapes = piece['shapes']
        return shapes[rotation % len(shapes)]
    
    def is_valid_position(self, board: List[List[str]], piece: Dict[str, Any], 
                         pos: List[int], rotation: int) -> bool:
        """Check if a piece position is valid"""
        shape = self.get_piece_shape(piece, rotation)
        row, col = pos
        
        for i, line in enumerate(shape):
            for j, cell in enumerate(line):
                if cell == '#':
                    new_row = row + i
                    new_col = col + j
                    
                    # Check boundaries
                    if (new_row < 0 or new_row >= self.board_height or 
                        new_col < 0 or new_col >= self.board_width):
                        return False
                    
                    # Check collision with existing pieces
                    if board[new_row][new_col] != '.':
                        return False
        
        return True
    
    def place_piece(self, board: List[List[str]], piece: Dict[str, Any], 
                   pos: List[int], rotation: int) -> List[List[str]]:
        """Place a piece on the board"""
        shape = self.get_piece_shape(piece, rotation)
        row, col = pos
        
        # Create a copy of the board
        new_board = [row[:] for row in board]
        
        for i, line in enumerate(shape):
            for j, cell in enumerate(line):
                if cell == '#':
                    new_row = row + i
                    new_col = col + j
                    if 0 <= new_row < self.board_height and 0 <= new_col < self.board_width:
                        new_board[new_row][new_col] = piece['type']
        
        return new_board
    
    def clear_lines(self, board: List[List[str]]) -> Tuple[List[List[str]], int]:
        """Clear completed lines and return new board and lines cleared"""
        lines_cleared = 0
        new_board = []
        
        for row in board:
            if '.' not in row:  # Line is complete
                lines_cleared += 1
            else:
                new_board.append(row)
        
        # Add empty lines at the top
        while len(new_board) < self.board_height:
            new_board.insert(0, ['.' for _ in range(self.board_width)])
        
        return new_board, lines_cleared
    
    def calculate_score(self, lines_cleared: int, level: int) -> int:
        """Calculate score based on lines cleared and level"""
        if lines_cleared == 0:
            return 0
        
        base_scores = {1: 40, 2: 100, 3: 300, 4: 1200}
        base_score = base_scores.get(lines_cleared, 0)
        return base_score * (level + 1)
    
    def move_piece(self, player_id: int, direction: str) -> Dict[str, Any]:
        """Move a player's piece"""
        if self.game_over:
            return {"success": False, "message": "Game is over"}
        
        if player_id == self.player1_id:
            board = self.player1_board
            piece = self.player1_current_piece
            pos = self.player1_piece_pos
            rotation = self.player1_piece_rotation
        elif player_id == self.player2_id:
            board = self.player2_board
            piece = self.player2_current_piece
            pos = self.player2_piece_pos
            rotation = self.player2_piece_rotation
        else:
            return {"success": False, "message": "Invalid player"}
        
        new_pos = pos[:]
        new_rotation = rotation
        
        if direction == "left":
            new_pos[1] -= 1
        elif direction == "right":
            new_pos[1] += 1
        elif direction == "down":
            new_pos[0] += 1
        elif direction == "rotate":
            new_rotation = (rotation + 1) % len(piece['shapes'])
        else:
            return {"success": False, "message": "Invalid direction"}
        
        # Check if the new position is valid
        if self.is_valid_position(board, piece, new_pos, new_rotation):
            # Update position
            if player_id == self.player1_id:
                self.player1_piece_pos = new_pos
                self.player1_piece_rotation = new_rotation
            else:
                self.player2_piece_pos = new_pos
                self.player2_piece_rotation = new_rotation
            
            return {"success": True, "message": "Piece moved"}
        else:
            # If moving down failed, place the piece
            if direction == "down":
                return self.place_current_piece(player_id)
            else:
                return {"success": False, "message": "Invalid move"}
    
    def place_current_piece(self, player_id: int) -> Dict[str, Any]:
        """Place the current piece and spawn a new one"""
        if player_id == self.player1_id:
            board = self.player1_board
            piece = self.player1_current_piece
            pos = self.player1_piece_pos
            rotation = self.player1_piece_rotation
            next_piece = self.player1_next_piece
        elif player_id == self.player2_id:
            board = self.player2_board
            piece = self.player2_current_piece
            pos = self.player2_piece_pos
            rotation = self.player2_piece_rotation
            next_piece = self.player2_next_piece
        else:
            return {"success": False, "message": "Invalid player"}
        
        # Place the piece
        new_board = self.place_piece(board, piece, pos, rotation)
        
        # Clear lines
        new_board, lines_cleared = self.clear_lines(new_board)
        
        # Calculate score
        if player_id == self.player1_id:
            level = self.player1_level
            score_gained = self.calculate_score(lines_cleared, level)
            self.player1_board = new_board
            self.player1_score += score_gained
            self.player1_lines_cleared += lines_cleared
            
            # Level up every 10 lines
            self.player1_level = (self.player1_lines_cleared // 10) + 1
            
            # Spawn new piece
            self.player1_current_piece = next_piece
            self.player1_next_piece = self.get_random_piece()
            self.player1_piece_pos = [0, 4]
            self.player1_piece_rotation = 0
            
            # Check game over
            if not self.is_valid_position(new_board, self.player1_current_piece, 
                                        self.player1_piece_pos, self.player1_piece_rotation):
                self.game_over = True
                self.winner = self.player2_id
        else:
            level = self.player2_level
            score_gained = self.calculate_score(lines_cleared, level)
            self.player2_board = new_board
            self.player2_score += score_gained
            self.player2_lines_cleared += lines_cleared
            
            # Level up every 10 lines
            self.player2_level = (self.player2_lines_cleared // 10) + 1
            
            # Spawn new piece
            self.player2_current_piece = next_piece
            self.player2_next_piece = self.get_random_piece()
            self.player2_piece_pos = [0, 4]
            self.player2_piece_rotation = 0
            
            # Check game over
            if not self.is_valid_position(new_board, self.player2_current_piece, 
                                        self.player2_piece_pos, self.player2_piece_rotation):
                self.game_over = True
                self.winner = self.player1_id
        
        return {
            "success": True, 
            "message": f"Piece placed, {lines_cleared} lines cleared, {score_gained} points gained",
            "lines_cleared": lines_cleared,
            "score_gained": score_gained
        }
    
    def drop_piece(self, player_id: int) -> Dict[str, Any]:
        """Drop piece to the bottom"""
        while True:
            result = self.move_piece(player_id, "down")
            if not result["success"]:
                break
        return {"success": True, "message": "Piece dropped"}
    
    def get_board_display(self, player_id: int) -> str:
        """Get a text representation of the player's board"""
        if player_id == self.player1_id:
            board = self.player1_board
            piece = self.player1_current_piece
            pos = self.player1_piece_pos
            rotation = self.player1_piece_rotation
        elif player_id == self.player2_id:
            board = self.player2_board
            piece = self.player2_current_piece
            pos = self.player2_piece_pos
            rotation = self.player2_piece_rotation
        else:
            return "Invalid player"
        
        # Create a copy of the board with the current piece
        display_board = [row[:] for row in board]
        
        # Add current piece to display
        if not self.game_over:
            shape = self.get_piece_shape(piece, rotation)
            row, col = pos
            
            for i, line in enumerate(shape):
                for j, cell in enumerate(line):
                    if cell == '#':
                        new_row = row + i
                        new_col = col + j
                        if (0 <= new_row < self.board_height and 
                            0 <= new_col < self.board_width and 
                            display_board[new_row][new_col] == '.'):
                            display_board[new_row][new_col] = '●'
        
        # Convert to string
        result = "```\n"
        result += "┌" + "─" * self.board_width + "┐\n"
        
        for row in display_board:
            result += "│"
            for cell in row:
                if cell == '.':
                    result += " "
                elif cell == '●':
                    result += "●"
                else:
                    result += "█"
            result += "│\n"
        
        result += "└" + "─" * self.board_width + "┘\n"
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
            "player1_level": self.player1_level,
            "player2_level": self.player2_level,
            "player1_lines": self.player1_lines_cleared,
            "player2_lines": self.player2_lines_cleared,
            "game_over": self.game_over,
            "winner": self.winner,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_game_display(self) -> str:
        """Get a formatted display of both players' games"""
        if self.game_over:
            winner_name = "Player 1" if self.winner == self.player1_id else "Player 2"
            result = f"🎮 TETRIS - GAME OVER! 🎮\n"
            result += f"🏆 Winner: {winner_name}\n\n"
        else:
            result = f"🎮 TETRIS - MULTIPLAYER 🎮\n\n"
        
        result += f"👤 Player 1 Score: {self.player1_score} (Level {self.player1_level})\n"
        result += f"👤 Player 2 Score: {self.player2_score} (Level {self.player2_level})\n"
        result += f"📊 Lines: P1({self.player1_lines_cleared}) P2({self.player2_lines_cleared})\n\n"
        
        if not self.game_over:
            result += "🎯 Commands:\n"
            result += "/left - Move left\n"
            result += "/right - Move right\n"
            result += "/down - Move down\n"
            result += "/rotate - Rotate piece\n"
            result += "/drop - Drop piece\n\n"
        
        return result
    
    def to_json(self) -> str:
        """Convert game state to JSON for storage"""
        state = {
            "session_id": self.session_id,
            "player1_id": self.player1_id,
            "player2_id": self.player2_id,
            "player1_board": self.player1_board,
            "player2_board": self.player2_board,
            "player1_score": self.player1_score,
            "player2_score": self.player2_score,
            "player1_lines_cleared": self.player1_lines_cleared,
            "player2_lines_cleared": self.player2_lines_cleared,
            "player1_level": self.player1_level,
            "player2_level": self.player2_level,
            "player1_current_piece": self.player1_current_piece,
            "player2_current_piece": self.player2_current_piece,
            "player1_next_piece": self.player1_next_piece,
            "player2_next_piece": self.player2_next_piece,
            "player1_piece_pos": self.player1_piece_pos,
            "player2_piece_pos": self.player2_piece_pos,
            "player1_piece_rotation": self.player1_piece_rotation,
            "player2_piece_rotation": self.player2_piece_rotation,
            "game_over": self.game_over,
            "winner": self.winner
        }
        return json.dumps(state)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'TetrisGame':
        """Create game instance from JSON"""
        state = json.loads(json_str)
        
        game = cls(state["session_id"], state["player1_id"], state["player2_id"])
        
        # Restore state
        game.player1_board = state["player1_board"]
        game.player2_board = state["player2_board"]
        game.player1_score = state["player1_score"]
        game.player2_score = state["player2_score"]
        game.player1_lines_cleared = state["player1_lines_cleared"]
        game.player2_lines_cleared = state["player2_lines_cleared"]
        game.player1_level = state["player1_level"]
        game.player2_level = state["player2_level"]
        game.player1_current_piece = state["player1_current_piece"]
        game.player2_current_piece = state["player2_current_piece"]
        game.player1_next_piece = state["player1_next_piece"]
        game.player2_next_piece = state["player2_next_piece"]
        game.player1_piece_pos = state["player1_piece_pos"]
        game.player2_piece_pos = state["player2_piece_pos"]
        game.player1_piece_rotation = state["player1_piece_rotation"]
        game.player2_piece_rotation = state["player2_piece_rotation"]
        game.game_over = state["game_over"]
        game.winner = state["winner"]
        
        return game
