import logging
import os
from pathlib import Path

def setup_logging(log_level=logging.INFO, log_file=None, enable_metrics_server=False, metrics_port=None):
    """Set up logging configuration."""
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Create a console handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)

    # Create a formatter and set it for the console handler
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    # Add the console handler to the logger
    logger.addHandler(ch)

    # If a log file is specified, set up file logging
    if log_file:
        log_file_path = Path(log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)  # Create directory if it doesn't exist
        fh = logging.FileHandler(log_file_path)
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    # Optionally set up metrics server logging
    if enable_metrics_server and metrics_port:
        # Placeholder for metrics server setup
        pass

    return logger

def get_logger(name):
    """Get a logger with the specified name."""
    return logging.getLogger(name)