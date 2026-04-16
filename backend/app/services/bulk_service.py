from __future__ import annotations

import csv
import io
from typing import Any, Type
from uuid import UUID

from fastapi import UploadFile
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.branch import Branch
from app.models.client import Client, ClientPreference
from app.models.vehicle import Vehicle
from app.schemas.bulk import BulkOperationResult, BulkOperationResponse
from app.schemas.client import ClientCreate
from app.schemas.vehicle import VehicleCreate


async def process_bulk_vehicles(
    db: Session, vehicles_data: list[VehicleCreate], current_user_id: UUID
) -> BulkOperationResponse:
    """Process bulk vehicle creation with error handling"""
    results = []
    successful = 0
    failed = 0

    for i, vehicle_data in enumerate(vehicles_data, 1):
        try:
            # Validate branch exists
            branch = db.scalar(select(Branch).where(Branch.id == vehicle_data.branch_id))
            if not branch:
                results.append(BulkOperationResult(
                    success=False,
                    row_number=i,
                    errors=["Sucursal no encontrada"]
                ))
                failed += 1
                continue

            # Create vehicle
            vehicle = Vehicle(**vehicle_data.model_dump(), created_by=current_user_id)
            db.add(vehicle)
            db.flush()  # Get ID without committing

            results.append(BulkOperationResult(
                success=True,
                id=vehicle.id,
                row_number=i
            ))
            successful += 1

        except IntegrityError as e:
            db.rollback()
            error_msg = "VIN duplicado o datos inválidos"
            if "vin" in str(e).lower():
                error_msg = "VIN ya existe"
            results.append(BulkOperationResult(
                success=False,
                row_number=i,
                errors=[error_msg]
            ))
            failed += 1
        except Exception as e:
            db.rollback()
            results.append(BulkOperationResult(
                success=False,
                row_number=i,
                errors=[f"Error inesperado: {str(e)}"]
            ))
            failed += 1

    # Commit all successful operations
    try:
        db.commit()
    except Exception:
        db.rollback()
        # If commit fails, mark all as failed
        for result in results:
            if result.success:
                result.success = False
                result.errors = ["Error al guardar cambios"]
                successful -= 1
                failed += 1

    return BulkOperationResponse(
        total_processed=len(vehicles_data),
        successful=successful,
        failed=failed,
        results=results
    )


async def process_bulk_clients(
    db: Session, clients_data: list[ClientCreate], current_user_id: UUID
) -> BulkOperationResponse:
    """Process bulk client creation with error handling"""
    results = []
    successful = 0
    failed = 0

    for i, client_data in enumerate(clients_data, 1):
        try:
            # Create client
            client_dict = client_data.model_dump(exclude={"preference"})
            client = Client(**client_dict, created_by=current_user_id)
            db.add(client)
            db.flush()

            # Add preference if provided
            if client_data.preference:
                preference = ClientPreference(
                    client_id=client.id,
                    **client_data.preference.model_dump()
                )
                db.add(preference)

            results.append(BulkOperationResult(
                success=True,
                id=client.id,
                row_number=i
            ))
            successful += 1

        except IntegrityError as e:
            db.rollback()
            error_msg = "Email duplicado o datos inválidos"
            if "email" in str(e).lower():
                error_msg = "Email ya existe"
            results.append(BulkOperationResult(
                success=False,
                row_number=i,
                errors=[error_msg]
            ))
            failed += 1
        except Exception as e:
            db.rollback()
            results.append(BulkOperationResult(
                success=False,
                row_number=i,
                errors=[f"Error inesperado: {str(e)}"]
            ))
            failed += 1

    # Commit all successful operations
    try:
        db.commit()
    except Exception:
        db.rollback()
        for result in results:
            if result.success:
                result.success = False
                result.errors = ["Error al guardar cambios"]
                successful -= 1
                failed += 1

    return BulkOperationResponse(
        total_processed=len(clients_data),
        successful=successful,
        failed=failed,
        results=results
    )


async def process_csv_import(
    file: UploadFile,
    model_class: Type[BaseModel],
    db: Session,
    current_user_id: UUID,
    entity_type: str
) -> tuple[list[BaseModel], list[dict[str, Any]]]:
    """Process CSV file and return valid objects and errors"""
    content = await file.read()
    text_content = content.decode('utf-8')

    # Parse CSV
    csv_reader = csv.DictReader(io.StringIO(text_content))
    rows = list(csv_reader)

    valid_objects = []
    errors = []

    for i, row in enumerate(rows, 1):
        try:
            # Clean row data (remove empty strings)
            cleaned_row = {k: v.strip() for k, v in row.items() if v and v.strip()}

            # Validate with Pydantic model
            obj = model_class(**cleaned_row)
            valid_objects.append(obj)

        except ValidationError as e:
            error_details = []
            for error in e.errors():
                field = error.get('loc', ['unknown'])[0]
                msg = error.get('msg', 'Error de validación')
                error_details.append(f"{field}: {msg}")

            errors.append({
                "row": i,
                "data": row,
                "errors": error_details
            })

    return valid_objects, errors


def validate_csv_headers(csv_content: str, required_headers: list[str]) -> list[str]:
    """Validate that CSV has required headers"""
    sample = csv_content[:1024]  # Read first 1KB
    csv_reader = csv.reader(io.StringIO(sample))
    headers = next(csv_reader, [])

    missing = []
    for required in required_headers:
        if required not in headers:
            missing.append(required)

    return missing