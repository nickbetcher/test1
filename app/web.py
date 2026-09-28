from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import service
from app.auth import get_principal
from app.db import get_db
from app.schemas import ApplicationCreate, Lifecycle

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db), user: str = Depends(get_principal)):
    return templates.TemplateResponse(
        request, "index.html", {"apps": service.list_applications(db), "user": user}
    )


@router.get("/applications/new", response_class=HTMLResponse)
def new_form(request: Request, user: str = Depends(get_principal)):
    return templates.TemplateResponse(
        request,
        "new.html",
        {"form": {}, "errors": [], "lifecycles": list(Lifecycle), "user": user},
    )


@router.post("/applications/new", response_class=HTMLResponse)
async def create(
    request: Request, db: Session = Depends(get_db), user: str = Depends(get_principal)
):
    form = {k: v.strip() for k, v in (await request.form()).items() if isinstance(v, str)}
    payload = {**form, "repo_url": form.get("repo_url") or None}
    errors: list[str] = []
    try:
        data = ApplicationCreate(**payload)
        service.create_application(db, data, created_by=user)
    except ValidationError as exc:
        errors = [f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()]
    except service.DuplicateNameError:
        errors = [f"An application named '{form.get('name')}' already exists."]

    if errors:
        return templates.TemplateResponse(
            request,
            "new.html",
            {"form": form, "errors": errors, "lifecycles": list(Lifecycle), "user": user},
            status_code=422,
        )
    return RedirectResponse("/", status_code=303)
