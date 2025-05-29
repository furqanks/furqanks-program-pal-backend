from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, models, schemas, database
from .auth import get_current_user

router = APIRouter(
    prefix="/emails",
    tags=["emails"],
    dependencies=[Depends(get_current_user)] # Protect all email routes
)

@router.get("/", response_model=List[schemas.EmailMessage])
def read_emails(
    folder: Optional[str] = None,
    is_read: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50, # Default limit to 50 for emails
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Retrieve email messages for the current user, with optional filters."""
    emails = crud.get_email_messages_by_owner(
        db, owner_id=current_user.id, folder=folder, is_read=is_read, skip=skip, limit=limit
    )
    return emails

@router.get("/{email_id}", response_model=schemas.EmailMessage)
def read_email(
    email_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Retrieve a specific email message by ID."""
    db_email = crud.get_email_message(db, email_id=email_id, owner_id=current_user.id)
    if db_email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    return db_email

@router.post("/", response_model=schemas.EmailMessage, status_code=status.HTTP_201_CREATED)
def create_email(
    email: schemas.EmailMessageCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a new email message (e.g., save draft, log received email)."""
    # For now, this endpoint primarily saves messages. Sending is separate.
    # Ensure the recipient/sender fields are handled appropriately based on context
    # (e.g., if saving a draft, recipient might be set, but is_sent_by_user is false)
    return crud.create_email_message(db=db, email=email, owner_id=current_user.id)

@router.patch("/{email_id}", response_model=schemas.EmailMessage)
def update_email_status(
    email_id: int,
    update_data: schemas.EmailMessageBase, # Reuse base schema for update fields
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update email status (is_read, folder)."""
    # Extract only the fields we allow updating
    update_payload = update_data.model_dump(include={
        "is_read": ..., "folder": ...
    }, exclude_unset=True)

    if not update_payload:
        raise HTTPException(status_code=400, detail="No valid fields provided for update")

    updated_email = crud.update_email_message_status(
        db=db,
        email_id=email_id,
        owner_id=current_user.id,
        is_read=update_payload.get("is_read"),
        folder=update_payload.get("folder")
    )
    if updated_email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    return updated_email

@router.delete("/{email_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email(
    email_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete an email message."""
    # Consider implementing soft delete (move to trash folder) instead
    deleted = crud.delete_email_message(db, email_id=email_id, owner_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Email not found")
    return

# Placeholder for sending email - this would likely involve an external service
@router.post("/send", response_model=schemas.EmailMessage)
def send_email(
    email_data: schemas.EmailSendRequest,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Simulate sending an email. Creates a record in the sent folder."""
    # In a real app, this would interact with an email sending service (SMTP, SendGrid, etc.)
    # Here, we just create a record in our DB
    sent_email_schema = schemas.EmailMessageCreate(
        sender=current_user.email, # Sender is the logged-in user
        recipient=email_data.recipient,
        subject=email_data.subject,
        body_text=email_data.body_text,
        body_html=email_data.body_html,
        folder="sent",
        is_read=True, # Sent messages are typically marked read
        is_sent_by_user=True
    )
    # Note: sent_at will be set within create_email_message based on folder/is_sent_by_user
    db_sent_email = crud.create_email_message(db=db, email=sent_email_schema, owner_id=current_user.id)
    return db_sent_email

# TODO: Add AI reply assistance endpoint later

