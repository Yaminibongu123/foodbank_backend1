import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Security - Use environment variables with fallbacks for development only
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-jwt-secret-key-change-in-production'
    
    # Database configuration - No defaults for production, require environment variables
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'foodbank_db')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    
    # Construct MySQL connection URI
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # File upload configuration
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # CORS settings
    CORS_SUPPORTS_CREDENTIALS = True

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    # Development-specific settings
    EXPLAIN_TEMPLATE_LOADING = False

class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    # Use test database
    MYSQL_DB = os.environ.get('MYSQL_TEST_DB', 'foodbank_test_db')

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Production security - require environment variables
    @property
    def SECRET_KEY(self):
        key = os.environ.get('SECRET_KEY')
        if not key or key == 'dev-secret-key-change-in-production':
            raise ValueError("SECRET_KEY must be set in production environment")
        return key
    
    @property
    def JWT_SECRET_KEY(self):
        key = os.environ.get('JWT_SECRET_KEY')
        if not key or key == 'dev-jwt-secret-key-change-in-production':
            raise ValueError("JWT_SECRET_KEY must be set in production environment")
        return key
    
    # Production database - no defaults
    MYSQL_HOST = os.environ.get('MYSQL_HOST')
    MYSQL_USER = os.environ.get('MYSQL_USER')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD')
    MYSQL_DB = os.environ.get('MYSQL_DB')
    
    def __init__(self):
        # Validate required production settings
        if not all([self.MYSQL_HOST, self.MYSQL_USER, self.MYSQL_PASSWORD, self.MYSQL_DB]):
            raise ValueError("All database environment variables must be set in production")

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# Utility function to get current configuration
def get_config():
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, DevelopmentConfig)

# Optional: Add configuration validation
def validate_config(config_obj):
    """Validate configuration settings"""
    required_settings = ['SECRET_KEY', 'MYSQL_HOST', 'MYSQL_USER', 'MYSQL_DB']
    
    for setting in required_settings:
        if not getattr(config_obj, setting, None):
            print(f"Warning: {setting} is not properly configured")
    
    return True