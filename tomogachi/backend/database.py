"""
PostgreSQL Database Connection and Models for Flask
"""

from sqlalchemy import text, create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import os

# Get DATABASE_URL from environment variable (required)
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required. Please set it in your .env file.")

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Tables

class User(Base):
    """User account"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    health = Column(Integer, default=20)  # Health score (0-100)
    
    # Relationships
    conversations = relationship('Conversation', back_populates='user', cascade='all, delete-orphan')
    food_logs = relationship('FoodLog', back_populates='user', cascade='all, delete-orphan')
    plaid_accounts = relationship('PlaidAccount', back_populates='user', cascade='all, delete-orphan')


class Conversation(Base):
    """Chat conversation history"""
    __tablename__ = 'conversations'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    user_message = Column(Text)
    bot_response = Column(Text)
    conversation_state = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    user = relationship('User', back_populates='conversations')


class FoodLog(Base):
    """Food consumption log"""
    __tablename__ = 'food_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    food_name = Column(String(255), index=True)
    category = Column(String(100))
    health_score = Column(Integer)
    confidence = Column(Float)
    image_path = Column(String(500), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    user = relationship('User', back_populates='food_logs')


class PlaidAccount(Base):
    """Plaid connected bank account"""
    __tablename__ = 'plaid_accounts'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    access_token = Column(String(500))
    item_id = Column(String(255))
    account_name = Column(String(255))
    account_type = Column(String(100))
    balance = Column(Float, nullable=True)
    connected_at = Column(DateTime, default=datetime.utcnow)
    last_synced = Column(DateTime, nullable=True)
    
    # Relationship
    user = relationship('User', back_populates='plaid_accounts')

# Utility functions

def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
    print("[DEBUG] Database tables created")


def get_db():
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """Test database connection"""
    try:
        db = SessionLocal()
        db.execute(text('SELECT 1'))
        db.close()
        print("[DEBUG] Connected to PostgreSQL successfully")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


if __name__ == '__main__':
    # Test connection and create tables
    if DATABASE_URL:
        # Mask password in output
        masked_url = DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL
        print(f"Using DATABASE_URL: ***@{masked_url}")
    if test_connection():
        init_db()