# Redline Core Project

Proyecto refactorizado al alcance actual del dealer, con **backend, frontend admin y esquema PostgreSQL sincronizados**.

# Video (acceso: [Redline](red.elrealplatano.com))

[![Video](https://img.youtube.com/vi/3U6OFTzFbyo/0.jpg)](https://youtu.be/3U6OFTzFbyo)

## Alcance activo
- sucursales
- usuarios, roles y permisos
- vehículos e imágenes
- clientes y preferencias
- ventas
- documentos y auditoría
- configuración general y reportes

## Alcance retirado
- SaaS / multi-dealer
- leads
- reservas
- portal público de ventas y favoritos

## Contenido
- `backend/`: API FastAPI + SQLAlchemy + Alembic
- `frontend/`: backoffice estático y página pública retirada del alcance
- `database/`: esquema SQL canónico para PostgreSQL
- `deploy/nginx/`: ejemplo de configuración Nginx
- `scripts/`: apoyo para reconstrucción

## Archivo de esquema recomendado
Usa este archivo como fuente de verdad de la base de datos:

- `database/redline_schema.sql`

Ese archivo único ya está alineado con:
- modelos SQLAlchemy activos
- enums de la aplicación
- `seed_auth.py`
- panel admin actual

## Requisitos previos

### PostgreSQL
Instala PostgreSQL y crea la base de datos:

```bash
# Debian / Ubuntu
sudo apt install postgresql

# RHEL / Fedora / CentOS
sudo dnf install postgresql-server

# openSUSE / SUSE
sudo zypper install postgresql-server

# macOS (Homebrew)
brew install postgresql@16
```

Crea el usuario y la base de datos:
```bash
sudo -u postgres psql <<EOF
CREATE USER redline WITH PASSWORD 'redline';
CREATE DATABASE redline OWNER redline;
EOF
```

## Backend
1. Entrar a la carpeta del backend
   ```bash
   cd backend
   ```
2. Crear entorno virtual e instalar dependencias
   ```bash
   python3 -m venv .deps
   source .deps/bin/activate
   pip install -r requirements.txt
   ```
3. Copiar variables de entorno
   ```bash
   cp .env.example .env
   ```
   Edita `.env` y ajusta `DATABASE_URL` con los datos de tu instancia PostgreSQL:
   ```
   DATABASE_URL=postgresql://redline:redline@localhost:5432/redline
   ```
4. Reconstruir el esquema
   ```bash
   psql -U redline -d redline < ../database/redline_schema.sql
   ```
5. Marcar migración base y sembrar usuario inicial
   ```bash
   alembic stamp head
   python3 -m app.db.seed_auth
   ```
6. Iniciar el servidor
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
7. *(Opcional)* Cargar datos demo para presentación
   ```bash
   python3 -m app.db.seed_demo
   ```
   Crea ~162 registros de ejemplo (sucursales, usuarios, clientes, vehículos, ventas).
   Contraseña de usuarios demo: `Demo123*`
   **No ejecutar en entornos con datos reales.**

## Frontend
Sirve la carpeta `frontend/` con Nginx o un servidor estático. El backoffice usa `/api/v1` como base.

## Usuario inicial
- Email: `admin@redline.com`
- Password: `Admin123*`

## Notas importantes
- `ALLOWED_ORIGINS` acepta formato JSON o coma-separado.
- El backend usa `search_path` hacia el esquema `redline`.
- Los enums PostgreSQL persisten los **values** (`active`, `disponible`, etc.) y no los nombres en mayúscula.
- `sales` ya no depende de `reservation_id`.
- El panel admin permite cargar imagen por archivo o por URL.
