from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any
from datetime import datetime

# --- Authentication Schemas ---
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    # is_active: bool # Removed as not present in model
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[EmailStr] = None

# --- Program Schemas ---
class ProgramBase(BaseModel):
    name: str
    university: Optional[str] = None # Made optional to match model
    country: Optional[str] = None
    details: Optional[str] = None # Changed from url/notes to details

class ProgramCreate(ProgramBase):
    pass

class Program(ProgramBase):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Document Schemas ---
class DocumentBase(BaseModel):
    filename: str
    description: Optional[str] = None # Added description

class DocumentCreate(DocumentBase):
    # file_path will be set internally during upload
    pass

class Document(DocumentBase):
    id: int
    owner_id: int
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Search Schemas ---
class SearchQuery(BaseModel):
    query: str

class SearchResultItem(BaseModel):
    program_name: Optional[str] = None
    university_name: Optional[str] = None
    country: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    tuition_fees: Optional[str] = None
    ranking: Optional[str] = None
    intake_dates: Optional[List[str]] = None
    visa_support: Optional[bool] = None
    source: str

class SearchResponse(BaseModel):
    results: List[SearchResultItem]
    summary: Optional[str] = None

# --- AI Document Assistance Schemas ---
class DocumentAnalysisRequest(BaseModel):
    document_id: int
    analysis_type: str = Field(..., description="Type of analysis requested, e.g., 'summary', 'key_points', 'qa'")
    query: Optional[str] = Field(None, description="User query if analysis_type is 'qa'")

class DocumentAnalysisResponse(BaseModel):
    document_id: int
    analysis_type: str
    status: str = Field(..., description="e.g., 'pending', 'processing', 'completed', 'failed'")
    result: Optional[Any] = Field(None, description="The result of the analysis, format depends on analysis_type")
    error_message: Optional[str] = None

# --- Email Schemas ---
class EmailMessageBase(BaseModel):
    sender: str
    recipient: str
    subject: Optional[str] = None
    body_text: Optional[str] = None
    body_html: Optional[str] = None
    folder: str = "inbox"
    is_read: bool = False
    is_draft: bool = False
    is_sent_by_user: bool = False
    message_id: Optional[str] = None # Optional external ID
    thread_id: Optional[str] = None # Optional thread ID

class EmailMessageCreate(EmailMessageBase):
    # sent_at will be set if sending, received_at defaults to now
    pass

class EmailMessage(EmailMessageBase):
    id: int
    owner_id: int
    received_at: datetime
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schema for sending an email
class EmailSendRequest(BaseModel):
    recipient: EmailStr
    subject: str
    body_text: str
    body_html: Optional[str] = None


