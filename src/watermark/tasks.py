"""Task scheduling and background jobs."""
from datetime import datetime, timedelta
import logging
import os
import shutil

logger = logging.getLogger(__name__)

def clear_previous_sessions(app=None):
    """Clean up old files and folders."""
    if app is None:
        return
    
    logger.info("Starting cleanup of previous sessions")
    for folder in [app.config['UPLOAD_FOLDER'], app.config['ZIP_FOLDER']]:
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    if datetime.now() - datetime.fromtimestamp(os.path.getctime(file_path)) > timedelta(hours=24):
                        os.unlink(file_path)
                elif os.path.isdir(file_path):
                    if datetime.now() - datetime.fromtimestamp(os.path.getctime(file_path)) > timedelta(hours=24):
                        shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {e}")

def setup_scheduler(app):
    """Initialize and start the background scheduler."""
    from apscheduler.schedulers.background import BackgroundScheduler
    
    scheduler = BackgroundScheduler()
    
    def scheduled_cleanup():
        """Wrapper to pass app context to clear_previous_sessions"""
        clear_previous_sessions(app)
        logger.info("Starting cleanup of previous sessions")
        for folder in [app.config['UPLOAD_FOLDER'], app.config['ZIP_FOLDER']]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        # Check if file is older than 24 hours
                        if datetime.now() - datetime.fromtimestamp(os.path.getctime(file_path)) > timedelta(hours=24):
                            os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        if datetime.now() - datetime.fromtimestamp(os.path.getctime(file_path)) > timedelta(hours=24):
                            shutil.rmtree(file_path)
                except Exception as e:
                    logger.error(f"Failed to delete {file_path}: {e}")
    
    scheduler.add_job(func=clear_previous_sessions, trigger="interval", hours=24)
    scheduler.start()