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


WITH seed_models(brand_code, code, name, sort_order, vehicle_type, transmission) AS (
    VALUES
        -- (brand_code, code, name, sort_order, vehicle_type, transmission)
        -- Toyota
        ('toyota', 'corolla',            'Corolla',            10,  'Sedan',    'Automatica'),
        ('toyota', 'camry',              'Camry',              20,  'Sedan',    'Automatica'),
        ('toyota', 'yaris',              'Yaris',              30,  'Hatchback','Manual'),
        ('toyota', 'rav4',               'RAV4',               40,  'SUV',      'Automatica'),
        ('toyota', 'hilux',              'Hilux',              50,  'Pickup',   'Manual'),
        ('toyota', 'fortuner',           'Fortuner',           60,  'SUV',      'Automatica'),
        ('toyota', 'prius',              'Prius',              70,  'Sedan',    'Automatica'),
        ('toyota', 'land-cruiser',       'Land Cruiser',       80,  'SUV',      'Automatica'),
        ('toyota', 'land-cruiser-prado', 'Land Cruiser Prado', 90,  'SUV',      'Automatica'),
        ('toyota', 'corolla-cross',      'Corolla Cross',      100, 'SUV',      'Automatica'),
        ('toyota', 'hiace',              'Hiace',              110, 'Van',       'Manual'),
        ('toyota', 'avanza',             'Avanza',             120, 'Van',       'Manual'),
        ('toyota', 'innova',             'Innova',             130, 'Van',       'Automatica'),
        -- Honda
        ('honda', 'civic',   'Civic',   10,  'Sedan',    'Automatica'),
        ('honda', 'accord',  'Accord',  20,  'Sedan',    'Automatica'),
        ('honda', 'cr-v',    'CR-V',    30,  'SUV',      'Automatica'),
        ('honda', 'hr-v',    'HR-V',    40,  'SUV',      'Automatica'),
        ('honda', 'pilot',   'Pilot',   50,  'SUV',      'Automatica'),
        ('honda', 'fit',     'Fit',     60,  'Hatchback','Manual'),
        ('honda', 'ridgeline','Ridgeline',70, 'Pickup',  'Automatica'),
        -- Ford
        ('ford', 'focus',    'Focus',    10,  'Hatchback','Manual'),
        ('ford', 'fusion',   'Fusion',   20,  'Sedan',    'Automatica'),
        ('ford', 'escape',   'Escape',   30,  'SUV',      'Automatica'),
        ('ford', 'explorer', 'Explorer', 40,  'SUV',      'Automatica'),
        ('ford', 'f-150',    'F-150',    50,  'Pickup',   'Automatica'),
        ('ford', 'ranger',   'Ranger',   60,  'Pickup',   'Automatica'),
        ('ford', 'bronco',   'Bronco',   70,  'SUV',      'Automatica'),
        ('ford', 'ecosport', 'EcoSport', 80,  'SUV',      'Automatica'),
        ('ford', 'territory','Territory',90,  'SUV',      'Automatica'),
        -- Chevrolet
        ('chevrolet', 'onix',     'Onix',     10,  'Hatchback','Manual'),
        ('chevrolet', 'cruze',    'Cruze',    20,  'Sedan',    'Automatica'),
        ('chevrolet', 'tracker',  'Tracker',  30,  'SUV',      'Automatica'),
        ('chevrolet', 'captiva',  'Captiva',  40,  'SUV',      'Automatica'),
        ('chevrolet', 'silverado','Silverado',50,  'Pickup',   'Automatica'),
        ('chevrolet', 'tahoe',    'Tahoe',    60,  'SUV',      'Automatica'),
        ('chevrolet', 'aveo',     'Aveo',     70,  'Sedan',    'Manual'),
        ('chevrolet', 'sail',     'Sail',     80,  'Sedan',    'Automatica'),
        ('chevrolet', 'blazer',   'Blazer',   90,  'SUV',      'Automatica'),
        ('chevrolet', 'd-max',    'D-Max',    100, 'Pickup',   'Manual'),
        ('chevrolet', 'n300',     'N300',     110, 'Van',       'Manual'),
        -- Hyundai
        ('hyundai', 'accent',   'Accent',   10,  'Sedan',    'Manual'),
        ('hyundai', 'elantra',  'Elantra',  20,  'Sedan',    'Automatica'),
        ('hyundai', 'sonata',   'Sonata',   30,  'Sedan',    'Automatica'),
        ('hyundai', 'tucson',   'Tucson',   40,  'SUV',      'Automatica'),
        ('hyundai', 'santa-fe', 'Santa Fe', 50,  'SUV',      'Automatica'),
        ('hyundai', 'creta',    'Creta',    60,  'SUV',      'Automatica'),
        ('hyundai', 'h-1',      'H-1',      70,  'Van',       'Manual'),
        ('hyundai', 'ioniq',    'Ioniq',    80,  'Sedan',    'Automatica'),
        -- Kia
        ('kia', 'rio',      'Rio',      10,  'Hatchback','Manual'),
        ('kia', 'cerato',   'Cerato',   20,  'Sedan',    'Automatica'),
        ('kia', 'sportage', 'Sportage', 30,  'SUV',      'Automatica'),
        ('kia', 'sorento',  'Sorento',  40,  'SUV',      'Automatica'),
        ('kia', 'stinger',  'Stinger',  50,  'Sedan',    'Automatica'),
        ('kia', 'seltos',   'Seltos',   60,  'SUV',      'Automatica'),
        ('kia', 'soul',     'Soul',     70,  'Hatchback','Automatica'),
        -- Nissan
        ('nissan', 'versa',    'Versa',    10,  'Sedan',    'Manual'),
        ('nissan', 'sentra',   'Sentra',   20,  'Sedan',    'Automatica'),
        ('nissan', 'altima',   'Altima',   30,  'Sedan',    'Automatica'),
        ('nissan', 'x-trail',  'X-Trail',  40,  'SUV',      'Automatica'),
        ('nissan', 'frontier', 'Frontier', 50,  'Pickup',   'Manual'),
        ('nissan', 'march',    'March',    60,  'Hatchback','Manual'),
        ('nissan', 'kicks',    'Kicks',    70,  'SUV',      'Automatica'),
        ('nissan', 'navara',   'Navara',   80,  'Pickup',   'Manual'),
        ('nissan', 'pathfinder','Pathfinder',90, 'SUV',     'Automatica'),
        -- Mazda
        ('mazda', 'mazda2', 'Mazda2', 10,  'Hatchback','Manual'),
        ('mazda', 'mazda3', 'Mazda3', 20,  'Sedan',    'Automatica'),
        ('mazda', 'cx-3',   'CX-3',   30,  'SUV',      'Automatica'),
        ('mazda', 'cx-5',   'CX-5',   40,  'SUV',      'Automatica'),
        ('mazda', 'cx-9',   'CX-9',   50,  'SUV',      'Automatica'),
        ('mazda', 'bt-50',  'BT-50',  60,  'Pickup',   'Manual'),
        -- Volkswagen
        ('volkswagen', 'polo',    'Polo',    10,  'Hatchback','Automatica'),
        ('volkswagen', 'jetta',   'Jetta',   20,  'Sedan',    'Automatica'),
        ('volkswagen', 'golf',    'Golf',    30,  'Hatchback','Automatica'),
        ('volkswagen', 'tiguan',  'Tiguan',  40,  'SUV',      'Automatica'),
        ('volkswagen', 'amarok',  'Amarok',  50,  'Pickup',   'Manual'),
        ('volkswagen', 't-cross', 'T-Cross', 60,  'SUV',      'Automatica'),
        ('volkswagen', 'gol',     'Gol',     70,  'Hatchback','Manual'),
        ('volkswagen', 'taos',    'Taos',    80,  'SUV',      'Automatica'),
        -- BMW
        ('bmw', 'serie-1', 'Serie 1', 10,  'Hatchback','Automatica'),
        ('bmw', 'serie-3', 'Serie 3', 20,  'Sedan',    'Automatica'),
        ('bmw', 'serie-5', 'Serie 5', 30,  'Sedan',    'Automatica'),
        ('bmw', 'x3',      'X3',      40,  'SUV',      'Automatica'),
        ('bmw', 'x5',      'X5',      50,  'SUV',      'Automatica'),
        ('bmw', 'x1',      'X1',      60,  'SUV',      'Automatica'),
        -- Mercedes-Benz
        ('mercedes-benz', 'clase-a', 'Clase A', 10,  'Hatchback','Automatica'),
        ('mercedes-benz', 'clase-c', 'Clase C', 20,  'Sedan',    'Automatica'),
        ('mercedes-benz', 'clase-e', 'Clase E', 30,  'Sedan',    'Automatica'),
        ('mercedes-benz', 'gle',     'GLE',     40,  'SUV',      'Automatica'),
        ('mercedes-benz', 'glc',     'GLC',     50,  'SUV',      'Automatica'),
        -- Audi
        ('audi', 'a3', 'A3', 10,  'Sedan',    'Automatica'),
        ('audi', 'a4', 'A4', 20,  'Sedan',    'Automatica'),
        ('audi', 'a6', 'A6', 30,  'Sedan',    'Automatica'),
        ('audi', 'q3', 'Q3', 40,  'SUV',      'Automatica'),
        ('audi', 'q5', 'Q5', 50,  'SUV',      'Automatica'),
        ('audi', 'q7', 'Q7', 60,  'SUV',      'Automatica'),
        -- Tesla
        ('tesla', 'model-3', 'Model 3', 10,  'Sedan',    'Automatica'),
        ('tesla', 'model-y', 'Model Y', 20,  'SUV',      'Automatica'),
        ('tesla', 'model-s', 'Model S', 30,  'Sedan',    'Automatica'),
        ('tesla', 'model-x', 'Model X', 40,  'SUV',      'Automatica'),
        -- Jeep
        ('jeep', 'wrangler',       'Wrangler',       10,  'SUV',      'Automatica'),
        ('jeep', 'grand-cherokee', 'Grand Cherokee', 20,  'SUV',      'Automatica'),
        ('jeep', 'compass',        'Compass',        30,  'SUV',      'Automatica'),
        ('jeep', 'gladiator',      'Gladiator',      40,  'Pickup',   'Manual'),
        ('jeep', 'renegade',       'Renegade',       50,  'SUV',      'Automatica'),
        -- Renault
        ('renault', 'duster',  'Duster',  10,  'SUV',      'Manual'),
        ('renault', 'logan',   'Logan',   20,  'Sedan',    'Manual'),
        ('renault', 'sandero', 'Sandero', 30,  'Hatchback','Manual'),
        ('renault', 'captur',  'Captur',  40,  'SUV',      'Automatica'),
        ('renault', 'koleos',  'Koleos',  50,  'SUV',      'Automatica'),
        ('renault', 'oroch',   'Oroch',   60,  'Pickup',   'Manual'),
        -- Mitsubishi
        ('mitsubishi', 'l200',          'L200',          10,  'Pickup',   'Manual'),
        ('mitsubishi', 'outlander',     'Outlander',     20,  'SUV',      'Automatica'),
        ('mitsubishi', 'eclipse-cross', 'Eclipse Cross', 30,  'SUV',      'Automatica'),
        ('mitsubishi', 'montero-sport', 'Montero Sport', 40,  'SUV',      'Automatica'),
        ('mitsubishi', 'pajero',        'Pajero',        50,  'SUV',      'Automatica'),
        ('mitsubishi', 'asx',           'ASX',           60,  'SUV',      'Automatica'),
        -- Porsche
        ('porsche', 'cayenne', 'Cayenne', 10,  'SUV',      'Automatica'),
        ('porsche', 'macan',   'Macan',   20,  'SUV',      'Automatica'),
        ('porsche', '911',     '911',     30,  'Coupe',    'Automatica'),
        ('porsche', 'panamera','Panamera',40,  'Sedan',    'Automatica'),
        -- Land Rover
        ('land-rover', 'defender',     'Defender',     10,  'SUV',      'Automatica'),
        ('land-rover', 'discovery',    'Discovery',    20,  'SUV',      'Automatica'),
        ('land-rover', 'range-rover',  'Range Rover',  30,  'SUV',      'Automatica'),
        ('land-rover', 'sport',        'Range Rover Sport', 40, 'SUV',  'Automatica'),
        -- Subaru
        ('subaru', 'forester',  'Forester',  10,  'SUV',      'Automatica'),
        ('subaru', 'outback',   'Outback',   20,  'Wagon',    'Automatica'),
        ('subaru', 'impreza',   'Impreza',   30,  'Sedan',    'Manual'),
        ('subaru', 'xv',        'XV',        40,  'SUV',      'Automatica'),
        -- Volvo
        ('volvo', 'xc60',  'XC60',  10,  'SUV',      'Automatica'),
        ('volvo', 'xc90',  'XC90',  20,  'SUV',      'Automatica'),
        ('volvo', 's60',   'S60',   30,  'Sedan',    'Automatica'),
        -- Lexus
        ('lexus', 'rx',   'RX',   10,  'SUV',      'Automatica'),
        ('lexus', 'nx',   'NX',   20,  'SUV',      'Automatica'),
        ('lexus', 'is',   'IS',   30,  'Sedan',    'Automatica'),
        ('lexus', 'lx',   'LX',   40,  'SUV',      'Automatica'),
        -- Dodge
        ('dodge', 'ram',      'RAM 1500',  10,  'Pickup',   'Automatica'),
        ('dodge', 'durango',  'Durango',   20,  'SUV',      'Automatica'),
        ('dodge', 'challenger','Challenger',30, 'Coupe',    'Automatica'),
        -- GMC
        ('gmc', 'sierra',  'Sierra',   10,  'Pickup',   'Automatica'),
        ('gmc', 'terrain', 'Terrain',  20,  'SUV',      'Automatica'),
        ('gmc', 'yukon',   'Yukon',    30,  'SUV',      'Automatica'),
        -- Suzuki
        ('suzuki', 'jimny',    'Jimny',    10,  'SUV',      'Manual'),
        ('suzuki', 'vitara',   'Vitara',   20,  'SUV',      'Automatica'),
        ('suzuki', 'swift',    'Swift',    30,  'Hatchback','Manual'),
        -- Chery
        ('chery', 'tiggo-4',  'Tiggo 4',   10,  'SUV',      'Automatica'),
        ('chery', 'tiggo-7',  'Tiggo 7',   20,  'SUV',      'Automatica'),
        ('chery', 'tiggo-8',  'Tiggo 8',   30,  'SUV',      'Automatica'),
        -- BYD
        ('byd', 'atto-3',  'Atto 3',   10,  'SUV',      'Automatica'),
        ('byd', 'han',     'Han',      20,  'Sedan',    'Automatica'),
        ('byd', 'song',    'Song',     30,  'SUV',      'Automatica'),
        -- Peugeot
        ('peugeot', '208',    '208',    10,  'Hatchback','Manual'),
        ('peugeot', '2008',   '2008',   20,  'SUV',      'Automatica'),
        ('peugeot', '3008',   '3008',   30,  'SUV',      'Automatica'),
        -- RAM
        ('ram', '1500',    'RAM 1500', 10,  'Pickup',   'Automatica'),
        ('ram', '2500',    'RAM 2500', 20,  'Pickup',   'Manual'),
        -- Lincoln
        ('lincoln', 'navigator', 'Navigator', 10,  'SUV',  'Automatica'),
        ('lincoln', 'corsair',   'Corsair',   20,  'SUV',  'Automatica')
)
INSERT INTO redline.vehicle_models_catalog (brand_id, code, name, sort_order, is_active, default_vehicle_type, default_transmission)
SELECT b.id, m.code, m.name, m.sort_order, TRUE, m.vehicle_type, m.transmission
FROM seed_models m
JOIN redline.vehicle_brands b ON b.code = m.brand_code
ON CONFLICT (brand_id, code) DO UPDATE
SET
    name                 = EXCLUDED.name,
    sort_order           = EXCLUDED.sort_order,
    is_active            = TRUE,
    default_vehicle_type = EXCLUDED.default_vehicle_type,
    default_transmission = EXCLUDED.default_transmission,
    updated_at           = NOW();

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
