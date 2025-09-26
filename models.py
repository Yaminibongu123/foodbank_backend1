from database import db
import bcrypt
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)

class User:
    def __init__(self, id=None, username=None, email=None, password_hash=None, 
                 full_name=None, phone=None, address=None, location=None, 
                 role='donor', is_verified=False, is_active=True, 
                 member_since=None, last_login=None, **kwargs):  # Added **kwargs to handle extra fields
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.full_name = full_name
        self.phone = phone
        self.address = address
        self.location = location
        self.role = role
        self.is_verified = is_verified
        self.is_active = is_active
        self.member_since = member_since
        self.last_login = last_login
        
        # Handle any additional fields from database that aren't in the main parameters
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    def save(self):
        connection = db.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor()
            if self.id:
                # Update existing user
                cursor.execute('''
                    UPDATE users SET username=%s, email=%s, full_name=%s, phone=%s, 
                    address=%s, location=%s, role=%s, is_verified=%s, is_active=%s, last_login=%s
                    WHERE id=%s
                ''', (self.username, self.email, self.full_name, self.phone, 
                      self.address, self.location, self.role, self.is_verified, 
                      self.is_active, self.last_login, self.id))
            else:
                # Insert new user
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash, full_name, 
                    phone, address, location, role, is_verified, is_active, member_since)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (self.username, self.email, self.password_hash, self.full_name,
                      self.phone, self.address, self.location, self.role, 
                      self.is_verified, self.is_active, datetime.now()))
                self.id = cursor.lastrowid
            
            connection.commit()
            return self.id
        except Exception as e:
            logger.error(f"Error saving user: {e}")
            connection.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
    
    @classmethod
    def find_by_username(cls, username):
        connection = db.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            user_data = cursor.fetchone()
            
            if user_data:
                return cls(**user_data)  # **kwargs will handle extra fields like created_at
            return None
        except Exception as e:
            logger.error(f"Error finding user by username: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    @classmethod
    def find_by_email(cls, email):
        connection = db.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
            user_data = cursor.fetchone()
            
            if user_data:
                return cls(**user_data)
            return None
        except Exception as e:
            logger.error(f"Error finding user by email: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    @classmethod
    def find_by_id(cls, user_id):
        connection = db.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            user_data = cursor.fetchone()
            
            if user_data:
                return cls(**user_data)
            return None
        except Exception as e:
            logger.error(f"Error finding user by ID: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'address': self.address,
            'location': self.location,
            'role': self.role,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'member_since': self.member_since.isoformat() if self.member_since else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class FoodDonation:
    def __init__(self, id=None, user_id=None, food_category=None, food_type=None,
                 description=None, quantity=None, unit=None, expiry_date=None,
                 preferred_pickup_time=None, pickup_address=None, special_instructions=None,
                 status='pending', created_at=None, **kwargs):
        self.id = id
        self.user_id = user_id
        self.food_category = food_category
        self.food_type = food_type
        self.description = description
        self.quantity = quantity
        self.unit = unit
        self.expiry_date = expiry_date
        self.preferred_pickup_time = preferred_pickup_time
        self.pickup_address = pickup_address
        self.special_instructions = special_instructions
        self.status = status
        self.created_at = created_at
        
        # Handle additional fields
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def save(self):
        connection = db.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor()
            if self.id:
                cursor.execute('''
                    UPDATE food_donations SET food_category=%s, food_type=%s, description=%s,
                    quantity=%s, unit=%s, expiry_date=%s, preferred_pickup_time=%s,
                    pickup_address=%s, special_instructions=%s, status=%s
                    WHERE id=%s
                ''', (self.food_category, self.food_type, self.description, self.quantity,
                      self.unit, self.expiry_date, self.preferred_pickup_time,
                      self.pickup_address, self.special_instructions, self.status, self.id))
            else:
                cursor.execute('''
                    INSERT INTO food_donations (user_id, food_category, food_type, description,
                    quantity, unit, expiry_date, preferred_pickup_time, pickup_address,
                    special_instructions, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (self.user_id, self.food_category, self.food_type, self.description,
                      self.quantity, self.unit, self.expiry_date, self.preferred_pickup_time,
                      self.pickup_address, self.special_instructions, self.status))
                self.id = cursor.lastrowid
            
            connection.commit()
            return self.id
        except Exception as e:
            logger.error(f"Error saving food donation: {e}")
            connection.rollback()
            return None
        finally:
            if cursor:
                cursor.close()
    
    @classmethod
    def find_by_user_id(cls, user_id, limit=10):
        connection = db.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute('''
                SELECT * FROM food_donations 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            ''', (user_id, limit))
            donations = cursor.fetchall()
            return [cls(**donation) for donation in donations]
        except Exception as e:
            logger.error(f"Error finding donations by user ID: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    @classmethod
    def get_available_donations(cls):
        """Get all available donations (for inventory)"""
        connection = db.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute('''
                SELECT * FROM food_donations 
                WHERE status = 'available' 
                ORDER BY created_at DESC
            ''')
            donations = cursor.fetchall()
            return [cls(**donation) for donation in donations]
        except Exception as e:
            logger.error(f"Error getting available donations: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
    
    @classmethod
    def get_all_donations(cls):
        """Get all donations"""
        connection = db.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute('SELECT * FROM food_donations ORDER BY created_at DESC')
            donations = cursor.fetchall()
            return [cls(**donation) for donation in donations]
        except Exception as e:
            logger.error(f"Error getting all donations: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

class FoodRequest:
    def __init__(self, id=None, user_id=None, food_category=None, quantity_needed=None,
                 urgency_level='medium', preferred_delivery_time=None, delivery_address=None,
                 special_requirements=None, status='pending', created_at=None, **kwargs):
        self.id = id
        self.user_id = user_id
        self.food_category = food_category
        self.quantity_needed = quantity_needed
        self.urgency_level = urgency_level
        self.preferred_delivery_time = preferred_delivery_time
        self.delivery_address = delivery_address
        self.special_requirements = special_requirements
        self.status = status
        self.created_at = created_at
        
        # Handle additional fields
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def save(self):
        connection = db.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor()
            if self.id:
                cursor.execute('''
                    UPDATE food_requests SET food_category=%s, quantity_needed=%s,
                    urgency_level=%s, preferred_delivery_time=%s, delivery_address=%s,
                    special_requirements=%s, status=%s
                    WHERE id=%s
                ''', (self.food_category, self.quantity_needed, self.urgency_level,
                      self.preferred_delivery_time, self.delivery_address,
                      self.special_requirements, self.status, self.id))
            else:
                cursor.execute('''
                    INSERT INTO food_requests (user_id, food_category, quantity_needed,
                    urgency_level, preferred_delivery_time, delivery_address,
                    special_requirements, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (self.user_id, self.food_category, self.quantity_needed,
                      self.urgency_level, self.preferred_delivery_time, self.delivery_address,
                      self.special_requirements, self.status))
                self.id = cursor.lastrowid
            
            connection.commit()
            return self.id
        except Exception as e:
            logger.error(f"Error saving food request: {e}")
            connection.rollback()
            return None
        finally:
            if cursor:
                cursor.close()

class OTPVerification:
    @staticmethod
    def generate_otp(user_id, purpose):
        otp_code = str(random.randint(100000, 999999))
        expires_at = datetime.now() + timedelta(minutes=10)
        
        connection = db.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO otp_verifications (user_id, otp_code, purpose, expires_at)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, otp_code, purpose, expires_at))
            connection.commit()
            return otp_code
        except Exception as e:
            logger.error(f"Error generating OTP: {e}")
            return None
        finally:
            if cursor:
                cursor.close()
    
    @staticmethod
    def verify_otp(user_id, otp_code, purpose):
        connection = db.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute('''
                SELECT * FROM otp_verifications 
                WHERE user_id = %s AND otp_code = %s AND purpose = %s 
                AND is_used = FALSE AND expires_at > NOW()
            ''', (user_id, otp_code, purpose))
            otp_record = cursor.fetchone()
            
            if otp_record:
                # Mark OTP as used
                cursor.execute('''
                    UPDATE otp_verifications SET is_used = TRUE 
                    WHERE id = %s
                ''', (otp_record['id'],))
                connection.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return False
        finally:
            if cursor:
                cursor.close()