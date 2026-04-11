# Integración actual

## Endpoints utilizados por el panel admin

- `GET/POST/PATCH /api/v1/branches`
- `GET/POST/PATCH/DELETE /api/v1/vehicles`
- `GET/POST /api/v1/vehicles/{vehicle_id}/images`
- `POST /api/v1/vehicles/{vehicle_id}/images/upload`
- `PATCH /api/v1/vehicles/{vehicle_id}/images/{image_id}/cover`
- `DELETE /api/v1/vehicles/{vehicle_id}/images/{image_id}`
- `GET/POST/PATCH/DELETE /api/v1/clients`
- `GET /api/v1/clients/{client_id}/history`
- `GET/POST/PATCH/DELETE /api/v1/sales`
- `GET /api/v1/sales/{sale_id}/pdf`
- `GET/PATCH /api/v1/settings`
- `GET /api/v1/reports/*`

## Alcance retirado

- `/api/v1/leads/*`
- `/api/v1/reservations/*`
- `/api/v1/portal/*`
