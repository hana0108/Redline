-- Seed completo de catalogos de vehiculos para Redline
-- -----------------------------------------------------------------------------
-- Este script:
-- 1) Inserta catalogo estatico amplio para uso en frontend (selects)
-- 2) Absorbe datos historicos desde redline.vehicles y redline.client_preferences
-- 3) Es idempotente (se puede ejecutar multiples veces sin duplicar)
--
-- Uso:
--   psql -U <usuario> -d <database> -f database/seed_vehicle_catalogs.sql
-- -----------------------------------------------------------------------------

BEGIN;

CREATE SCHEMA IF NOT EXISTS redline;
SET search_path TO redline, public;

-- Verifica prerequisitos minimos
DO $$
BEGIN
    IF to_regclass('redline.vehicle_brands') IS NULL THEN
        RAISE EXCEPTION 'Falta redline.vehicle_brands. Ejecuta primero database/redline_schema.sql';
    END IF;
    IF to_regclass('redline.vehicle_models_catalog') IS NULL THEN
        RAISE EXCEPTION 'Falta redline.vehicle_models_catalog. Ejecuta primero database/redline_schema.sql';
    END IF;
    IF to_regclass('redline.vehicle_types_catalog') IS NULL THEN
        RAISE EXCEPTION 'Falta redline.vehicle_types_catalog. Ejecuta primero database/redline_schema.sql';
    END IF;
    IF to_regclass('redline.fuel_types_catalog') IS NULL THEN
        RAISE EXCEPTION 'Falta redline.fuel_types_catalog. Ejecuta primero database/redline_schema.sql';
    END IF;
    IF to_regclass('redline.transmissions_catalog') IS NULL THEN
        RAISE EXCEPTION 'Falta redline.transmissions_catalog. Ejecuta primero database/redline_schema.sql';
    END IF;
    IF to_regclass('redline.vehicle_colors_catalog') IS NULL THEN
        RAISE EXCEPTION 'Falta redline.vehicle_colors_catalog. Ejecuta primero database/redline_schema.sql';
    END IF;
END $$;

-- -----------------------------------------------------------------------------
-- CATALOGO ESTATICO BASE (AMPLIO)
-- -----------------------------------------------------------------------------

WITH seed_brands(code, name, sort_order) AS (
    VALUES
        ('toyota', 'Toyota', 10),
        ('honda', 'Honda', 20),
        ('ford', 'Ford', 30),
        ('chevrolet', 'Chevrolet', 40),
        ('hyundai', 'Hyundai', 50),
        ('kia', 'Kia', 60),
        ('nissan', 'Nissan', 70),
        ('mazda', 'Mazda', 80),
        ('volkswagen', 'Volkswagen', 90),
        ('bmw', 'BMW', 100),
        ('mercedes-benz', 'Mercedes-Benz', 110),
        ('audi', 'Audi', 120),
        ('lexus', 'Lexus', 130),
        ('acura', 'Acura', 140),
        ('infiniti', 'Infiniti', 150),
        ('subaru', 'Subaru', 160),
        ('mitsubishi', 'Mitsubishi', 170),
        ('renault', 'Renault', 180),
        ('peugeot', 'Peugeot', 190),
        ('citroen', 'Citroen', 200),
        ('fiat', 'Fiat', 210),
        ('jeep', 'Jeep', 220),
        ('ram', 'RAM', 230),
        ('dodge', 'Dodge', 240),
        ('gmc', 'GMC', 250),
        ('cadillac', 'Cadillac', 260),
        ('volvo', 'Volvo', 270),
        ('land-rover', 'Land Rover', 280),
        ('jaguar', 'Jaguar', 290),
        ('porsche', 'Porsche', 300),
        ('tesla', 'Tesla', 310),
        ('mini', 'MINI', 320),
        ('suzuki', 'Suzuki', 330),
        ('chery', 'Chery', 340),
        ('byd', 'BYD', 350),
        ('geely', 'Geely', 360),
        ('seat', 'SEAT', 370),
        ('skoda', 'Skoda', 380),
        ('alfa-romeo', 'Alfa Romeo', 390),
        ('lincoln', 'Lincoln', 400)
)
INSERT INTO redline.vehicle_brands (code, name, sort_order, is_active)
SELECT code, name, sort_order, TRUE
FROM seed_brands
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    sort_order = EXCLUDED.sort_order,
    is_active = TRUE,
    updated_at = NOW();


WITH seed_types(code, name, sort_order) AS (
    VALUES
        ('sedan', 'Sedan', 10),
        ('suv', 'SUV', 20),
        ('hatchback', 'Hatchback', 30),
        ('pickup', 'Pickup', 40),
        ('coupe', 'Coupe', 50),
        ('convertible', 'Convertible', 60),
        ('wagon', 'Wagon', 70),
        ('minivan', 'Minivan', 80),
        ('van', 'Van', 90),
        ('crossover', 'Crossover', 100),
        ('roadster', 'Roadster', 110)
)
INSERT INTO redline.vehicle_types_catalog (code, name, sort_order, is_active)
SELECT code, name, sort_order, TRUE
FROM seed_types
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    sort_order = EXCLUDED.sort_order,
    is_active = TRUE,
    updated_at = NOW();


WITH seed_fuel(code, name, sort_order) AS (
    VALUES
        ('gasolina', 'Gasolina', 10),
        ('diesel', 'Diesel', 20),
        ('hibrido', 'Hibrido', 30),
        ('electrico', 'Electrico', 40),
        ('plugin-hibrido', 'Plugin Hibrido', 50),
        ('gas-natural', 'Gas Natural', 60),
        ('flex', 'Flex', 70)
)
INSERT INTO redline.fuel_types_catalog (code, name, sort_order, is_active)
SELECT code, name, sort_order, TRUE
FROM seed_fuel
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    sort_order = EXCLUDED.sort_order,
    is_active = TRUE,
    updated_at = NOW();


WITH seed_transmissions(code, name, sort_order) AS (
    VALUES
        ('manual', 'Manual', 10),
        ('automatica', 'Automatica', 20),
        ('cvt', 'CVT', 30),
        ('dct', 'DCT', 40),
        ('tiptronic', 'Tiptronic', 50),
        ('secuencial', 'Secuencial', 60)
)
INSERT INTO redline.transmissions_catalog (code, name, sort_order, is_active)
SELECT code, name, sort_order, TRUE
FROM seed_transmissions
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    sort_order = EXCLUDED.sort_order,
    is_active = TRUE,
    updated_at = NOW();


WITH seed_colors(code, name, sort_order) AS (
    VALUES
        ('blanco', 'Blanco', 10),
        ('negro', 'Negro', 20),
        ('gris', 'Gris', 30),
        ('plata', 'Plata', 40),
        ('rojo', 'Rojo', 50),
        ('azul', 'Azul', 60),
        ('verde', 'Verde', 70),
        ('amarillo', 'Amarillo', 80),
        ('naranja', 'Naranja', 90),
        ('marron', 'Marron', 100),
        ('beige', 'Beige', 110),
        ('dorado', 'Dorado', 120),
        ('vino', 'Vino', 130),
        ('turquesa', 'Turquesa', 140),
        ('gris-oscuro', 'Gris Oscuro', 150),
        ('azul-marino', 'Azul Marino', 160)
)
INSERT INTO redline.vehicle_colors_catalog (code, name, sort_order, is_active)
SELECT code, name, sort_order, TRUE
FROM seed_colors
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    sort_order = EXCLUDED.sort_order,
    is_active = TRUE,
    updated_at = NOW();


WITH seed_models(brand_code, code, name, sort_order) AS (
    VALUES
        -- Toyota
        ('toyota', 'corolla', 'Corolla', 10),
        ('toyota', 'camry', 'Camry', 20),
        ('toyota', 'yaris', 'Yaris', 30),
        ('toyota', 'rav4', 'RAV4', 40),
        ('toyota', 'hilux', 'Hilux', 50),
        ('toyota', 'fortuner', 'Fortuner', 60),
        ('toyota', 'prius', 'Prius', 70),
        -- Honda
        ('honda', 'civic', 'Civic', 10),
        ('honda', 'accord', 'Accord', 20),
        ('honda', 'cr-v', 'CR-V', 30),
        ('honda', 'hr-v', 'HR-V', 40),
        ('honda', 'pilot', 'Pilot', 50),
        -- Ford
        ('ford', 'focus', 'Focus', 10),
        ('ford', 'fusion', 'Fusion', 20),
        ('ford', 'escape', 'Escape', 30),
        ('ford', 'explorer', 'Explorer', 40),
        ('ford', 'f-150', 'F-150', 50),
        ('ford', 'ranger', 'Ranger', 60),
        -- Chevrolet
        ('chevrolet', 'onix', 'Onix', 10),
        ('chevrolet', 'cruze', 'Cruze', 20),
        ('chevrolet', 'tracker', 'Tracker', 30),
        ('chevrolet', 'captiva', 'Captiva', 40),
        ('chevrolet', 'silverado', 'Silverado', 50),
        ('chevrolet', 'tahoe', 'Tahoe', 60),
        -- Hyundai
        ('hyundai', 'accent', 'Accent', 10),
        ('hyundai', 'elantra', 'Elantra', 20),
        ('hyundai', 'sonata', 'Sonata', 30),
        ('hyundai', 'tucson', 'Tucson', 40),
        ('hyundai', 'santa-fe', 'Santa Fe', 50),
        -- Kia
        ('kia', 'rio', 'Rio', 10),
        ('kia', 'cerato', 'Cerato', 20),
        ('kia', 'sportage', 'Sportage', 30),
        ('kia', 'sorento', 'Sorento', 40),
        -- Nissan
        ('nissan', 'versa', 'Versa', 10),
        ('nissan', 'sentra', 'Sentra', 20),
        ('nissan', 'altima', 'Altima', 30),
        ('nissan', 'x-trail', 'X-Trail', 40),
        ('nissan', 'frontier', 'Frontier', 50),
        -- Mazda
        ('mazda', 'mazda2', 'Mazda2', 10),
        ('mazda', 'mazda3', 'Mazda3', 20),
        ('mazda', 'cx-3', 'CX-3', 30),
        ('mazda', 'cx-5', 'CX-5', 40),
        ('mazda', 'cx-9', 'CX-9', 50),
        -- Volkswagen
        ('volkswagen', 'polo', 'Polo', 10),
        ('volkswagen', 'jetta', 'Jetta', 20),
        ('volkswagen', 'golf', 'Golf', 30),
        ('volkswagen', 'tiguan', 'Tiguan', 40),
        ('volkswagen', 'amarok', 'Amarok', 50),
        -- BMW
        ('bmw', 'serie-1', 'Serie 1', 10),
        ('bmw', 'serie-3', 'Serie 3', 20),
        ('bmw', 'serie-5', 'Serie 5', 30),
        ('bmw', 'x3', 'X3', 40),
        ('bmw', 'x5', 'X5', 50),
        -- Mercedes-Benz
        ('mercedes-benz', 'clase-a', 'Clase A', 10),
        ('mercedes-benz', 'clase-c', 'Clase C', 20),
        ('mercedes-benz', 'clase-e', 'Clase E', 30),
        ('mercedes-benz', 'gle', 'GLE', 40),
        -- Audi
        ('audi', 'a3', 'A3', 10),
        ('audi', 'a4', 'A4', 20),
        ('audi', 'a6', 'A6', 30),
        ('audi', 'q3', 'Q3', 40),
        ('audi', 'q5', 'Q5', 50),
        -- Tesla
        ('tesla', 'model-3', 'Model 3', 10),
        ('tesla', 'model-y', 'Model Y', 20),
        ('tesla', 'model-s', 'Model S', 30),
        ('tesla', 'model-x', 'Model X', 40),
        -- Jeep
        ('jeep', 'wrangler', 'Wrangler', 10),
        ('jeep', 'grand-cherokee', 'Grand Cherokee', 20),
        ('jeep', 'compass', 'Compass', 30),
        -- Porsche
        ('porsche', 'cayenne', 'Cayenne', 10),
        ('porsche', 'macan', 'Macan', 20),
        ('porsche', '911', '911', 30)
)
INSERT INTO redline.vehicle_models_catalog (brand_id, code, name, sort_order, is_active)
SELECT b.id, m.code, m.name, m.sort_order, TRUE
FROM seed_models m
JOIN redline.vehicle_brands b ON b.code = m.brand_code
ON CONFLICT (brand_id, code) DO UPDATE
SET
    name = EXCLUDED.name,
    sort_order = EXCLUDED.sort_order,
    is_active = TRUE,
    updated_at = NOW();

-- -----------------------------------------------------------------------------
-- ABSORCION DE DATOS HISTORICOS
-- -----------------------------------------------------------------------------
-- Fuente A: redline.vehicles
-- Fuente B: redline.client_preferences (tipos, combustible, transmision y marcas preferidas)

-- Marcas historicas desde vehicles y client_preferences.preferred_brands[]
WITH vehicles_brand AS (
    SELECT NULLIF(TRIM(v.brand), '') AS raw_name
    FROM redline.vehicles v
), prefs_brand AS (
    SELECT NULLIF(TRIM(b), '') AS raw_name
    FROM redline.client_preferences cp
    CROSS JOIN LATERAL unnest(cp.preferred_brands) AS b
), combined AS (
    SELECT raw_name FROM vehicles_brand
    UNION
    SELECT raw_name FROM prefs_brand
), normalized AS (
    SELECT
        NULLIF(REGEXP_REPLACE(LOWER(raw_name), '[^a-z0-9]+', '-', 'g'), '') AS code,
        raw_name AS name
    FROM combined
    WHERE raw_name IS NOT NULL
), dedup AS (
    SELECT
        code,
        MIN(name) AS name,
        9000 + ROW_NUMBER() OVER (ORDER BY MIN(name)) AS sort_order
    FROM normalized
    WHERE code IS NOT NULL
    GROUP BY code
)
INSERT INTO redline.vehicle_brands (code, name, sort_order, is_active)
SELECT code, name, sort_order, TRUE
FROM dedup
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    is_active = TRUE,
    updated_at = NOW();


-- Tipos historicos
WITH vehicles_type AS (
    SELECT NULLIF(TRIM(v.vehicle_type), '') AS raw_name
    FROM redline.vehicles v
), prefs_type AS (
    SELECT NULLIF(TRIM(cp.vehicle_type), '') AS raw_name
    FROM redline.client_preferences cp
), combined AS (
    SELECT raw_name FROM vehicles_type
    UNION
    SELECT raw_name FROM prefs_type
), normalized AS (
    SELECT
        NULLIF(REGEXP_REPLACE(LOWER(raw_name), '[^a-z0-9]+', '-', 'g'), '') AS code,
        raw_name AS name
    FROM combined
    WHERE raw_name IS NOT NULL
), dedup AS (
    SELECT
        code,
        MIN(name) AS name,
        9000 + ROW_NUMBER() OVER (ORDER BY MIN(name)) AS sort_order
    FROM normalized
    WHERE code IS NOT NULL
    GROUP BY code
)
INSERT INTO redline.vehicle_types_catalog (code, name, sort_order, is_active)
SELECT code, name, sort_order, TRUE
FROM dedup
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    is_active = TRUE,
    updated_at = NOW();


-- Combustibles historicos
WITH vehicles_fuel AS (
    SELECT NULLIF(TRIM(v.fuel_type), '') AS raw_name
    FROM redline.vehicles v
), prefs_fuel AS (
    SELECT NULLIF(TRIM(cp.fuel_type), '') AS raw_name
    FROM redline.client_preferences cp
), combined AS (
    SELECT raw_name FROM vehicles_fuel
    UNION
    SELECT raw_name FROM prefs_fuel
), normalized AS (
    SELECT
        NULLIF(REGEXP_REPLACE(LOWER(raw_name), '[^a-z0-9]+', '-', 'g'), '') AS code,
        raw_name AS name
    FROM combined
    WHERE raw_name IS NOT NULL
), dedup AS (
    SELECT
        code,
        MIN(name) AS name,
        9000 + ROW_NUMBER() OVER (ORDER BY MIN(name)) AS sort_order
    FROM normalized
    WHERE code IS NOT NULL
    GROUP BY code
)
INSERT INTO redline.fuel_types_catalog (code, name, sort_order, is_active)
SELECT code, name, sort_order, TRUE
FROM dedup
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    is_active = TRUE,
    updated_at = NOW();


-- Transmisiones historicas
WITH vehicles_tx AS (
    SELECT NULLIF(TRIM(v.transmission), '') AS raw_name
    FROM redline.vehicles v
), prefs_tx AS (
    SELECT NULLIF(TRIM(cp.transmission), '') AS raw_name
    FROM redline.client_preferences cp
), combined AS (
    SELECT raw_name FROM vehicles_tx
    UNION
    SELECT raw_name FROM prefs_tx
), normalized AS (
    SELECT
        NULLIF(REGEXP_REPLACE(LOWER(raw_name), '[^a-z0-9]+', '-', 'g'), '') AS code,
        raw_name AS name
    FROM combined
    WHERE raw_name IS NOT NULL
), dedup AS (
    SELECT
        code,
        MIN(name) AS name,
        9000 + ROW_NUMBER() OVER (ORDER BY MIN(name)) AS sort_order
    FROM normalized
    WHERE code IS NOT NULL
    GROUP BY code
)
INSERT INTO redline.transmissions_catalog (code, name, sort_order, is_active)
SELECT code, name, sort_order, TRUE
FROM dedup
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    is_active = TRUE,
    updated_at = NOW();


-- Colores historicos
WITH vehicles_color AS (
    SELECT NULLIF(TRIM(v.color), '') AS raw_name
    FROM redline.vehicles v
), prefs_color AS (
    SELECT NULLIF(TRIM(cp.color), '') AS raw_name
    FROM redline.client_preferences cp
), combined AS (
    SELECT raw_name FROM vehicles_color
    UNION
    SELECT raw_name FROM prefs_color
), normalized AS (
    SELECT
        NULLIF(REGEXP_REPLACE(LOWER(raw_name), '[^a-z0-9]+', '-', 'g'), '') AS code,
        raw_name AS name
    FROM combined
    WHERE raw_name IS NOT NULL
), dedup AS (
    SELECT
        code,
        MIN(name) AS name,
        9000 + ROW_NUMBER() OVER (ORDER BY MIN(name)) AS sort_order
    FROM normalized
    WHERE code IS NOT NULL
    GROUP BY code
)
INSERT INTO redline.vehicle_colors_catalog (code, name, sort_order, is_active)
SELECT code, name, sort_order, TRUE
FROM dedup
ON CONFLICT (code) DO UPDATE
SET
    name = EXCLUDED.name,
    is_active = TRUE,
    updated_at = NOW();


-- Modelos historicos (dependen de marca)
WITH extracted AS (
    SELECT
        NULLIF(TRIM(v.brand), '') AS raw_brand,
        NULLIF(TRIM(v.model), '') AS raw_model
    FROM redline.vehicles v
    WHERE v.brand IS NOT NULL
      AND v.model IS NOT NULL
), normalized AS (
    SELECT
        NULLIF(REGEXP_REPLACE(LOWER(raw_brand), '[^a-z0-9]+', '-', 'g'), '') AS brand_code,
        NULLIF(REGEXP_REPLACE(LOWER(raw_model), '[^a-z0-9]+', '-', 'g'), '') AS model_code,
        raw_model AS model_name
    FROM extracted
), dedup AS (
    SELECT
        brand_code,
        model_code,
        MIN(model_name) AS model_name
    FROM normalized
    WHERE brand_code IS NOT NULL
      AND model_code IS NOT NULL
    GROUP BY brand_code, model_code
)
INSERT INTO redline.vehicle_models_catalog (brand_id, code, name, sort_order, is_active)
SELECT
    b.id,
    d.model_code,
    d.model_name,
    9000 + ROW_NUMBER() OVER (PARTITION BY b.id ORDER BY d.model_name),
    TRUE
FROM dedup d
JOIN redline.vehicle_brands b ON b.code = d.brand_code
ON CONFLICT (brand_id, code) DO UPDATE
SET
    name = EXCLUDED.name,
    is_active = TRUE,
    updated_at = NOW();

COMMIT;

-- Reporte rapido (opcional)
SELECT 'vehicle_brands' AS catalog, COUNT(*) AS total FROM redline.vehicle_brands
UNION ALL
SELECT 'vehicle_models_catalog', COUNT(*) FROM redline.vehicle_models_catalog
UNION ALL
SELECT 'vehicle_types_catalog', COUNT(*) FROM redline.vehicle_types_catalog
UNION ALL
SELECT 'fuel_types_catalog', COUNT(*) FROM redline.fuel_types_catalog
UNION ALL
SELECT 'transmissions_catalog', COUNT(*) FROM redline.transmissions_catalog
UNION ALL
SELECT 'vehicle_colors_catalog', COUNT(*) FROM redline.vehicle_colors_catalog
ORDER BY catalog;
