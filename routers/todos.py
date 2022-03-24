from ast import For
import sys
sys.path.append("..")
from starlette import status
from starlette.responses import RedirectResponse
from fastapi import Depends, HTTPException, APIRouter, Request, Form
import models
from typing import Optional
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from .auth import get_current_user

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/todos",
    tags=["todos"],
    responses={404: {"description": "Not found"}}
) 

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")


"""
# crear la base de datos inicial
@app.get("/")
async def create_datebase():
    return {"Datatebase": "Created"}
"""

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

class Todo(BaseModel):
    title: str
    description: Optional[str]
    priority: int = Field(gt=0, lt=6, description="The priority must be between 1-5")
    complete: bool

@router.get("/", response_class=HTMLResponse)
async def read_all_by_user(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todos = db.query(models.Todos).filter(models.Todos.owner_id == user.get("id")).all()
    return templates.TemplateResponse("home.html", {"request": request, "todos": todos, "user": user})

@router.get("/add-todo", response_class=HTMLResponse)
async def add_new_todo(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse("add-todo.html", {"request": request, "user": user})

@router.post("/add-todo", response_class=HTMLResponse)
async def create_todo(request: Request, title: str = Form(...), description: str = Form(...), priority: int = Form(...), db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = models.Todos()
    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority
    todo_model.complete = False
    todo_model.owner_id = user.get("id")

    db.add(todo_model)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def edit_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo, "user": user})

@router.post("/edit-todo/{todo_id}", response_class=HTMLResponse)
async def edit_todo_commit(request: Request, todo_id: int, db: Session = Depends(get_db), title: str = Form(...), description: str = Form(...), priority: int = Form(...)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority

    db.add(todo_model)
    db.commit()
    
    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

@router.get("/delete/{todo_id}", response_class=HTMLResponse)
async def delete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get("id")).first()

    if todo_model is None:
        return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)

    db.query(models.Todos).filter(models.Todos.id == todo_id).delete()

    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)



# obtener todos los todos
@router.get("/")
async def read_all(db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    return db.query(models.Todos).all()


@router.get("/user")
async def read_all_by_user(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    if user is None:
        raise get_user_exception()
    return db.query(models.Todos).filter(models.Todos.owner_id == user.get("id"))


# obtener todo por id
@router.get("/{todo_id}")
async def read_todo(todo_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get("id")).first()
    if todo_model is not None:
        return todo_model
    raise http_exception()

@router.post("/")
async def create_todo(todo: Todo, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    user = await get_current_user(request)

    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = models.Todos()
    todo_model.title = todo.title
    todo_model.description = todo.description
    todo_model.priority = todo.priority
    todo_model.complete = todo.complete
    todo_model.owner_id = user.get("id")

    db.add (todo_model)
    db.commit()

    return successful_response(201)

@router.put("/{todo_id}")
async def update_todo(todo_id: int, todo: Todo, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    
    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get("id")).first()
    
    if todo_model  is None:
        raise http_exception()
    
    todo_model.title = todo.title
    todo_model.description = todo.description
    todo_model.priority = todo.priority
    todo_model.complete = todo.complete

    db.add(todo_model)
    db.commit()

    return successful_response(200)

@router.delete("/{todo_id}")
async def delete_todo(todo_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo_model = db.query(models.Todos).filter(models.Todos.id == todo_id).filter(models.Todos.owner_id == user.get("id")).first()

    if todo_model  is None:
        raise http_exception()
    
    db.query(models.Todos).filter(models.Todos.id == todo_id).delete()
    
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


@router.get("/complete/{todo_id}", response_class=HTMLResponse)
async def complete_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):

    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)

    todo = db.query(models.Todos).filter(models.Todos.id == todo_id).first()

    todo.complete = not todo.complete

    db.add(todo)
    db.commit()

    return RedirectResponse(url="/todos", status_code=status.HTTP_302_FOUND)


def successful_response(status_code: int):
    return {
        'status': status_code,
        'transaction': 'Successful'
    }


def http_exception():
    return HTTPException(status_code=404, detail="Todo not found")