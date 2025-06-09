from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
 
engine = create_engine("sqlite:///submissions.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
 
Base = declarative_base()
 
class Submission(Base):
    __tablename__ = "submissions"
    id = Column(String, primary_key=True, index=True)
    filename = Column(String)
    filepath = Column(String)
    folder = Column(String)
    status = Column(String)
    sender_email = Column(String)
    sender_password = Column(String)
    approver_email = Column(String)
 
Base.metadata.create_all(bind=engine)