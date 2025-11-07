"""Flask application configuration and initialization."""
import os
import logging
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from concurrent.futures import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from .config import Config
from .routes import register_routes
from .tasks import setup_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    app.cache = Cache(app)
    app.executor = ThreadPoolExecutor(max_workers=3)

    # Configure folders
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['ZIP_FOLDER'], exist_ok=True)

    # Register routes
    register_routes(app,limiter)

    # Setup scheduler
    setup_scheduler(app)

    return app