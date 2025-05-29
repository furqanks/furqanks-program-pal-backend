from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
from pathlib import Path

from .. import crud, models, schemas, database
from .auth import get_current_user

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(get_current_user)] # Protect all document routes
)

UPLOAD_DIRECTORY = "/home/ubuntu/program_pal_uploads"
Path(UPLOAD_DIRECTORY).mkdir(parents=True, exist_ok=True)

@router.post("/", response_model=schemas.Document)
def upload_document(
    description: str | None = None, # Get description from form data
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    user_upload_dir = Path(UPLOAD_DIRECTORY) / str(current_user.id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)

    # Basic sanitization - replace spaces, avoid path traversal
    safe_filename = file.filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
    file_location = user_upload_dir / safe_filename

    # Avoid overwriting existing files by adding a counter if needed (simple approach)
    counter = 0
    original_location = file_location
    while file_location.exists():
        counter += 1
        file_location = user_upload_dir / f"{original_location.stem}_{counter}{original_location.suffix}"
        if counter > 100: # Safety break
             raise HTTPException(status_code=500, detail="Could not save file due to naming conflict.")

    try:
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(file.file, file_object)
    except Exception as e:
        # Clean up partial file if copy fails
        if file_location.exists():
            os.remove(file_location)
        raise HTTPException(status_code=500, detail=f"Could not save file: {e}")
    finally:
        file.file.close()

    doc_create = schemas.DocumentCreate(filename=safe_filename, description=description)
    return crud.create_user_document(db=db, document=doc_create, file_path=str(file_location), owner_id=current_user.id)

@router.get("/", response_model=List[schemas.Document])
def read_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    documents = crud.get_documents_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return documents

@router.get("/{document_id}", response_model=schemas.Document)
def read_document(
    document_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_document = crud.get_document(db, document_id=document_id, owner_id=current_user.id)
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return db_document

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_document = crud.get_document(db, document_id=document_id, owner_id=current_user.id)
    if db_document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # Attempt to delete the file from storage
    try:
        if os.path.exists(db_document.file_path):
            os.remove(db_document.file_path)
    except Exception as e:
        # Log error but proceed with DB deletion
        print(f"Error deleting file {db_document.file_path}: {e}")
        # Optionally raise an error if file deletion failure is critical
        # raise HTTPException(status_code=500, detail=f"Could not delete file: {e}")

    deleted = crud.delete_document(db, document_id=document_id, owner_id=current_user.id)
    # The crud function already checks if the document exists, so this check might be redundant
    # if not deleted:
    #     raise HTTPException(status_code=404, detail="Document not found during deletion attempt")
    return

