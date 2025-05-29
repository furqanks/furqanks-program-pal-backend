from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import shutil
import os

from .. import crud, models, schemas, database
from .auth import get_current_user

router = APIRouter(
    prefix="/programs",
    tags=["programs"],
    dependencies=[Depends(get_current_user)] # Protect all program routes
)

@router.post("/", response_model=schemas.Program)
def create_program(
    program: schemas.ProgramCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    return crud.create_user_program(db=db, program=program, owner_id=current_user.id)

@router.get("/", response_model=List[schemas.Program])
def read_programs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    programs = crud.get_programs_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    return programs

@router.get("/{program_id}", response_model=schemas.Program)
def read_program(
    program_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_program = crud.get_program(db, program_id=program_id, owner_id=current_user.id)
    if db_program is None:
        raise HTTPException(status_code=404, detail="Program not found")
    return db_program

@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_program(
    program_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    deleted = crud.delete_program(db, program_id=program_id, owner_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Program not found")
    return

