"""
Database models for the Sudoku game.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """A player of the Sudoku game."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: one user has many games
    games = db.relationship('Game', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Game(db.Model):
    """A single Sudoku game played by a user."""
    __tablename__ = 'games'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    difficulty = db.Column(db.String(20), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    solved = db.Column(db.Boolean, default=False, nullable=False)
    puzzle = db.Column(db.Text, nullable=True)  # JSON-encoded puzzle state

    def __repr__(self):
        return f'<Game {self.id} by {self.user.username} ({self.difficulty})>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'difficulty': self.difficulty,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'duration_formatted': self.format_duration(),
            'solved': self.solved,
        }

    def format_duration(self):
        """Return duration as human-readable string (e.g., '5m 30s')."""
        if self.duration_seconds is None:
            return 'N/A'
        minutes, seconds = divmod(self.duration_seconds, 60)
        if minutes > 0:
            return f'{minutes}m {seconds}s'
        return f'{seconds}s'