from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.api.deps import require_permissions
from app.db.session import get_db
from app.models.user import User
from app.schemas.bulk import (
    BulkClientCreate,
    BulkOperationResponse,
    BulkVehicleCreate,
    CSVImportResponse,
    CSVImportResult,
)
from app.schemas.client import ClientCreate
from app.schemas.vehicle import VehicleCreate
from app.services.bulk_service import (
    process_bulk_clients,
    process_bulk_vehicles,
    process_csv_import,
    validate_csv_headers,
)

router = APIRouter(prefix="/bulk", tags=["bulk"])

_MAX_CSV_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/vehicles", response_model=BulkOperationResponse)
async def bulk_create_vehicles(
    payload: BulkVehicleCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("vehicles.write"))],
) -> BulkOperationResponse:
    """Create multiple vehicles in bulk"""
    return await process_bulk_vehicles(db, payload.vehicles, current_user.id)


@router.post("/clients", response_model=BulkOperationResponse)
async def bulk_create_clients(
    payload: BulkClientCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("clients.write"))],
) -> BulkOperationResponse:
    """Create multiple clients in bulk"""
    return await process_bulk_clients(db, payload.clients, current_user.id)


@router.post("/vehicles/import", response_model=CSVImportResponse)
async def import_vehicles_csv(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("vehicles.write"))],
) -> CSVImportResponse:
    """Import vehicles from CSV file"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Solo archivos CSV son permitidos")

    # Validate CSV headers
    content = await file.read()
    if len(content) > _MAX_CSV_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="El archivo CSV supera el límite de 10 MB")
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400, detail="El archivo CSV debe estar codificado en UTF-8"
        ) from exc

    required_headers = ["branch_id", "brand", "model", "vehicle_year", "price", "vin"]
    missing = validate_csv_headers(text_content, required_headers)
    if missing:
        raise HTTPException(
            status_code=400, detail=f"Headers requeridos faltantes: {', '.join(missing)}"
        )

    # Reset file pointer
    file.file.seek(0)

    # Process CSV
    valid_vehicles, csv_errors = await process_csv_import(
        file, VehicleCreate, db, current_user.id, "vehicles"
    )

    # Process valid vehicles
    if valid_vehicles:
        bulk_result = await process_bulk_vehicles(db, valid_vehicles, current_user.id)
        successful = bulk_result.successful
        failed = bulk_result.failed + len(csv_errors)
    else:
        successful = 0
        failed = len(csv_errors)

    return CSVImportResponse(
        result=CSVImportResult(
            total_rows=len(valid_vehicles) + len(csv_errors),
            processed=len(valid_vehicles) + len(csv_errors),
            successful=successful,
            failed=failed,
            errors=csv_errors,
        ),
        created_ids=[r.id for r in bulk_result.results if r.success and r.id]
        if valid_vehicles
        else [],
    )


@router.post("/clients/import", response_model=CSVImportResponse)
async def import_clients_csv(
    file: Annotated[UploadFile, File()],
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_permissions("clients.write"))],
) -> CSVImportResponse:
    """Import clients from CSV file"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Solo archivos CSV son permitidos")

    # Validate CSV headers
    content = await file.read()
    if len(content) > _MAX_CSV_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="El archivo CSV supera el límite de 10 MB")
    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400, detail="El archivo CSV debe estar codificado en UTF-8"
        ) from exc

    required_headers = ["full_name", "email"]
    missing = validate_csv_headers(text_content, required_headers)
    if missing:
        raise HTTPException(
            status_code=400, detail=f"Headers requeridos faltantes: {', '.join(missing)}"
        )

    # Reset file pointer
    file.file.seek(0)

    # Process CSV
    valid_clients, csv_errors = await process_csv_import(
        file, ClientCreate, db, current_user.id, "clients"
    )

    # Process valid clients
    if valid_clients:
        bulk_result = await process_bulk_clients(db, valid_clients, current_user.id)
        successful = bulk_result.successful
        failed = bulk_result.failed + len(csv_errors)
    else:
        successful = 0
        failed = len(csv_errors)

    return CSVImportResponse(
        result=CSVImportResult(
            total_rows=len(valid_clients) + len(csv_errors),
            processed=len(valid_clients) + len(csv_errors),
            successful=successful,
            failed=failed,
            errors=csv_errors,
        ),
        created_ids=[r.id for r in bulk_result.results if r.success and r.id]
        if valid_clients
        else [],
    )


@router.get("/templates/vehicles")
def get_vehicle_csv_template():
    """Download CSV template for vehicle import"""
    template = """branch_id,brand,model,vehicle_year,price,mileage,vin,plate,color,transmission,fuel_type,vehicle_type,description
550e8400-e29b-41d4-a716-446655440000,Toyota,Corolla,2020,15000,50000,1HGCM82633A123456,ABC-123,Blanco,Manual,Gasolina,Sedan,Vehículo en excelente estado"""

    return {
        "filename": "vehicle_import_template.csv",
        "content": template,
        "headers": {
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment; filename=vehicle_import_template.csv",
        },
    }


@router.get("/templates/clients")
def get_client_csv_template():
    """Download CSV template for client import"""
    template = """full_name,email,phone,document_type,document_number,address,notes
Juan Pérez,juan@email.com,+18091234567,cedula,001123456789,Santo Domingo,Cliente preferencial"""

    return {
        "filename": "client_import_template.csv",
        "content": template,
        "headers": {
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment; filename=client_import_template.csv",
        },
    }
