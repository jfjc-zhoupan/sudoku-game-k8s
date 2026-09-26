"""Web Sudoku app with database for game records."""

import os
from datetime import datetime
from flask import Flask, jsonify, render_template, request, redirect, url_for
from engine import DIFFICULTY, new_puzzle
from models import db, User, Game
from version import __version__, __app_name__, __description__


def create_app():
    """Application factory pattern."""
    app = Flask(__name__)

    # Database configuration
    # Use SQLite for local dev, PostgreSQL for production
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///sudoku.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,       # Verify connections before use
        'pool_recycle': 300,         # Recycle connections every 5 minutes
    }

    # Initialize database
    db.init_app(app)

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    return app


app = create_app()


# ============================================================
# Helper: Get or create the current user (simplified - no auth yet)
# ============================================================
def get_or_create_user(username='guest'):
    """Get existing user or create a new one."""
    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()
    return user


# ============================================================
# Page Routes
# ============================================================

@app.get("/")
def index():
    """Home page with New Game and Game Records buttons."""
    return render_template("home.html", version=__version__, app_name=__app_name__)


@app.get("/new-game")
def new_game_page():
    """New game page with difficulty selection."""
    return render_template(
        "index.html",
        difficulties=list(DIFFICULTY.keys()),
        version=__version__,
    )


@app.get("/records")
def records_page():
    """Show all past games."""
    user = get_or_create_user('guest')
    games = Game.query.filter_by(user_id=user.id).order_by(Game.started_at.desc()).all()
    return render_template(
        "records.html",
        games=games,
        version=__version__,
    )


# ============================================================
# API Routes
# ============================================================

@app.post("/api/new")
def api_new():
    """Create a new game and return the puzzle."""
    data = request.get_json(silent=True) or {}
    difficulty = data.get('difficulty', 'Easy')
    if difficulty not in DIFFICULTY:
        difficulty = 'Easy'

    puzzle, solution = new_puzzle(difficulty)
    empty = sum(1 for row in puzzle for cell in row if cell == 0)

    # ✅ Save game to database
    user = get_or_create_user('guest')
    game = Game(
        user_id=user.id,
        difficulty=difficulty,
        started_at=datetime.utcnow(),
        solved=False,
    )
    db.session.add(game)
    db.session.commit()

    return jsonify({
        'game_id': game.id,
        'difficulty': difficulty,
        'puzzle': puzzle,
        'solution': solution,
        'empty': empty,
        'started_at': game.started_at.isoformat(),
    })


@app.post("/api/complete")
def api_complete():
    """Mark a game as complete and record the duration."""
    data = request.get_json(silent=True) or {}
    game_id = data.get('game_id')
    solved = data.get('solved', False)

    if not game_id:
        return jsonify({'error': 'game_id is required'}), 400

    game = Game.query.get(game_id)
    if not game:
        return jsonify({'error': 'Game not found'}), 404

    # ✅ Record completion time and duration
    game.completed_at = datetime.utcnow()
    game.duration_seconds = int((game.completed_at - game.started_at).total_seconds())
    game.solved = solved
    db.session.commit()

    return jsonify({
        'success': True,
        'game': game.to_dict(),
    })


@app.get("/api/records")
def api_records():
    """Get all game records as JSON."""
    user = get_or_create_user('guest')
    games = Game.query.filter_by(user_id=user.id).order_by(Game.started_at.desc()).all()
    return jsonify([g.to_dict() for g in games])


@app.get("/api/version")
def api_version():
    return jsonify({
        'version': __version__,
        'app_name': __app_name__,
    })


@app.get("/health")
def health():
    """Health check for Kubernetes."""
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
