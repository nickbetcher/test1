from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Application
from app.schemas import ApplicationCreate


class DuplicateNameError(Exception):
    pass


def list_applications(db: Session) -> list[Application]:
    return list(db.scalars(select(Application).order_by(Application.name)))


def get_application(db: Session, name: str) -> Application | None:
    return db.scalar(select(Application).where(Application.name == name))


def create_application(db: Session, data: ApplicationCreate, created_by: str) -> Application:
    app = Application(
        name=data.name,
        description=data.description,
        owner_team=data.owner_team,
        owner_email=str(data.owner_email),
        repo_url=str(data.repo_url) if data.repo_url else "",
        lifecycle=data.lifecycle.value,
        created_by=created_by,
    )
    db.add(app)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateNameError(data.name) from exc
    db.refresh(app)
    return app
