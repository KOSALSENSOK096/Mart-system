# Application Configuration
APP_NAME = "Mart Manager"
APP_VERSION = "1.0.0"

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'mart_db',
    'port': 3306
}

# Default Admin Account
DEFAULT_ADMIN = {
    'username': 'admin',
    'password': 'admin123',
    'role': 'admin'
}

# Receipt Configuration
RECEIPT_WIDTH = 90  # mm (updated for new design)
RECEIPT_MARGIN = 5  # mm
RECEIPT_FOOTER = "Thank you for shopping with us!"  # Removed heart emoji

# Company Information
COMPANY_NAME = "Mart Manager"
COMPANY_ADDRESS = {
    'street': "123 Main Street",
    'city': "City",
    'state': "State",
    'zip': "12345",
    'country': "Country"
}
COMPANY_CONTACT = {
    'phone': "(555) 123-4567",
    'email': "support@martmanager.com",
    'website': "www.martmanager.com"
}

# Store Policy
RETURN_POLICY = "Returns accepted within 30 days with original receipt"
STORE_HOURS = "Mon-Sat: 9:00 AM - 9:00 PM, Sun: 10:00 AM - 6:00 PM"

# Application Settings
CURRENCY_SYMBOL = "$"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"

# File Paths
ASSETS_DIR = "assets"
LOGS_DIR = "logs"
RECEIPTS_DIR = "receipts"
BACKUP_DIR = "backups"
TEMP_DIR = "temp"

# Create necessary directories
import os

DIRS = [ASSETS_DIR, LOGS_DIR, RECEIPTS_DIR, BACKUP_DIR, TEMP_DIR]

for directory in DIRS:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Security settings
SECRET_KEY = "your-secret-key-here"
PASSWORD_SALT = "your-salt-here"

# UI Theme settings
THEME = {
    'appearance_mode': 'dark',
    'color_theme': 'blue'
}

# Receipt Colors
RECEIPT_COLORS = {
    'primary': (41, 128, 185),      # Modern blue
    'accent': (52, 152, 219),       # Lighter blue
    'success': (46, 204, 113),      # Green
    'warning': (241, 196, 15),      # Yellow
    'error': (231, 76, 60),         # Red
    'text': (0, 0, 0),              # Black
    'text_secondary': (128, 128, 128), # Gray
    'background': (255, 255, 255)    # White
}

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout'  # Use stdout instead of stderr
        },
        'file': {
            'level': 'DEBUG',
            'formatter': 'detailed',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_DIR, 'mart_manager.log'),
            'mode': 'a',
            'encoding': 'utf-8'  # Explicitly set UTF-8 encoding
        }
    },
    'loggers': {
        '': {  # Root logger
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
}

# Initialize logging
import logging.config
logging.config.dictConfig(LOGGING_CONFIG)

# Cleanup old files
def cleanup_old_files():
    """Clean up old temporary files and logs"""
    import glob
    from datetime import datetime, timedelta
    
    # Clean temp files older than 24 hours
    temp_files = glob.glob(os.path.join(TEMP_DIR, '*'))
    for file in temp_files:
        try:
            if os.path.getmtime(file) < (datetime.now() - timedelta(days=1)).timestamp():
                os.remove(file)
        except Exception as e:
            logging.warning(f"Failed to remove old temp file {file}: {e}")
    
    # Rotate logs if too large
    log_file = os.path.join(LOGS_DIR, 'mart_manager.log')
    try:
        if os.path.exists(log_file) and os.path.getsize(log_file) > 10 * 1024 * 1024:  # 10MB
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            os.rename(log_file, f"{log_file}.{timestamp}")
    except Exception as e:
        logging.warning(f"Failed to rotate log file: {e}")

# Run cleanup on startup
cleanup_old_files() 