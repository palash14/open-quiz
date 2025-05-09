import logging
from logging.handlers import RotatingFileHandler
import os
from src.app.core.config import settings


def create_logger(name, log_file):
    # Ensure the log directory exists
    log_dir = settings.LOG_DIR_PATH
    os.makedirs(log_dir, exist_ok=True)

    # Set up a rotating log handler
    handler = RotatingFileHandler(
        os.path.join(log_dir, log_file), maxBytes=10485760, backupCount=5
    )
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    # Create and configure the logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger
