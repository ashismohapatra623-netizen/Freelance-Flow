"""
Client CRUD routes.
Phase 1: Uses hardcoded user_id. Phase 2 will replace with JWT auth.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.client import Client
from models.project import Project
from schemas.client import ClientCreate, ClientUpdate, ClientResponse, ClientListResponse
from middleware.auth import get_current_user_id

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.get("", response_model=List[ClientListResponse])
def list_clients(
    status: Optional[str] = Query(None, pattern="^(active|inactive)$"),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all clients for the current user, optionally filtered by status."""
    query = db.query(Client).filter(Client.user_id == user_id)
    if status:
        query = query.filter(Client.status == status)
    clients = query.order_by(Client.created_at.desc()).all()

    result = []
    for client in clients:
        project_count = db.query(func.count(Project.id)).filter(Project.client_id == client.id).scalar()
        result.append(ClientListResponse(
            id=client.id,
            name=client.name,
            email=client.email,
            company=client.company,
            status=client.status,
            project_count=project_count,
            created_at=client.created_at,
        ))
    return result


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get a single client by ID."""
    client = db.query(Client).filter(Client.id == client_id, Client.user_id == user_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    project_count = db.query(func.count(Project.id)).filter(Project.client_id == client.id).scalar()

    return ClientResponse(
        id=client.id,
        user_id=client.user_id,
        name=client.name,
        email=client.email,
        phone=client.phone,
        company=client.company,
        notes=client.notes,
        status=client.status,
        created_at=client.created_at,
        updated_at=client.updated_at,
        project_count=project_count,
    )


@router.post("", response_model=ClientResponse, status_code=201)
def create_client(
    data: ClientCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Create a new client."""
    client = Client(
        user_id=user_id,
        name=data.name,
        email=data.email,
        phone=data.phone,
        company=data.company,
        notes=data.notes,
        status=data.status,
    )
    db.add(client)
    db.commit()
    db.refresh(client)

    return ClientResponse(
        id=client.id,
        user_id=client.user_id,
        name=client.name,
        email=client.email,
        phone=client.phone,
        company=client.company,
        notes=client.notes,
        status=client.status,
        created_at=client.created_at,
        updated_at=client.updated_at,
        project_count=0,
    )


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: str,
    data: ClientUpdate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Update an existing client."""
    client = db.query(Client).filter(Client.id == client_id, Client.user_id == user_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)

    project_count = db.query(func.count(Project.id)).filter(Project.client_id == client.id).scalar()

    return ClientResponse(
        id=client.id,
        user_id=client.user_id,
        name=client.name,
        email=client.email,
        phone=client.phone,
        company=client.company,
        notes=client.notes,
        status=client.status,
        created_at=client.created_at,
        updated_at=client.updated_at,
        project_count=project_count,
    )


@router.delete("/{client_id}", status_code=204)
def delete_client(
    client_id: str,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Delete a client and cascade to all projects/tasks."""
    client = db.query(Client).filter(Client.id == client_id, Client.user_id == user_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    db.delete(client)
    db.commit()
    return None
