from sqlalchemy.orm import Session
from . import models, schemas, security
from typing import List, Optional # Added Optional

# --- User CRUD ---

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Program CRUD ---

def get_programs_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Program).filter(models.Program.owner_id == owner_id).offset(skip).limit(limit).all()

def create_user_program(db: Session, program: schemas.ProgramCreate, owner_id: int):
    db_program = models.Program(**program.model_dump(), owner_id=owner_id)
    db.add(db_program)
    db.commit()
    db.refresh(db_program)
    return db_program

def get_program(db: Session, program_id: int, owner_id: int):
    return db.query(models.Program).filter(models.Program.id == program_id, models.Program.owner_id == owner_id).first()

def delete_program(db: Session, program_id: int, owner_id: int):
    db_program = db.query(models.Program).filter(models.Program.id == program_id, models.Program.owner_id == owner_id).first()
    if db_program:
        db.delete(db_program)
        db.commit()
        return True
    return False

# --- Document CRUD ---

def get_documents_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Document).filter(models.Document.owner_id == owner_id).offset(skip).limit(limit).all()

def create_user_document(db: Session, document: schemas.DocumentCreate, file_path: str, owner_id: int):
    # Ensure description is handled correctly (it's optional in schema)
    db_document = models.Document(
        filename=document.filename,
        description=document.description,
        file_path=file_path,
        owner_id=owner_id
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def get_document(db: Session, document_id: int, owner_id: int):
    return db.query(models.Document).filter(models.Document.id == document_id, models.Document.owner_id == owner_id).first()

def delete_document(db: Session, document_id: int, owner_id: int):
    db_document = db.query(models.Document).filter(models.Document.id == document_id, models.Document.owner_id == owner_id).first()
    if db_document:
        # Consider deleting the actual file from storage here as well
        # import os
        # if os.path.exists(db_document.file_path):
        #     os.remove(db_document.file_path)
        db.delete(db_document)
        db.commit()
        return True
    return False

# --- Email Message CRUD ---

def create_email_message(db: Session, email: schemas.EmailMessageCreate, owner_id: int) -> models.EmailMessage:
    """Creates a new email message in the database."""
    db_email = models.EmailMessage(**email.model_dump(), owner_id=owner_id)
    # Set sent_at if it's a sent message (e.g., folder='sent')
    if db_email.folder == 'sent' or db_email.is_sent_by_user:
        db_email.sent_at = db_email.received_at # Or use a specific sent time if provided

    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    return db_email

def get_email_message(db: Session, email_id: int, owner_id: int) -> Optional[models.EmailMessage]:
    """Retrieves a single email message by its ID for a specific owner."""
    return db.query(models.EmailMessage).filter(
        models.EmailMessage.id == email_id,
        models.EmailMessage.owner_id == owner_id
    ).first()

def get_email_messages_by_owner(
    db: Session,
    owner_id: int,
    folder: Optional[str] = None,
    is_read: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.EmailMessage]:
    """Retrieves a list of email messages for a specific owner, with optional filters."""
    query = db.query(models.EmailMessage).filter(models.EmailMessage.owner_id == owner_id)

    if folder is not None:
        query = query.filter(models.EmailMessage.folder == folder)
    if is_read is not None:
        query = query.filter(models.EmailMessage.is_read == is_read)

    # Add sorting, e.g., by received date descending
    query = query.order_by(models.EmailMessage.received_at.desc())

    return query.offset(skip).limit(limit).all()

def update_email_message_status(
    db: Session,
    email_id: int,
    owner_id: int,
    is_read: Optional[bool] = None,
    folder: Optional[str] = None
) -> Optional[models.EmailMessage]:
    """Updates the status (is_read, folder) of an email message."""
    db_email = get_email_message(db, email_id=email_id, owner_id=owner_id)
    if not db_email:
        return None

    updated = False
    if is_read is not None and db_email.is_read != is_read:
        db_email.is_read = is_read
        updated = True
    if folder is not None and db_email.folder != folder:
        db_email.folder = folder
        updated = True

    if updated:
        db.commit()
        db.refresh(db_email)

    return db_email

def delete_email_message(db: Session, email_id: int, owner_id: int) -> bool:
    """Deletes an email message from the database."""
    # Consider moving to 'trash' folder instead of hard delete initially
    db_email = get_email_message(db, email_id=email_id, owner_id=owner_id)
    if db_email:
        db.delete(db_email)
        db.commit()
        return True
    return False

