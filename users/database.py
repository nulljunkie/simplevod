from sqlalchemy import ForeignKey, create_engine, Column, Integer, String, Boolean, DateTime
from datetime import datetime, timedelta, UTC
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
from contextlib import contextmanager
from utils import generate_random_string
from decouple import config
import logging
from tenacity import retry, stop_after_attempt, wait_fixed


DATABASE_URL = config('DATABASE_URL')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def create_db_engine() -> "Engine":
    """
    Attempt to create a SQLAlchemy engine and verify DB connection.
    Retries up to 5 times with a 2-second wait between attempts.
    Returns:
        SQLAlchemy Engine
    """
    logger.info('Attempting to connect to the database...')
    engine = create_engine(DATABASE_URL)
    try:
        conn = engine.connect()
        conn.close()
        logger.info('Database connection established.')
    except Exception as e:
        logger.exception(f"Database connection failed: {e}")
        raise
    return engine

engine = create_db_engine()

Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

class User(Base):
    """
    SQLAlchemy model for the users table.
    """
    __tablename__ = "users"
    id: int = Column(Integer, primary_key=True, index=True)
    email: str = Column(String, unique=True, index=True)
    username: str = Column(String(50), unique=True, index=True)
    hashed_password: str = Column(String, nullable=True)
    is_active: bool = Column(Boolean, default=False)
    created_at: datetime = Column(DateTime, server_default=func.now())
    updated_at: datetime = Column(DateTime, server_default=func.now(), onupdate=func.now())

    activation_tokens = relationship("ActivationToken", back_populates="user")

class ActivationToken(Base):
    """
    SQLAlchemy model for activation_tokens table.
    """
    __tablename__ = "activation_tokens"
    id: int = Column(Integer, primary_key=True)
    token: str = Column(String(255), unique=True, nullable=False, default=lambda: generate_random_string(64))
    user_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: datetime = Column(DateTime, nullable=False, default=datetime.now(UTC))
    expires_at: datetime = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC) + timedelta(hours=6))

    user = relationship("User", back_populates="activation_tokens")

User.activation_tokens = relationship("ActivationToken", back_populates="user")

# Create tables in DB if don't exist
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created or verified.")
except Exception as e:
    logger.exception(f"Error creating tables: {e}")

@contextmanager
def get_db() -> "Session":
    """
    Context manager for SQLAlchemy session lifecycle.
    Yields a database session and ensures cleanup.
    Returns:
        SQLAlchemy Session
    """
    session = Session()
    logger.debug("Database session started.")
    try:
        yield session
        session.commit()
        logger.debug("Database session committed.")
    except Exception as e:
        session.rollback()
        logger.exception(f"Session rollback due to exception: {e}")
        raise
    finally:
        session.close()
        logger.debug("Database session closed.")
