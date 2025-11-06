"""Task scheduling and background jobs."""
from datetime import datetime, timedelta
import logging
import os
import shutil

logger = logging.getLogger(__name__)

def clear_previous_sessions(upload_folder, zip_folder):
    """Clean up old files and folders."""
    logger.info("Starting cleanup of previous sessions")
    
    for folder in [upload_folder, zip_folder]:
        if not os.path.exists(folder):
            continue
            
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    # Check if file is older than 24 hours
                    file_age = datetime.now() - datetime.fromtimestamp(os.path.getctime(file_path))
                    if file_age > timedelta(hours=24):
                        os.unlink(file_path)
                        logger.info(f"Deleted old file: {file_path}")
                elif os.path.isdir(file_path):
                    # Check if directory is older than 24 hours
                    dir_age = datetime.now() - datetime.fromtimestamp(os.path.getctime(file_path))
                    if dir_age > timedelta(hours=24):
                        shutil.rmtree(file_path)
                        logger.info(f"Deleted old directory: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {e}")

def setup_scheduler(app):
    """Initialize and start the background scheduler."""
    from apscheduler.schedulers.background import BackgroundScheduler
    
    scheduler = BackgroundScheduler()
    
    def scheduled_cleanup():
        """Wrapper to pass app context to cleanup function"""
        with app.app_context():
            upload_folder = os.path.join(app.root_path, 'static', 'output')
            zip_folder = os.path.join(app.root_path, 'static', 'zips')
            clear_previous_sessions(upload_folder, zip_folder)
    
    # Run cleanup every 24 hours
    scheduler.add_job(
        func=scheduled_cleanup,
        trigger="interval",
        hours=24,
        id='cleanup_old_files',
        replace_existing=True
    )
    
    # Also run cleanup on startup (after 1 minute)
    scheduler.add_job(
        func=scheduled_cleanup,
        trigger="date",
        run_date=datetime.now() + timedelta(minutes=1),
        id='cleanup_on_startup'
    )
    
    scheduler.start()
    logger.info("Scheduler started successfully")
    
    # Shutdown scheduler when app stops
    import atexit
    atexit.register(lambda: scheduler.shutdown())