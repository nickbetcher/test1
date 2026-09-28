from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import service
from app.auth import get_principal
from app.db import get_db
from app.schemas import ApplicationCreate, ApplicationRead

router = APIRouter(prefix="/api/v1", tags=["applications"])


@router.get("/applications", response_model=list[ApplicationRead])
def list_applications(db: Session = Depends(get_db), _: str = Depends(get_principal)):
    """List every registered application."""
    return service.list_applications(db)


@router.get("/applications/{name}", response_model=ApplicationRead)
def get_application(name: str, db: Session = Depends(get_db), _: str = Depends(get_principal)):
    """Fetch one application by its unique name."""
    app = service.get_application(db, name)
    if app is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Application '{name}' not found")
    return app


@router.post("/applications", response_model=ApplicationRead, status_code=201)
def create_application(
    data: ApplicationCreate,
    db: Session = Depends(get_db),
    principal: str = Depends(get_principal),
):
    """Register a new application. Names must be unique."""
    try:
        return service.create_application(db, data, created_by=principal)
    except service.DuplicateNameError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Application '{data.name}' already exists"
        ) from None
