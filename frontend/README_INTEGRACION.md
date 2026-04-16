# Documentación de integración — API Redline

Base URL: `http://<host>/api/v1`
Autenticación: `Authorization: Bearer <token>` en todos los endpoints protegidos.
Formato: JSON (excepto endpoints de subida de archivos que usan `multipart/form-data`).

---

## Índice

1. [Autenticación](#1-autenticación)
2. [Usuarios](#2-usuarios)
3. [Roles y permisos](#3-roles-y-permisos)
4. [Sucursales](#4-sucursales)
5. [Vehículos](#5-vehículos)
6. [Clientes](#6-clientes)
7. [Ventas](#7-ventas)
8. [Documentos](#8-documentos)
9. [Búsqueda](#9-búsqueda)
10. [Reportes](#10-reportes)
11. [Configuración del sistema](#11-configuración-del-sistema)
12. [Catálogos](#12-catálogos)
13. [Importación masiva](#13-importación-masiva)
14. [Caché](#14-caché)
15. [Health](#15-health)
16. [Endpoints públicos (sin autenticación)](#16-endpoints-públicos-sin-autenticación)

---

## 1. Autenticación

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/auth/login` | Login con email y contraseña |
| `POST` | `/auth/token` | Alias de login (mismo comportamiento) |
| `GET`  | `/auth/me` | Retorna el usuario autenticado actual |

### `POST /auth/login`

**Body (JSON):**
```json
{
  "email": "admin@redline.com",
  "password": "secreto123"
}
```

**Respuesta 200:**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

---

### `GET /auth/me`

**Requiere:** Token válido.

**Respuesta 200:**
```json
{
  "id": "uuid",
  "full_name": "Admin General",
  "email": "admin@redline.com",
  "role": "admin",
  "permissions": ["vehicles.read", "vehicles.write", "..."],
  "branch_ids": ["uuid1", "uuid2"]
}
```

---

## 2. Usuarios

**Prefijo:** `/users`

| Método   | Ruta                        | Permiso requerido | Descripción |
|----------|-----------------------------|-------------------|-------------|
| `GET`    | `/users`                    | `users.read`      | Listar todos los usuarios |
| `POST`   | `/users`                    | `users.write`     | Crear usuario |
| `GET`    | `/users/{user_id}`          | `users.read`      | Obtener usuario por ID |
| `PATCH`  | `/users/{user_id}`          | `users.write`     | Actualizar usuario |
| `PATCH`  | `/users/{user_id}/status`   | `users.write`     | Cambiar estado (active/inactive) |
| `PUT`    | `/users/{user_id}/branches` | `users.write`     | Reemplazar sucursales asignadas |
| `DELETE` | `/users/{user_id}`          | `users.write`     | Eliminar usuario |

### Body: `POST /users`
```json
{
  "role_id": "uuid",
  "full_name": "Juan Pérez",
  "email": "juan@redline.com",
  "phone": "5551234567",
  "password": "min8chars",
  "status": "active",
  "branch_ids": ["uuid1", "uuid2"]
}
```

### Body: `PATCH /users/{user_id}`
Todos los campos son opcionales:
```json
{
  "role_id": "uuid",
  "full_name": "Nuevo nombre",
  "email": "nuevo@email.com",
  "phone": "555...",
  "password": "nuevaPass123",
  "status": "active"
}
```

### Body: `PATCH /users/{user_id}/status`
```json
{ "status": "active" }
```
Valores válidos: `active`, `inactive`.

### Body: `PUT /users/{user_id}/branches`
```json
{ "branch_ids": ["uuid1", "uuid2"] }
```

### Respuesta (UserResponse):
```json
{
  "id": "uuid",
  "role": { "id": "uuid", "name": "vendedor" },
  "full_name": "Juan Pérez",
  "email": "juan@redline.com",
  "phone": null,
  "status": "active",
  "last_login_at": "2025-01-01T00:00:00",
  "created_at": "...",
  "updated_at": "...",
  "branch_ids": ["uuid1"]
}
```

---

## 3. Roles y permisos

**Prefijo:** `/roles`

| Método | Ruta                 | Permiso requerido | Descripción |
|--------|----------------------|-------------------|-------------|
| `GET`  | `/roles`             | `roles.read`      | Listar roles del sistema |
| `GET`  | `/roles/permissions` | `roles.read`      | Listar todos los permisos disponibles |

### Respuesta `/roles`:
```json
[
  { "id": "uuid", "name": "admin", "permissions": ["vehicles.read", "..."] }
]
```

### Respuesta `/roles/permissions`:
```json
[
  { "id": "uuid", "codename": "vehicles.read", "description": "..." }
]
```

---

## 4. Sucursales

**Prefijo:** `/branches`

| Método   | Ruta                     | Permiso requerido  | Descripción |
|----------|--------------------------|--------------------|-------------|
| `GET`    | `/branches`              | `branches.read`    | Listar sucursales activas |
| `GET`    | `/branches/public`       | Sin auth           | Sucursales activas (uso público) |
| `POST`   | `/branches`              | `branches.write`   | Crear sucursal |
| `GET`    | `/branches/{branch_id}`  | `branches.read`    | Obtener sucursal por ID |
| `PATCH`  | `/branches/{branch_id}`  | `branches.write`   | Actualizar sucursal |
| `DELETE` | `/branches/{branch_id}`  | `branches.write`   | Eliminar sucursal |

### Body: `POST /branches`
```json
{
  "name": "Sucursal Norte",
  "address": "Av. Ejemplo 123",
  "phone": "555-0001",
  "email": "norte@redline.com"
}
```

### Body: `PATCH /branches/{branch_id}`
Todos los campos opcionales:
```json
{
  "name": "Nuevo nombre",
  "address": null,
  "phone": null,
  "email": null,
  "status": "inactive"
}
```

### Respuesta (BranchResponse):
```json
{
  "id": "uuid",
  "name": "Sucursal Norte",
  "address": "Av. Ejemplo 123",
  "phone": "555-0001",
  "email": "norte@redline.com",
  "status": "active",
  "created_at": "...",
  "updated_at": "..."
}
```

---

## 5. Vehículos

**Prefijo:** `/vehicles`

| Método   | Ruta                                              | Permiso requerido   | Descripción |
|----------|---------------------------------------------------|---------------------|-------------|
| `GET`    | `/vehicles`                                       | `vehicles.read`     | Listar vehículos (con filtros) |
| `POST`   | `/vehicles`                                       | `vehicles.write`    | Crear vehículo |
| `GET`    | `/vehicles/{vehicle_id}`                          | `vehicles.read`     | Obtener vehículo por ID |
| `PATCH`  | `/vehicles/{vehicle_id}`                          | `vehicles.write`    | Actualizar vehículo |
| `PATCH`  | `/vehicles/{vehicle_id}/status`                   | `vehicles.write`    | Cambiar estado del vehículo |
| `DELETE` | `/vehicles/{vehicle_id}`                          | `vehicles.write`    | Eliminar vehículo |
| `GET`    | `/vehicles/{vehicle_id}/status-history`           | `vehicles.read`     | Historial de estados |
| `GET`    | `/vehicles/{vehicle_id}/images`                   | `vehicles.read`     | Listar imágenes |
| `POST`   | `/vehicles/{vehicle_id}/images`                   | `vehicles.write`    | Agregar imagen por ruta de archivo |
| `POST`   | `/vehicles/{vehicle_id}/images/upload`            | `vehicles.write`    | Subir imagen (multipart) |
| `PATCH`  | `/vehicles/{vehicle_id}/images/{image_id}/cover`  | `vehicles.write`    | Marcar como portada |
| `PATCH`  | `/vehicles/{vehicle_id}/images/{image_id}/sort`   | `vehicles.write`    | Actualizar orden |
| `DELETE` | `/vehicles/{vehicle_id}/images/{image_id}`        | `vehicles.write`    | Eliminar imagen |

### Query params: `GET /vehicles`

| Parámetro | Tipo   | Descripción |
|-----------|--------|-------------|
| `status`  | string | Filtrar por estado (`disponible`, `vendido`, `reservado`, etc.) |
| `branch_id` | UUID | Filtrar por sucursal |
| `search`  | string | Búsqueda por marca, modelo, VIN, placa |

### Body: `POST /vehicles`
```json
{
  "branch_id": "uuid",
  "brand": "Toyota",
  "model": "Corolla",
  "vehicle_year": 2022,
  "price": 250000.00,
  "mileage": 15000,
  "vin": "1HGBH41JXMN109186",
  "plate": "ABC-123",
  "color": "Blanco",
  "transmission": "Automático",
  "fuel_type": "Gasolina",
  "vehicle_type": "Sedán",
  "description": "Excelente estado"
}
```

### Body: `PATCH /vehicles/{vehicle_id}/status`
```json
{
  "status": "vendido",
  "client_id": "uuid",
  "notes": "Pago de contado"
}
```
Estados válidos: `disponible`, `reservado`, `vendido`, `en_proceso`, `no_disponible`.

### Body: `POST /vehicles/{vehicle_id}/images` (por ruta)
```json
{
  "file_path": "/uploads/vehicles/<uuid>/foto.jpg",
  "sort_order": 0,
  "is_cover": true
}
```

### `POST /vehicles/{vehicle_id}/images/upload` (multipart/form-data)

| Campo        | Tipo     | Descripción |
|--------------|----------|-------------|
| `file`       | File     | Imagen (obligatorio) |
| `sort_order` | int      | Orden de presentación (default: 0) |
| `is_cover`   | bool     | Marcar como portada (default: false) |

---

## 6. Clientes

**Prefijo:** `/clients`

| Método   | Ruta                                              | Permiso requerido  | Descripción |
|----------|----------------------------------------------------|---------------------|-------------|
| `GET`    | `/clients`                                         | `clients.read`      | Listar clientes |
| `POST`   | `/clients`                                         | `clients.write`     | Crear cliente |
| `GET`    | `/clients/{client_id}`                             | `clients.read`      | Obtener cliente por ID |
| `PATCH`  | `/clients/{client_id}`                             | `clients.write`     | Actualizar cliente |
| `DELETE` | `/clients/{client_id}`                             | `clients.write`     | Eliminar cliente |
| `GET`    | `/clients/{client_id}/history`                     | `clients.read`      | Historial de ventas y eventos |
| `GET`    | `/clients/{client_id}/images`                      | `clients.read`      | Listar imágenes del cliente |
| `POST`   | `/clients/{client_id}/images`                      | `clients.write`     | Subir imagen (multipart) |
| `PATCH`  | `/clients/{client_id}/images/{image_id}/cover`     | `clients.write`     | Marcar imagen como portada |
| `PATCH`  | `/clients/{client_id}/images/{image_id}/sort`      | `clients.write`     | Actualizar orden de imagen |
| `DELETE` | `/clients/{client_id}/images/{image_id}`           | `clients.write`     | Eliminar imagen |

### Query params: `GET /clients`

| Parámetro | Tipo   | Descripción |
|-----------|--------|-------------|
| `search`  | string | Búsqueda por nombre, documento, email o teléfono |

### Body: `POST /clients`
```json
{
  "full_name": "María González",
  "document_type": "INE",
  "document_number": "GOME850101MDFXXX",
  "email": "maria@email.com",
  "phone": "5559876543",
  "alternate_phone": null,
  "address": "Calle Falsa 123",
  "notes": "Cliente frecuente",
  "preference": {
    "preferred_brands": ["Toyota", "Honda"],
    "price_min": 100000,
    "price_max": 300000,
    "vehicle_type": "Sedán",
    "transmission": "Automático",
    "fuel_type": "Gasolina",
    "color": "Blanco",
    "notes": "Prefiere 4 puertas"
  }
}
```

### Respuesta `/clients/{client_id}/history`:
```json
{
  "client_id": "uuid",
  "sales": [
    {
      "id": "uuid",
      "vehicle_id": "uuid",
      "branch_id": "uuid",
      "sale_date": "2025-01-15T00:00:00",
      "sale_price": 250000.00,
      "status": "completada"
    }
  ],
  "status_events": [
    {
      "id": "uuid",
      "vehicle_id": "uuid",
      "old_status": "disponible",
      "new_status": "reservado",
      "notes": null,
      "created_at": "2025-01-10T00:00:00"
    }
  ]
}
```

---

## 7. Ventas

**Prefijo:** `/sales`

| Método   | Ruta                  | Permiso requerido | Descripción |
|----------|-----------------------|-------------------|-------------|
| `GET`    | `/sales`              | `sales.read`      | Listar ventas |
| `POST`   | `/sales`              | `sales.write`     | Crear venta |
| `GET`    | `/sales/{sale_id}`    | `sales.read`      | Obtener venta por ID |
| `PATCH`  | `/sales/{sale_id}`    | `sales.write`     | Actualizar venta |
| `DELETE` | `/sales/{sale_id}`    | `sales.write`     | Eliminar venta |
| `GET`    | `/sales/{sale_id}/pdf` | `sales.read`     | Descargar PDF de contrato |

### Body: `POST /sales`
```json
{
  "vehicle_id": "uuid",
  "client_id": "uuid",
  "seller_user_id": "uuid",
  "branch_id": "uuid",
  "sale_price": 250000.00,
  "cost": 200000.00,
  "payment_method": "contado",
  "sale_date": "2025-06-01T10:00:00",
  "notes": "Incluye garantía 6 meses"
}
```
`seller_user_id`, `cost`, `payment_method`, `sale_date` y `notes` son opcionales.

### Respuesta (SaleResponse):
```json
{
  "id": "uuid",
  "vehicle_id": "uuid",
  "client_id": "uuid",
  "seller_user_id": "uuid",
  "branch_id": "uuid",
  "sale_date": "2025-06-01T10:00:00",
  "sale_price": 250000.00,
  "cost": 200000.00,
  "profit": 50000.00,
  "payment_method": "contado",
  "status": "completada",
  "notes": null,
  "created_at": "..."
}
```

### `GET /sales/{sale_id}/pdf`

Retorna el PDF del contrato de venta como archivo descargable (`Content-Type: application/pdf`).

---

## 8. Documentos

**Prefijo:** `/documents`

| Método   | Ruta                                         | Permiso requerido    | Descripción |
|----------|----------------------------------------------|----------------------|-------------|
| `GET`    | `/documents`                                 | `documents.read`     | Listar documentos (con filtros) |
| `POST`   | `/documents`                                 | `documents.write`    | Subir documento (multipart) |
| `GET`    | `/documents/{document_id}`                   | `documents.read`     | Obtener documento por ID |
| `GET`    | `/documents/{document_id}/download`          | `documents.read`     | Descargar archivo del documento |
| `PATCH`  | `/documents/{document_id}`                   | `documents.write`    | Actualizar metadatos del documento |
| `DELETE` | `/documents/{document_id}`                   | `documents.write`    | Eliminar documento |
| `GET`    | `/documents/entity/{entity_type}/{entity_id}`| `documents.read`     | Documentos de una entidad específica |

### Query params: `GET /documents`

| Parámetro       | Tipo   | Descripción |
|-----------------|--------|-------------|
| `entity_type`   | string | Tipo de entidad (`vehicles`, `clients`, `sales`) |
| `entity_id`     | UUID   | ID de la entidad |
| `document_type` | string | Tipo de documento (`factura`, `contrato`, etc.) |
| `skip`          | int    | Paginación (default: 0) |
| `limit`         | int    | Cantidad máxima (default: 50, máx: 100) |

### `POST /documents` (multipart/form-data)

| Campo           | Tipo   | Descripción |
|-----------------|--------|-------------|
| `file`          | File   | Archivo a subir (obligatorio) |
| `entity_type`   | string | Tipo de entidad (obligatorio) |
| `entity_id`     | UUID   | ID de la entidad (obligatorio) |
| `document_type` | string | Tipo de documento (obligatorio) |

---

## 9. Búsqueda

**Prefijo:** `/search`
**Requiere:** Cualquier usuario autenticado.

| Método | Ruta               | Descripción |
|--------|--------------------|-------------|
| `GET`  | `/search/vehicles` | Búsqueda avanzada de vehículos con facetas |
| `GET`  | `/search/clients`  | Búsqueda de clientes |
| `GET`  | `/search`          | Búsqueda unificada (vehículos + clientes) |
| `GET`  | `/search/suggest`  | Sugerencias de autocompletado |

### Query params: `GET /search/vehicles`

| Parámetro      | Tipo   | Descripción |
|----------------|--------|-------------|
| `q`            | string | Texto de búsqueda (obligatorio, mín. 1 caracter) |
| `branch_id`    | UUID   | Filtrar por sucursal |
| `status`       | string | Filtrar por estado |
| `price_min`    | float  | Precio mínimo |
| `price_max`    | float  | Precio máximo |
| `year_min`     | int    | Año mínimo |
| `year_max`     | int    | Año máximo |
| `fuel_type`    | string | Tipo de combustible |
| `transmission` | string | Tipo de transmisión |
| `vehicle_type` | string | Tipo de vehículo |
| `limit`        | int    | Resultados por página (1–100, default: 50) |
| `offset`       | int    | Desplazamiento (default: 0) |
| `facets`       | bool   | Incluir facetas de búsqueda (default: false) |

### Query params: `GET /search/clients`

| Parámetro       | Tipo   | Descripción |
|-----------------|--------|-------------|
| `q`             | string | Texto de búsqueda (obligatorio) |
| `document_type` | string | Filtrar por tipo de documento |
| `limit`         | int    | Resultados por página (1–100, default: 50) |
| `offset`        | int    | Desplazamiento (default: 0) |

### Query params: `GET /search` (unificado)

| Parámetro        | Tipo   | Descripción |
|------------------|--------|-------------|
| `q`              | string | Texto de búsqueda (obligatorio) |
| `types`          | string | Entidades a incluir (`vehicles`, `clients`) |
| `limit_per_type` | int    | Resultados por tipo (1–50, default: 10) |

### Query params: `GET /search/suggest`

| Parámetro   | Tipo   | Descripción |
|-------------|--------|-------------|
| `q`         | string | Texto parcial (obligatorio, mín. 1, máx. 50 caracteres) |
| `type`      | string | Tipo de entidad (`vehicles` o `clients`) |
| `limit`     | int    | Número de sugerencias (1–20, default: 10) |

---

## 10. Reportes

**Prefijo:** `/reports`
**Permiso requerido:** `reports.read` en todos los endpoints.

| Método | Ruta                        | Descripción |
|--------|-----------------------------|-------------|
| `GET`  | `/reports/dashboard`        | Resumen ejecutivo del dashboard |
| `GET`  | `/reports/inventory-summary`| Resumen de inventario por sucursal/estado |
| `GET`  | `/reports/sales-summary`    | Resumen de ventas agrupadas |
| `GET`  | `/reports/inventory-rows`   | Filas detalladas de inventario (exportable) |
| `GET`  | `/reports/sales-rows`       | Filas detalladas de ventas (exportable) |

### Respuesta `/reports/dashboard` (resumen):
```json
{
  "total_vehicles": 45,
  "available_vehicles": 30,
  "total_clients": 120,
  "total_sales": 15,
  "revenue_this_month": 3750000.00
}
```

---

## 11. Configuración del sistema

**Prefijo:** `/settings`

| Método  | Ruta        | Permiso requerido  | Descripción |
|---------|-------------|--------------------|-------------|
| `GET`   | `/settings` | `settings.read`    | Obtener configuración del sistema |
| `PATCH` | `/settings` | `settings.write`   | Actualizar configuración |

### Body: `PATCH /settings`
Todos los campos son opcionales:
```json
{
  "business_name": "Redline Autos",
  "logo_path": "/uploads/logo.png",
  "contact_email": "contacto@redline.com",
  "contact_phone": "555-0000",
  "whatsapp": "5551234567",
  "address": "Av. Principal 1",
  "facebook": "https://facebook.com/redline",
  "instagram": "https://instagram.com/redline",
  "website": "https://redline.com",
  "terms_and_conditions": "...",
  "privacy_policy": "..."
}
```

---

## 12. Catálogos

**Prefijo:** `/catalogs`
**Sin autenticación requerida.**

| Método | Ruta                       | Descripción |
|--------|----------------------------|-------------|
| `GET`  | `/catalogs/vehicles`       | Catálogo de vehículos disponibles al público |
| `GET`  | `/catalogs/vehicle-models` | Modelos de vehículos agrupados por marca |

---

## 13. Importación masiva

**Prefijo:** `/bulk`

| Método | Ruta                          | Permiso requerido  | Descripción |
|--------|-------------------------------|--------------------|-------------|
| `POST` | `/bulk/vehicles`              | `vehicles.write`   | Crear múltiples vehículos en JSON |
| `POST` | `/bulk/clients`               | `clients.write`    | Crear múltiples clientes en JSON |
| `POST` | `/bulk/vehicles/import`       | `vehicles.write`   | Importar vehículos desde archivo CSV |
| `POST` | `/bulk/clients/import`        | `clients.write`    | Importar clientes desde archivo CSV |
| `GET`  | `/bulk/templates/vehicles`    | `vehicles.write`   | Descargar plantilla CSV de vehículos |
| `GET`  | `/bulk/templates/clients`     | `clients.write`    | Descargar plantilla CSV de clientes |

### Body: `POST /bulk/vehicles`
```json
{
  "vehicles": [
    { "branch_id": "uuid", "brand": "Toyota", "model": "Camry", "vehicle_year": 2023, "price": 300000, "mileage": 0, "vin": "VIN001" }
  ]
}
```

### `POST /bulk/vehicles/import` (multipart/form-data)

| Campo  | Tipo | Descripción |
|--------|------|-------------|
| `file` | File | Archivo CSV con columnas según plantilla |

### Respuesta (BulkOperationResponse):
```json
{
  "created": 10,
  "failed": 2,
  "errors": [
    { "row": 3, "error": "VIN duplicado" }
  ]
}
```

---

## 14. Caché

**Prefijo:** `/cache`

| Método | Ruta             | Permiso requerido  | Descripción |
|--------|------------------|--------------------|-------------|
| `GET`  | `/cache/stats`   | `settings.read`    | Estadísticas del caché (Redis) |
| `GET`  | `/cache/keys`    | `settings.read`    | Listar claves en caché |
| `POST` | `/cache/clear`   | `settings.write`   | Limpiar todo el caché |
| `POST` | `/cache/warmup`  | `settings.write`   | Pre-cargar caché con datos frecuentes |

---

## 15. Health

**Prefijo:** `/health`
**Sin autenticación requerida.**

| Método | Ruta               | Descripción |
|--------|--------------------|-------------|
| `GET`  | `/health`          | Estado básico del servicio |
| `GET`  | `/health/detailed` | Estado detallado (DB, Redis, etc.) |
| `GET`  | `/health/ready`    | Kubernetes readiness probe |
| `GET`  | `/health/live`     | Kubernetes liveness probe |

---

## 16. Endpoints públicos (sin autenticación)

Estos endpoints son utilizados por el sitio web público (catálogo de vehículos).

| Método | Ruta                                          | Descripción |
|--------|-----------------------------------------------|-------------|
| `GET`  | `/branches/public`                            | Sucursales activas |
| `GET`  | `/vehicles/public`                            | Vehículos disponibles al público (con filtros) |
| `GET`  | `/vehicles/public/{vehicle_id}`               | Detalle público de un vehículo |
| `POST` | `/vehicles/public/{vehicle_id}/reserve`       | Reservar vehículo (captura datos del cliente) |
| `POST` | `/vehicles/public/{vehicle_id}/purchase_intent` | Registrar intención de compra |
| `GET`  | `/catalogs/vehicles`                          | Catálogo completo |
| `GET`  | `/catalogs/vehicle-models`                    | Marcas y modelos |
| `GET`  | `/health`                                     | Status del servicio |

### Query params: `GET /vehicles/public`

| Parámetro  | Tipo   | Descripción |
|------------|--------|-------------|
| `branch_id`| UUID   | Filtrar por sucursal |
| `search`   | string | Búsqueda por texto |
| `status`   | string | Estado (default: `disponible`) |
| `limit`    | int    | Cantidad máxima (1–500, default: 100) |

### Body: `POST /vehicles/public/{vehicle_id}/reserve`
```json
{
  "full_name": "Carlos López",
  "phone": "5559001122",
  "email": "carlos@email.com",
  "document_type": "INE",
  "document_number": "LOPC900101HDFXXX",
  "notes": "Quiero verlo el sábado"
}
```

### Respuesta:
```json
{
  "message": "Vehículo reservado exitosamente",
  "client_id": "uuid"
}
```

---

## Códigos de error comunes

| Código | Significado |
|--------|-------------|
| `400`  | Datos inválidos en el body |
| `401`  | Token ausente o inválido |
| `403`  | Sin permiso para el recurso |
| `404`  | Recurso no encontrado |
| `409`  | Conflicto (ej. VIN duplicado, vehículo ya reservado) |
| `422`  | Error de validación de Pydantic |
| `500`  | Error interno del servidor |

---

## Uso desde el frontend (`api.js`)

```js
// Llamada autenticada
const branches = await window.REDLINE.request('GET', '/branches');

// Con body
const vehicle = await window.REDLINE.request('POST', '/vehicles', {
  brand: 'Toyota',
  model: 'Corolla',
  // ...
});

// Subida de archivo
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('sort_order', '0');
formData.append('is_cover', 'true');
await window.REDLINE.request('POST', `/vehicles/${id}/images/upload`, formData);
```

El token JWT se lee de `localStorage.getItem('redline_token')` y se incluye automáticamente por `api.js`.
