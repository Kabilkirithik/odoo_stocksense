from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..fetchers import move_fetcher
from ..schemas import MoveHistoryOut

router = APIRouter(prefix="/api/moves", tags=["Move History"])

@router.get("")
def list_moves(
    movement_type: Optional[str] = None,
    product_id: Optional[str] = None,
    reference_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    return move_fetcher.fetch(
        db,
        movement_type=movement_type,
        product_id=product_id,
        reference_id=reference_id,
        skip=skip,
        limit=limit
    )

@router.get("/{id}", response_model=MoveHistoryOut)
def get_move(id: int, db: Session = Depends(get_db)):
    move = move_fetcher.get_by_id(db, id)
    if not move:
        raise HTTPException(status_code=404, detail="Movement record not found")
    return move
