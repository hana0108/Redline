# Backend Redline

API FastAPI para el dealership de vehículos Redline.

**Stack**: FastAPI + SQLAlchemy 2.0 + PostgreSQL 13+ + Alembic

---

## Inicio Rápido

### 1. Preparar entorno

```bash
python3 -m venv .deps
source .deps/bin/activate
pip install -r requirements.txt
```

### 2. Variables de entorno

```bash
cp .env.example .env
# Configurar DATABASE_URL, SECRET_KEY, ALLOWED_ORIGINS, etc.
```

### 3. Inicializar base de datos

```bash
# Si es nueva instalación:
podman exec -i -u postgres arca psql -d redline < ../database/redline_schema.sql

# Marcar como migrada:
alembic stamp head

# Sembrar datos iniciales (admin@redline.com / Admin123*):
python3 -m app.db.seed_auth
```

### 4. Datos demo (opcional)

El seed de demo **no se ejecuta automáticamente**. Para cargar datos de presentación
(sucursales, usuarios, clientes, vehículos y ventas de ejemplo) ejecutar manualmente:

```bash
python3 -m app.db.seed_demo
```

Crea ~162 registros. Idempotente: si los datos ya existen, no hace nada.
Contraseña de los usuarios demo: `Demo123*`

> **Nota**: No correr en producción con datos reales.

### 4. Ejecutar servidor

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## Autenticación

Todos los endpoints (excepto `/auth/login`) requieren token JWT en header:

```http
Authorization: Bearer <token>
```

### Endpoints de Autenticación

| Método | Endpoint | Descripción | Autenticación |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/login` | Login con email/password, retorna token | ❌ No |
| GET | `/api/v1/auth/me` | Usuario actual del token | ✅ Sí |
| POST | `/api/v1/auth/logout` | Logout (limpia estado) | ✅ Sí |

**Respuesta login:**
```json
{
  "access_token": "token_jwt",
  "token_type": "bearer",
  "user": { "id": "uuid", "email": "...", "role": "admin", ... }
}
```

---

## Autorización

Basada en **roles y permisos**. Usuario inicial:
- **Email**: `admin@redline.com`
- **Password**: `Admin123*`
- **Rol**: `admin` (todos los permisos)

Permisos por módulo:
- `branches.read` / `branches.write` / `branches.delete`
- `users.read` / `users.write` / `users.delete`
- `roles.read`
- `vehicles.read` / `vehicles.write` / `vehicles.delete`
- `clients.read` / `clients.write` / `clients.delete`
- `sales.read` / `sales.write` / `sales.delete`
- `settings.read` / `settings.write`
- `reports.read`

---

## API Endpoints por Categoría

### 🏢 Sucursales (Branches)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/v1/branches` | Listar todas las sucursales | `branches.read` |
| POST | `/api/v1/branches` | Crear sucursal | `branches.write` |
| GET | `/api/v1/branches/{id}` | Obtener sucursal por ID | `branches.read` |
| PATCH | `/api/v1/branches/{id}` | Actualizar sucursal | `branches.write` |
| DELETE | `/api/v1/branches/{id}` | Eliminar sucursal | `branches.write` |

**Validaciones DELETE**: No puede tener vehículos ni ventas asociados.

---

### 👥 Usuarios (Users)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/v1/users` | Listar usuarios | `users.read` |
| POST | `/api/v1/users` | Crear usuario | `users.write` |
| GET | `/api/v1/users/{id}` | Obtener usuario por ID | `users.read` |
| PATCH | `/api/v1/users/{id}` | Actualizar usuario | `users.write` |
| PATCH | `/api/v1/users/{id}/status` | Cambiar status (active/inactive) | `users.write` |
| PUT | `/api/v1/users/{id}/branches` | Reemplazar sucursales del usuario | `users.write` |
| DELETE | `/api/v1/users/{id}` | Eliminar usuario | `users.write` |

**Validaciones DELETE**:
- No puede auto-eliminarse
- No puede eliminar admin principal
- No puede tener ventas registradas

---

### 🔐 Roles & Permisos

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/v1/roles` | Listar roles | `roles.read` |
| GET | `/api/v1/roles/permissions` | Listar todos los permisos | `roles.read` |

*Nota*: Roles y permisos son solo lectura. Se configuran vía seed o directamente en BD.

---

### 🚗 Vehículos (Vehicles)

#### Vehículos - CRUD

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/v1/vehicles` | Listar vehículos (con filtros) | `vehicles.read` |
| | | Query params: `status`, `branch_id`, `search` | |
| POST | `/api/v1/vehicles` | Crear vehículo | `vehicles.write` |
| GET | `/api/v1/vehicles/{id}` | Obtener vehículo | `vehicles.read` |
| PATCH | `/api/v1/vehicles/{id}` | Actualizar vehículo | `vehicles.write` |
| DELETE | `/api/v1/vehicles/{id}` | Eliminar vehículo | `vehicles.write` |

#### Vehículos - Estado

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| PATCH | `/api/v1/vehicles/{id}/status` | Cambiar estado con historial | `vehicles.write` |

**Estados permitidos**: `disponible`, `reservado`, `vendido`, `en_proceso`, `retirado`

**Validación**: Cambiar a `disponible` o `en_proceso` requiere **≥1 imagen**.

#### Vehículos - Imágenes

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/v1/vehicles/{id}/images` | Listar imágenes del vehículo | `vehicles.read` |
| POST | `/api/v1/vehicles/{id}/images` | Crear imagen desde ruta/URL | `vehicles.write` |
| POST | `/api/v1/vehicles/{id}/images/upload` | Upload multipart (archivo) | `vehicles.write` |
| PATCH | `/api/v1/vehicles/{id}/images/{img_id}/cover` | Marcar como portada | `vehicles.write` |
| PATCH | `/api/v1/vehicles/{id}/images/{img_id}/sort` | Actualizar orden | `vehicles.write` |
| DELETE | `/api/v1/vehicles/{id}/images/{img_id}` | Eliminar imagen | `vehicles.write` |

**Respuesta imagen:**
```json
{
  "id": "uuid",
  "file_path": "/media/vehicles/...",
  "sort_order": 0,
  "is_cover": true,
  "created_at": "ISO8601"
}
```

---

### 👤 Clientes (Clients)

#### Clientes - CRUD

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/v1/clients` | Listar clientes (con búsqueda) | `clients.read` |
| | | Query param: `search` | |
| POST | `/api/v1/clients` | Crear cliente (+ preferencias opcional) | `clients.write` |
| GET | `/api/v1/clients/{id}` | Obtener cliente | `clients.read` |
| PATCH | `/api/v1/clients/{id}` | Actualizar cliente | `clients.write` |
| DELETE | `/api/v1/clients/{id}` | Eliminar cliente | `clients.write` |

**Validación DELETE**: No puede tener ventas asociadas.

#### Clientes - Historial

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/v1/clients/{id}/history` | Historial de compras del cliente | `clients.read` |

#### Clientes - Imágenes

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/v1/clients/{id}/images` | Listar imágenes del cliente (opcional) | `clients.read` |
| POST | `/api/v1/clients/{id}/images` | Upload de foto multipart | `clients.write` |
| PATCH | `/api/v1/clients/{id}/images/{img_id}/cover` | Marcar como portada | `clients.write` |
| PATCH | `/api/v1/clients/{id}/images/{img_id}/sort` | Actualizar orden | `clients.write` |
| DELETE | `/api/v1/clients/{id}/images/{img_id}` | Eliminar imagen | `clients.write` |

**Nota**: Imágenes de clientes son **opcionales** (a diferencia de vehículos).

---

### � Documentos (Documents)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/v1/documents` | Listar documentos con filtros | `documents.read` |
| | | Query params: `entity_type`, `entity_id`, `document_type`, `skip`, `limit` | |
| POST | `/api/v1/documents` | Subir documento | `documents.write` |
| | | Form data: `file`, `entity_type`, `entity_id`, `document_type` | |
| GET | `/api/v1/documents/{id}` | Obtener documento | `documents.read` |
| GET | `/api/v1/documents/{id}/download` | Descargar archivo | `documents.read` |
| PATCH | `/api/v1/documents/{id}` | Actualizar tipo de documento | `documents.write` |
| DELETE | `/api/v1/documents/{id}` | Eliminar documento | `documents.write` |
| GET | `/api/v1/documents/entity/{entity_type}/{entity_id}` | Documentos por entidad | `documents.read` |

**Tipos de documento:**
- `venta_pdf` - PDFs de ventas
- `otro` - Otros documentos

**Entidades soportadas:**
- `vehicles` - Documentos de vehículos
- `clients` - Documentos de clientes
- `sales` - Documentos de ventas
- `branches` - Documentos de sucursales

**Formatos permitidos:** PDF, DOC, DOCX, XLS, XLSX, TXT, JPG, JPEG, PNG

---

### �💰 Ventas (Sales)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/v1/sales` | Listar ventas | `sales.read` |
| POST | `/api/v1/sales` | Registrar venta (cambia vehículo a vendido) | `sales.write` |
| GET | `/api/v1/sales/{id}` | Obtener venta | `sales.read` |
| PATCH | `/api/v1/sales/{id}` | Actualizar venta | `sales.write` |
| DELETE | `/api/v1/sales/{id}` | Anular venta (vehículo vuelve a disponible) | `sales.write` |
| GET | `/api/v1/sales/{id}/pdf` | Descargar PDF de venta | `sales.read` |

**Estados**: `completada`, `anulada`

---

### ⚙️ Configuración (Settings)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/v1/settings` | Obtener configuración general | `settings.read` |
| PATCH | `/api/v1/settings` | Actualizar configuración del negocio | `settings.write` |

**Campos**: business_name, logo_path, contact_email, contact_phone, whatsapp, address, facebook, instagram, website, terms_and_conditions, privacy_policy

---

### 📊 Reportes (Reports)

| Método | Endpoint | Descripción | Permisos |
|--------|----------|-------------|----------|
| GET | `/api/v1/reports/dashboard` | Resumen dashboard (total vehículos, ventas, etc.) | `reports.read` |
| GET | `/api/v1/reports/inventory/summary` | Resumen inventario por status | `reports.read` |
| GET | `/api/v1/reports/inventory/rows` | Filas de inventario detallado | `reports.read` |
| GET | `/api/v1/reports/sales/summary` | Resumen de ventas (total, promedio, etc.) | `reports.read` |
| GET | `/api/v1/reports/sales/rows` | Filas de ventas detallado | `reports.read` |

---

## Estructura de datos

### Vehicle Status
- `disponible` - Listo para vender
- `en_proceso` - En negociación (requiere ≥1 imagen)
- `reservado` - Cliente reservó
- `vendido` - Venta completada
- `retirado` - No disponible

### Sale Status
- `completada` - Venta registrada
- `anulada` - Venta cancelada (vehículo retorna a disponible)

### User/Branch Status
- `active` - Activo
- `inactive` - Inactivo

---

## Códigos de Error

| Código | Escenario |
|--------|-----------|
| 400 | Validación fallida (ej: foto obligatoria en vehículo) |
| 401 | Token inválido o expirado |
| 403 | Permiso insuficiente |
| 404 | Recurso no encontrado |
| 409 | Conflicto (ej: email duplicado, vehículo con historial) |
| 422 | Validación de Pydantic fallida |

---

## Migraciones Alembic

```bash
# Listar migraciones
alembic history

# Ejecutar hasta head
alembic upgrade head

# Revertir última migración
alembic downgrade -1
```

**Versiones actuales:**
- `0001_initial_schema` - Schema inicial (branches, users, vehicles, clients, sales, etc.)
- `0002_client_images` - Tabla `client_images` (fotos opcionales de clientes)

---

## Auditoría y Logs

Todas las operaciones CRUD se registran en tabla `audit_logs`:
- Usuario que realizó la acción
- Tipo de acción (create, update, delete, login, status_change, sale)
- Entidad afectada (id, tipo)
- Datos anteriores y nuevos (JSON)
- IP address
- Timestamp

---

## Media/Almacenamiento

Archivos guardados en directorio `media/`:
- `media/vehicles/{vehicle_id}/` - Imágenes de vehículos
- `media/clients/{client_id}/` - Imágenes de clientes
- Acceso público vía: `GET /media/...`

---

## Notas de Producción

- **CORS**: Configure `ALLOWED_ORIGINS` en `.env` (formato JSON o coma-separado)
- **JWT**: Configure `SECRET_KEY` seguro en `.env`
- **Database**: Use `search_path = 'redline'` para aislar schema
- **Media path**: Configure ruta persistente (volumen en Docker) para `/media/`
- **Email**: Configurable vía `ALLOWED_ORIGINS` y otros settings
