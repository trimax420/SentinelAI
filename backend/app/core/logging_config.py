import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Ensure log directory exists
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Log file path
log_file = os.path.join(log_dir, 'app.log')

def setup_logging():
    """Sets up the application logging configuration."""
    
    # Configure the root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5), # Rotate at 10MB, keep 5 backups
            logging.StreamHandler(sys.stdout) # Also log to console
        ]
    )
    
    # Set higher level for noisy libraries if needed
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info("Logging configured.")

# Call setup on import
setup_logging() 