import mysql.connector
from mysql.connector import Error
from config import Config
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.config = Config()
        self.connection = None
    
    def get_connection(self):
        try:
            if not self.connection or not self.connection.is_connected():
                self.connection = mysql.connector.connect(
                    host=self.config.MYSQL_HOST,
                    user=self.config.MYSQL_USER,
                    password=self.config.MYSQL_PASSWORD,
                    database=self.config.MYSQL_DB,
                    port=self.config.MYSQL_PORT
                )
            return self.connection
        except Error as e:
            logger.error(f"Error connecting to MySQL: {e}")
            return None
    
    def close_connection(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
    
    def initialize_database(self):
        """Initialize database tables"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    full_name VARCHAR(200) NOT NULL,
                    phone VARCHAR(20),
                    address TEXT,
                    location VARCHAR(200),
                    role ENUM('admin', 'donor', 'recipient') DEFAULT 'donor',
                    is_verified BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    member_since TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            ''')
            
            # Food donations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS food_donations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    food_category VARCHAR(100) NOT NULL,
                    food_type ENUM('veg', 'non-veg') NOT NULL,
                    description TEXT NOT NULL,
                    quantity DECIMAL(10,2) NOT NULL,
                    unit VARCHAR(20) NOT NULL,
                    expiry_date DATE NOT NULL,
                    preferred_pickup_time TIME NOT NULL,
                    pickup_address TEXT NOT NULL,
                    special_instructions TEXT,
                    status ENUM('pending', 'approved', 'collected', 'cancelled') DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Food requests table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS food_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    food_category VARCHAR(100) NOT NULL,
                    quantity_needed INT NOT NULL,
                    urgency_level ENUM('low', 'medium', 'high') DEFAULT 'medium',
                    preferred_delivery_time TIME,
                    delivery_address TEXT NOT NULL,
                    special_requirements TEXT,
                    status ENUM('pending', 'approved', 'delivered', 'cancelled') DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Notifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    message TEXT NOT NULL,
                    type ENUM('info', 'success', 'warning', 'error') DEFAULT 'info',
                    is_read BOOLEAN DEFAULT FALSE,
                    related_entity_type ENUM('donation', 'request', 'system') DEFAULT 'system',
                    related_entity_id INT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # OTP verification table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS otp_verifications (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    otp_code VARCHAR(6) NOT NULL,
                    purpose ENUM('email_verification', 'password_reset', 'profile_update') NOT NULL,
                    is_used BOOLEAN DEFAULT FALSE,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            connection.commit()
            logger.info("Database tables initialized successfully")
            return True
            
        except Error as e:
            logger.error(f"Error initializing database: {e}")
            return False
        finally:
            if cursor:
                cursor.close()

db = Database()