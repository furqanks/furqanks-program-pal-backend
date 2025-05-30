from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean # Added Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    programs = relationship("Program", back_populates="owner")
    documents = relationship("Document", back_populates="owner")
    # Add relationship to EmailAccount if needed, or manage emails directly
    emails = relationship("EmailMessage", back_populates="owner") # Link user to their emails

class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    university = Column(String, index=True)
    country = Column(String, index=True)
    details = Column(String) # Could be JSON or text
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="programs")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True, nullable=False)
    file_path = Column(String, nullable=False) # Store path to the actual file
    description = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="documents")

# New Models for Email Feature

# class EmailAccount(Base):
#     __tablename__ = "email_accounts"
#     # If we were managing external accounts (IMAP/SMTP)
#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(Integer, ForeignKey("users.id"))
#     email_address = Column(String, unique=True, index=True)
#     # Store encrypted credentials, server details etc.
#     # ... (omitted for simplicity as we are likely simulating)
#     owner = relationship("User")

class EmailMessage(Base):
    __tablename__ = "email_messages"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id")) # Link email to the user
    message_id = Column(String, unique=True, index=True, nullable=True) # Optional: external message ID
    thread_id = Column(String, index=True, nullable=True) # Optional: for grouping conversations
    sender = Column(String, nullable=False)
    recipient = Column(String, nullable=False) # For simplicity, assuming one recipient for now
    # recipients_to = Column(Text) # Could store comma-separated or JSON list
    # recipients_cc = Column(Text)
    # recipients_bcc = Column(Text)
    subject = Column(String)
    body_text = Column(Text) # Plain text body
    body_html = Column(Text) # HTML body (optional)
    received_at = Column(DateTime, default=datetime.utcnow, index=True)
    sent_at = Column(DateTime, nullable=True, index=True) # Null if received
    is_read = Column(Boolean, default=False)
    is_draft = Column(Boolean, default=False)
    is_sent_by_user = Column(Boolean, default=False) # True if sent from this app
    folder = Column(String, default="inbox") # e.g., inbox, sent, drafts, trash

    owner = relationship("User", back_populates="emails")


