import os
import logging
from src.config.app_settings import AppSettings
from logging.handlers import RotatingFileHandler
from datetime import datetime

LOG_DIR = AppSettings.LOG_DIR
# Dynamically generate log file name based on current year and month
LOG_FILE = f"{datetime.now().strftime('%Y%m')}.log"
os.makedirs(AppSettings.LOG_DIR, exist_ok=True)

def setup_logging():
    log_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler = RotatingFileHandler(
        os.path.join(AppSettings.LOG_DIR, LOG_FILE), maxBytes=5 * 1024 * 1024, backupCount=5
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not any(isinstance(h, RotatingFileHandler) and h.baseFilename.endswith(LOG_FILE)
               for h in root_logger.handlers):
        root_logger.addHandler(file_handler)

    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(console_handler)

def cleanup_old_logs(months: int):
    """
    Delete log files in LOG_DIR that are older than the specified number of months.
    Log filenames must be in the format 'YYYYMM.log'.
    """
    threshold_date = datetime.now() - timedelta(days=months * 30)

    for filename in os.listdir(AppSettings.LOG_DIR):
        if filename.endswith(".log"):
            try:
                base_name = filename.split(".")[0]
                log_date = datetime.strptime(base_name, "%Y%m")
                if log_date < threshold_date:
                    file_path = os.path.join(AppSettings.LOG_DIR, filename)
                    os.remove(file_path)
                    print(f"Deleted old log file: {file_path}")
            except ValueError:
                # Skip files not matching the YYYYMM.log pattern
                continue