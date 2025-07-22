# rfiprocessor/utils/logger.py

import logging
from config.config import Config

def get_logger(name: str, log_file: str = "app.log") -> logging.Logger:
    logger = logging.getLogger(name)

    # Ensure handlers are not added multiple times if get_logger is called repeatedly
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler
        file_handler = logging.FileHandler(Config.LOG_FILE_PATH)
        file_formatter = logging.Formatter(Config.LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        logger.setLevel(logging.DEBUG)
    return logger