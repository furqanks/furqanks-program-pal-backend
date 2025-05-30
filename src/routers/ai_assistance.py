from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Any
import os # Import os for path checking

from .. import crud, models, schemas, database, services
from ..services import ai_service # Import the AI service
from .auth import get_current_user # Import the correct dependency from auth router

router = APIRouter(
    prefix="/ai",
    tags=["ai"],
    dependencies=[Depends(get_current_user)], # Use the imported dependency
)

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/analyze_document", response_model=schemas.DocumentAnalysisResponse)
async def analyze_document(
    request: schemas.DocumentAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Use the imported dependency
):
    """Endpoint to trigger AI analysis on an uploaded document."""
    db_document = crud.get_document(db, document_id=request.document_id)

    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if db_document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this document")

    # --- Retrieve actual document content --- 
    try:
        file_path = db_document.file_path
        if not file_path or not os.path.exists(file_path):
             print(f"Error: Document file path not found or file does not exist for ID: {request.document_id}, Path: {file_path}")
             raise FileNotFoundError(f"Document file not found at path: {file_path}")

        with open(file_path, "rb") as f:
            document_content = f.read()
        print(f"Successfully read content for document ID: {request.document_id}, Path: {file_path}, Size: {len(document_content)} bytes")

    except FileNotFoundError:
         # Return a pending/failed status immediately if content retrieval fails
         return schemas.DocumentAnalysisResponse(
             document_id=request.document_id,
             analysis_type=request.analysis_type,
             status="failed",
             error_message="Document content not found or inaccessible."
         )
    except Exception as e:
        print(f"Error retrieving document content for ID {request.document_id}: {e}")
        return schemas.DocumentAnalysisResponse(
             document_id=request.document_id,
             analysis_type=request.analysis_type,
             status="failed",
             error_message=f"Failed to retrieve document content: {e}"
         )
    # --- End Content Retrieval ---

    # Call the AI service, passing content and filename for type detection
    try:
        analysis_result = await ai_service.analyze_document_content(
            document_content=document_content,
            filename=db_document.filename, # Pass filename for type inference
            analysis_type=request.analysis_type,
            query=request.query
        )
        status = "completed"
        error_message = None
        # Check if the service returned an error string
        if isinstance(analysis_result, str) and analysis_result.startswith("Error:"):
            status = "failed"
            error_message = analysis_result
            analysis_result = None

    except Exception as e:
        print(f"AI analysis failed for document {request.document_id}: {e}")
        status = "failed"
        analysis_result = None
        error_message = str(e)

    # TODO: Update document status/result in the database if needed

    return schemas.DocumentAnalysisResponse(
        document_id=request.document_id,
        analysis_type=request.analysis_type,
        status=status,
        result=analysis_result,
        error_message=error_message
    )

