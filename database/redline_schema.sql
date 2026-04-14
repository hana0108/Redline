-- Redline canonical database schema
-- Fuente única de verdad para inicializar PostgreSQL
-- Alcance actual: sucursales, usuarios/roles, clientes, vehículos, ventas, documentos y auditoría.

BEGIN;

CREATE SCHEMA IF NOT EXISTS redline;
SET search_path TO redline, public;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'status_generic' AND n.nspname = 'redline') THEN
        CREATE TYPE redline.status_generic AS ENUM ('active', 'inactive');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'vehicle_status' AND n.nspname = 'redline') THEN
        CREATE TYPE redline.vehicle_status AS ENUM ('disponible', 'reservado', 'vendido', 'en_proceso', 'retirado');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'sale_status' AND n.nspname = 'redline') THEN
        CREATE TYPE redline.sale_status AS ENUM ('completada', 'anulada');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'document_type' AND n.nspname = 'redline') THEN
        CREATE TYPE redline.document_type AS ENUM ('venta_pdf', 'otro');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace WHERE t.typname = 'audit_action' AND n.nspname = 'redline') THEN
        CREATE TYPE redline.audit_action AS ENUM ('create', 'update', 'delete', 'login', 'logout', 'status_change', 'sale');
    END IF;
END $$;

CREATE OR REPLACE FUNCTION redline.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TABLE IF NOT EXISTS redline.branches (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name varchar(150) NOT NULL,
    address text,
    phone varchar(30),
    email varchar(150),
    status redline.status_generic NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS redline.roles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    name varchar(100) NOT NULL UNIQUE,
    description text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS redline.permissions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(100) NOT NULL UNIQUE,
    name varchar(150) NOT NULL,
    description text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS redline.role_permissions (
    role_id uuid NOT NULL REFERENCES redline.roles(id) ON DELETE CASCADE,
    permission_id uuid NOT NULL REFERENCES redline.permissions(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS redline.users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id uuid NOT NULL REFERENCES redline.roles(id),
    full_name varchar(180) NOT NULL,
    email varchar(150) NOT NULL UNIQUE,
    phone varchar(30),
    password_hash text NOT NULL,
    status redline.status_generic NOT NULL DEFAULT 'active',
    last_login_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS redline.user_branch_access (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES redline.users(id) ON DELETE CASCADE,
    branch_id uuid NOT NULL REFERENCES redline.branches(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_branch_access UNIQUE (user_id, branch_id)
);

CREATE TABLE IF NOT EXISTS redline.system_settings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    business_name varchar(180) NOT NULL,
    logo_path text,
    contact_email varchar(150),
    contact_phone varchar(30),
    whatsapp varchar(30),
    address text,
    facebook varchar(255),
    instagram varchar(255),
    website varchar(255),
    terms_and_conditions text,
    privacy_policy text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS redline.vehicles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    branch_id uuid NOT NULL REFERENCES redline.branches(id),
    brand varchar(100) NOT NULL,
    model varchar(100) NOT NULL,
    vehicle_year integer NOT NULL CHECK (vehicle_year BETWEEN 1900 AND 2100),
    price numeric(14,2) NOT NULL CHECK (price >= 0),
    mileage integer NOT NULL DEFAULT 0 CHECK (mileage >= 0),
    vin varchar(50) NOT NULL UNIQUE,
    plate varchar(30),
    color varchar(50),
    transmission varchar(50),
    fuel_type varchar(50),
    vehicle_type varchar(50),
    description text,
    status redline.vehicle_status NOT NULL DEFAULT 'disponible',
    created_by uuid REFERENCES redline.users(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vehicles_branch_status ON redline.vehicles(branch_id, status);
CREATE INDEX IF NOT EXISTS idx_vehicles_brand_model_year ON redline.vehicles(brand, model, vehicle_year);
CREATE INDEX IF NOT EXISTS idx_vehicles_price ON redline.vehicles(price);
CREATE INDEX IF NOT EXISTS idx_vehicles_plate ON redline.vehicles(plate);

CREATE TABLE IF NOT EXISTS redline.vehicle_images (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id uuid NOT NULL REFERENCES redline.vehicles(id) ON DELETE CASCADE,
    file_path text NOT NULL,
    sort_order integer NOT NULL DEFAULT 0,
    is_cover boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vehicle_images_vehicle ON redline.vehicle_images(vehicle_id);

CREATE TABLE IF NOT EXISTS redline.vehicle_status_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id uuid NOT NULL REFERENCES redline.vehicles(id) ON DELETE CASCADE,
    old_status redline.vehicle_status,
    new_status redline.vehicle_status NOT NULL,
    changed_by uuid REFERENCES redline.users(id),
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS redline.vehicle_brands (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    name varchar(150) NOT NULL,
    sort_order integer NOT NULL DEFAULT 0,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vehicle_brands_active_sort ON redline.vehicle_brands(is_active, sort_order);

CREATE TABLE IF NOT EXISTS redline.vehicle_models_catalog (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    brand_id uuid NOT NULL REFERENCES redline.vehicle_brands(id) ON DELETE CASCADE,
    code varchar(50) NOT NULL,
    name varchar(150) NOT NULL,
    sort_order integer NOT NULL DEFAULT 0,
    is_active boolean NOT NULL DEFAULT true,
    default_vehicle_type varchar(50),
    default_transmission varchar(50),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_vehicle_models_catalog_brand_code UNIQUE (brand_id, code)
);

-- Idempotent: add hint columns on existing installations
ALTER TABLE redline.vehicle_models_catalog
    ADD COLUMN IF NOT EXISTS default_vehicle_type varchar(50),
    ADD COLUMN IF NOT EXISTS default_transmission varchar(50);

CREATE INDEX IF NOT EXISTS idx_vehicle_models_catalog_brand_active_sort ON redline.vehicle_models_catalog(brand_id, is_active, sort_order);

CREATE TABLE IF NOT EXISTS redline.vehicle_types_catalog (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    name varchar(150) NOT NULL,
    sort_order integer NOT NULL DEFAULT 0,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vehicle_types_catalog_active_sort ON redline.vehicle_types_catalog(is_active, sort_order);

CREATE TABLE IF NOT EXISTS redline.fuel_types_catalog (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    name varchar(150) NOT NULL,
    sort_order integer NOT NULL DEFAULT 0,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_fuel_types_catalog_active_sort ON redline.fuel_types_catalog(is_active, sort_order);

CREATE TABLE IF NOT EXISTS redline.transmissions_catalog (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    name varchar(150) NOT NULL,
    sort_order integer NOT NULL DEFAULT 0,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_transmissions_catalog_active_sort ON redline.transmissions_catalog(is_active, sort_order);

CREATE TABLE IF NOT EXISTS redline.vehicle_colors_catalog (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code varchar(50) NOT NULL UNIQUE,
    name varchar(150) NOT NULL,
    sort_order integer NOT NULL DEFAULT 0,
    is_active boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vehicle_colors_catalog_active_sort ON redline.vehicle_colors_catalog(is_active, sort_order);

CREATE TABLE IF NOT EXISTS redline.clients (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name varchar(180) NOT NULL,
    document_type varchar(30),
    document_number varchar(50),
    email varchar(150),
    phone varchar(30),
    alternate_phone varchar(30),
    address text,
    notes text,
    status redline.status_generic NOT NULL DEFAULT 'active',
    created_by uuid REFERENCES redline.users(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT uq_clients_document UNIQUE NULLS NOT DISTINCT (document_type, document_number)
);

CREATE INDEX IF NOT EXISTS idx_clients_full_name ON redline.clients(full_name);
CREATE INDEX IF NOT EXISTS idx_clients_email ON redline.clients(email);
CREATE INDEX IF NOT EXISTS idx_clients_phone ON redline.clients(phone);

CREATE TABLE IF NOT EXISTS redline.client_preferences (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id uuid NOT NULL UNIQUE REFERENCES redline.clients(id) ON DELETE CASCADE,
    preferred_brands text[],
    price_min numeric(14,2),
    price_max numeric(14,2),
    vehicle_type varchar(50),
    transmission varchar(50),
    fuel_type varchar(50),
    color varchar(50),
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS redline.client_images (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id uuid NOT NULL REFERENCES redline.clients(id) ON DELETE CASCADE,
    file_path text NOT NULL,
    sort_order integer NOT NULL DEFAULT 0,
    is_cover boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_client_images_client ON redline.client_images(client_id);

-- Back-reference columns that depend on clients existing first
ALTER TABLE redline.vehicles
    ADD COLUMN IF NOT EXISTS reserved_client_id uuid REFERENCES redline.clients(id);

ALTER TABLE redline.vehicle_status_history
    ADD COLUMN IF NOT EXISTS client_id uuid REFERENCES redline.clients(id);

CREATE TABLE IF NOT EXISTS redline.sales (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id uuid NOT NULL UNIQUE REFERENCES redline.vehicles(id),
    client_id uuid NOT NULL REFERENCES redline.clients(id),
    seller_user_id uuid REFERENCES redline.users(id),
    branch_id uuid NOT NULL REFERENCES redline.branches(id),
    sale_date timestamptz NOT NULL DEFAULT now(),
    sale_price numeric(14,2) NOT NULL CHECK (sale_price >= 0),
    cost numeric(14,2) CHECK (cost IS NULL OR cost >= 0),
    profit numeric(14,2),
    payment_method varchar(50),
    status redline.sale_status NOT NULL DEFAULT 'completada',
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_sales_branch_date ON redline.sales(branch_id, sale_date DESC);
CREATE INDEX IF NOT EXISTS idx_sales_seller_date ON redline.sales(seller_user_id, sale_date DESC);

CREATE TABLE IF NOT EXISTS redline.documents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type varchar(50) NOT NULL,
    entity_id uuid NOT NULL,
    file_path text NOT NULL,
    document_type redline.document_type NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS redline.audit_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES redline.users(id),
    action redline.audit_action NOT NULL,
    entity_type varchar(50) NOT NULL,
    entity_id uuid,
    old_data jsonb,
    new_data jsonb,
    ip_address varchar(64),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

DROP TRIGGER IF EXISTS trg_branches_updated_at ON redline.branches;
CREATE TRIGGER trg_branches_updated_at BEFORE UPDATE ON redline.branches FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_roles_updated_at ON redline.roles;
CREATE TRIGGER trg_roles_updated_at BEFORE UPDATE ON redline.roles FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_permissions_updated_at ON redline.permissions;
CREATE TRIGGER trg_permissions_updated_at BEFORE UPDATE ON redline.permissions FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_users_updated_at ON redline.users;
CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON redline.users FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_user_branch_access_updated_at ON redline.user_branch_access;
CREATE TRIGGER trg_user_branch_access_updated_at BEFORE UPDATE ON redline.user_branch_access FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_system_settings_updated_at ON redline.system_settings;
CREATE TRIGGER trg_system_settings_updated_at BEFORE UPDATE ON redline.system_settings FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_vehicles_updated_at ON redline.vehicles;
CREATE TRIGGER trg_vehicles_updated_at BEFORE UPDATE ON redline.vehicles FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_vehicle_images_updated_at ON redline.vehicle_images;
CREATE TRIGGER trg_vehicle_images_updated_at BEFORE UPDATE ON redline.vehicle_images FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_vehicle_status_history_updated_at ON redline.vehicle_status_history;
CREATE TRIGGER trg_vehicle_status_history_updated_at BEFORE UPDATE ON redline.vehicle_status_history FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_vehicle_brands_updated_at ON redline.vehicle_brands;
CREATE TRIGGER trg_vehicle_brands_updated_at BEFORE UPDATE ON redline.vehicle_brands FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_vehicle_models_catalog_updated_at ON redline.vehicle_models_catalog;
CREATE TRIGGER trg_vehicle_models_catalog_updated_at BEFORE UPDATE ON redline.vehicle_models_catalog FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_vehicle_types_catalog_updated_at ON redline.vehicle_types_catalog;
CREATE TRIGGER trg_vehicle_types_catalog_updated_at BEFORE UPDATE ON redline.vehicle_types_catalog FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_fuel_types_catalog_updated_at ON redline.fuel_types_catalog;
CREATE TRIGGER trg_fuel_types_catalog_updated_at BEFORE UPDATE ON redline.fuel_types_catalog FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_transmissions_catalog_updated_at ON redline.transmissions_catalog;
CREATE TRIGGER trg_transmissions_catalog_updated_at BEFORE UPDATE ON redline.transmissions_catalog FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_vehicle_colors_catalog_updated_at ON redline.vehicle_colors_catalog;
CREATE TRIGGER trg_vehicle_colors_catalog_updated_at BEFORE UPDATE ON redline.vehicle_colors_catalog FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_clients_updated_at ON redline.clients;
CREATE TRIGGER trg_clients_updated_at BEFORE UPDATE ON redline.clients FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_client_preferences_updated_at ON redline.client_preferences;
CREATE TRIGGER trg_client_preferences_updated_at BEFORE UPDATE ON redline.client_preferences FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_client_images_updated_at ON redline.client_images;
CREATE TRIGGER trg_client_images_updated_at BEFORE UPDATE ON redline.client_images FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_sales_updated_at ON redline.sales;
CREATE TRIGGER trg_sales_updated_at BEFORE UPDATE ON redline.sales FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_documents_updated_at ON redline.documents;
CREATE TRIGGER trg_documents_updated_at BEFORE UPDATE ON redline.documents FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();
DROP TRIGGER IF EXISTS trg_audit_logs_updated_at ON redline.audit_logs;
CREATE TRIGGER trg_audit_logs_updated_at BEFORE UPDATE ON redline.audit_logs FOR EACH ROW EXECUTE FUNCTION redline.set_updated_at();

COMMIT;
