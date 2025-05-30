from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas, models, database
from ..services import search_service
from .auth import get_current_user

router = APIRouter(
    prefix="/search",
    tags=["search"],
    dependencies=[Depends(get_current_user)] # Protect search routes
)

@router.post("/", response_model=schemas.SearchResponse)
async def perform_search(
    search_query: schemas.SearchQuery,
    db: Session = Depends(database.get_db), # Keep DB session if needed later
    current_user: models.User = Depends(get_current_user)
):
    """Receives a natural language query and returns search results."""
    try:
        results = await search_service.perform_advanced_search(search_query)
        return results
    except Exception as e:
        # Basic error handling for now
        print(f"Error during search: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

