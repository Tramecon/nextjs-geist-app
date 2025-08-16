"""
Games package for the Telegram Gaming Bot
Contains implementations of Tetris, Snake, and Ping Pong games
"""

from .tetris import TetrisGame
from .snake import SnakeGame
from .ping_pong import PingPongGame

__all__ = ['TetrisGame', 'SnakeGame', 'PingPongGame']
