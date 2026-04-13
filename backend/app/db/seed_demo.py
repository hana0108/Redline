"""
Seed de datos demo para presentación del proyecto.

Idempotente: salta si la sucursal "Redline Caracas Centro" ya existe.

Crea:
  - 5 sucursales
  - 8 usuarios demo  (1 gerente, 5 vendedores, 2 inventario)  → contraseña: Demo123*
  - 50 clientes
  - 81 vehículos  (DISPONIBLE / RESERVADO / VENDIDO / EN_PROCESO)
  - 18 ventas
  Total: ~162 registros
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select

import app.db.base  # noqa: F401  – registra todos los modelos
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.branch import Branch
from app.models.client import Client
from app.models.enums import SaleStatus, StatusGeneric, VehicleStatus
from app.models.role import Role
from app.models.sale import Sale
from app.models.user import User, UserBranchAccess
from app.models.vehicle import Vehicle

# ── Sucursales ────────────────────────────────────────────────────────────────

BRANCHES: list[dict] = [
    {
        "name": "Redline Caracas Centro",
        "address": "Av. Libertador, El Recreo, Caracas",
        "phone": "0212-555-0101",
        "email": "centro@redline.com",
    },
    {
        "name": "Redline Caracas Este",
        "address": "Av. Francisco de Miranda, Chacao, Caracas",
        "phone": "0212-555-0202",
        "email": "este@redline.com",
    },
    {
        "name": "Redline Maracaibo",
        "address": "Av. 5 de Julio, Maracaibo",
        "phone": "0261-555-0303",
        "email": "maracaibo@redline.com",
    },
    {
        "name": "Redline Valencia",
        "address": "Av. Bolívar Norte, Valencia",
        "phone": "0241-555-0404",
        "email": "valencia@redline.com",
    },
    {
        "name": "Redline Barquisimeto",
        "address": "Av. Lara, Barquisimeto",
        "phone": "0251-555-0505",
        "email": "barquisimeto@redline.com",
    },
]

# ── Usuarios demo ─────────────────────────────────────────────────────────────
# branch_names: None → acceso a todas las sucursales

USERS: list[dict] = [
    {
        "email": "carlos.mendoza@redline.com",
        "full_name": "Carlos Mendoza",
        "role_code": "manager",
        "phone": "0414-5550001",
        "branch_names": None,
    },
    {
        "email": "laura.perez@redline.com",
        "full_name": "Laura Pérez",
        "role_code": "seller",
        "phone": "0424-5550002",
        "branch_names": ["Redline Caracas Centro"],
    },
    {
        "email": "miguel.torres@redline.com",
        "full_name": "Miguel Torres",
        "role_code": "seller",
        "phone": "0416-5550003",
        "branch_names": ["Redline Caracas Este"],
    },
    {
        "email": "sofia.garcia@redline.com",
        "full_name": "Sofía García",
        "role_code": "seller",
        "phone": "0412-5550004",
        "branch_names": ["Redline Maracaibo"],
    },
    {
        "email": "roberto.silva@redline.com",
        "full_name": "Roberto Silva",
        "role_code": "seller",
        "phone": "0414-5550005",
        "branch_names": ["Redline Valencia"],
    },
    {
        "email": "ana.jimenez@redline.com",
        "full_name": "Ana Jiménez",
        "role_code": "seller",
        "phone": "0424-5550006",
        "branch_names": ["Redline Barquisimeto"],
    },
    {
        "email": "jorge.castillo@redline.com",
        "full_name": "Jorge Castillo",
        "role_code": "inventory",
        "phone": "0416-5550007",
        "branch_names": ["Redline Caracas Centro", "Redline Caracas Este"],
    },
    {
        "email": "yolanda.moreno@redline.com",
        "full_name": "Yolanda Moreno",
        "role_code": "inventory",
        "phone": "0412-5550008",
        "branch_names": ["Redline Maracaibo", "Redline Valencia", "Redline Barquisimeto"],
    },
]

# ── Clientes ──────────────────────────────────────────────────────────────────

CLIENTS: list[dict] = [
    {
        "full_name": "Juan Carlos Rodríguez",
        "doc_type": "V",
        "doc_num": "V-12345678",
        "email": "jrodriguez@mail.com",
        "phone": "0414-6010001",
    },
    {
        "full_name": "María Elena González",
        "doc_type": "V",
        "doc_num": "V-23456789",
        "email": "mgonzalez@mail.com",
        "phone": "0424-6010002",
    },
    {
        "full_name": "Pedro Antonio Martínez",
        "doc_type": "V",
        "doc_num": "V-34567890",
        "email": "pmartinez@mail.com",
        "phone": "0416-6010003",
    },
    {
        "full_name": "Ana Sofía López",
        "doc_type": "V",
        "doc_num": "V-45678901",
        "email": "aslopez@mail.com",
        "phone": "0412-6010004",
    },
    {
        "full_name": "José Miguel Pérez",
        "doc_type": "V",
        "doc_num": "V-56789012",
        "email": "jmperez@mail.com",
        "phone": "0414-6010005",
    },
    {
        "full_name": "Carmen Teresa Díaz",
        "doc_type": "V",
        "doc_num": "V-67890123",
        "email": "ctdiaz@mail.com",
        "phone": "0424-6010006",
    },
    {
        "full_name": "Luis Alberto Hernández",
        "doc_type": "V",
        "doc_num": "V-78901234",
        "email": "lahernandez@mail.com",
        "phone": "0416-6010007",
    },
    {
        "full_name": "Luisa Margarita Torres",
        "doc_type": "V",
        "doc_num": "V-89012345",
        "email": "lmtorres@mail.com",
        "phone": "0412-6010008",
    },
    {
        "full_name": "Carlos Eduardo Ramírez",
        "doc_type": "V",
        "doc_num": "V-90123456",
        "email": "ceramirez@mail.com",
        "phone": "0414-6010009",
    },
    {
        "full_name": "Rosa Angélica Castro",
        "doc_type": "V",
        "doc_num": "V-01234567",
        "email": "racastro@mail.com",
        "phone": "0424-6010010",
    },
    {
        "full_name": "Roberto José Morales",
        "doc_type": "V",
        "doc_num": "V-11223344",
        "email": "rjmorales@mail.com",
        "phone": "0416-6010011",
    },
    {
        "full_name": "Elena Patricia Jiménez",
        "doc_type": "V",
        "doc_num": "V-22334455",
        "email": "epjimenez@mail.com",
        "phone": "0412-6010012",
    },
    {
        "full_name": "Manuel Antonio Ramos",
        "doc_type": "V",
        "doc_num": "V-33445566",
        "email": "maramos@mail.com",
        "phone": "0414-6010013",
    },
    {
        "full_name": "Valentina Andrea Suárez",
        "doc_type": "V",
        "doc_num": "V-44556677",
        "email": "vasuarez@mail.com",
        "phone": "0424-6010014",
    },
    {
        "full_name": "Christian David Vargas",
        "doc_type": "V",
        "doc_num": "V-55667788",
        "email": "cdvargas@mail.com",
        "phone": "0416-6010015",
    },
    {
        "full_name": "Alejandra Beatriz Flores",
        "doc_type": "V",
        "doc_num": "V-66778899",
        "email": "abflores@mail.com",
        "phone": "0412-6010016",
    },
    {
        "full_name": "Andrés Felipe Reyes",
        "doc_type": "V",
        "doc_num": "V-77889900",
        "email": "afreyes@mail.com",
        "phone": "0414-6010017",
    },
    {
        "full_name": "Patricia Lorena Medina",
        "doc_type": "V",
        "doc_num": "V-88990011",
        "email": "plmedina@mail.com",
        "phone": "0424-6010018",
    },
    {
        "full_name": "Fernando Javier Núñez",
        "doc_type": "V",
        "doc_num": "V-99001122",
        "email": "fjnunez@mail.com",
        "phone": "0416-6010019",
    },
    {
        "full_name": "Gabriela Cristina Salazar",
        "doc_type": "V",
        "doc_num": "V-10111213",
        "email": "gcsalazar@mail.com",
        "phone": "0412-6010020",
    },
    {
        "full_name": "Diego Alejandro Torres",
        "doc_type": "V",
        "doc_num": "V-20212223",
        "email": "datorres@mail.com",
        "phone": "0414-6010021",
    },
    {
        "full_name": "Isabel Cristina Montoya",
        "doc_type": "V",
        "doc_num": "V-30313233",
        "email": "icmontoya@mail.com",
        "phone": "0424-6010022",
    },
    {
        "full_name": "Héctor Rafael Gutiérrez",
        "doc_type": "V",
        "doc_num": "V-40414243",
        "email": "hrgutierrez@mail.com",
        "phone": "0416-6010023",
    },
    {
        "full_name": "Claudia Berenice Soto",
        "doc_type": "V",
        "doc_num": "V-50515253",
        "email": "cbsoto@mail.com",
        "phone": "0412-6010024",
    },
    {
        "full_name": "Javier Eduardo Álvarez",
        "doc_type": "V",
        "doc_num": "V-60616263",
        "email": "jealvarez@mail.com",
        "phone": "0414-6010025",
    },
    {
        "full_name": "Sandra Patricia Romero",
        "doc_type": "V",
        "doc_num": "V-70717273",
        "email": "spromero@mail.com",
        "phone": "0424-6010026",
    },
    {
        "full_name": "Miguel Ángel Parra",
        "doc_type": "V",
        "doc_num": "V-80818283",
        "email": "maparra@mail.com",
        "phone": "0416-6010027",
    },
    {
        "full_name": "Natalia Fernanda Cruz",
        "doc_type": "V",
        "doc_num": "V-90919293",
        "email": "nfcruz@mail.com",
        "phone": "0412-6010028",
    },
    {
        "full_name": "Reinaldo José Blanco",
        "doc_type": "V",
        "doc_num": "V-15161718",
        "email": "rjblanco@mail.com",
        "phone": "0414-6010029",
    },
    {
        "full_name": "Ángela María Delgado",
        "doc_type": "V",
        "doc_num": "V-19202122",
        "email": "amdelgado@mail.com",
        "phone": "0424-6010030",
    },
    {
        "full_name": "Guillermo Antonio Santos",
        "doc_type": "V",
        "doc_num": "V-23242526",
        "email": "gasantos@mail.com",
        "phone": "0416-6010031",
    },
    {
        "full_name": "Daniela Carolina Espinoza",
        "doc_type": "V",
        "doc_num": "V-27282930",
        "email": "dcespinoza@mail.com",
        "phone": "0412-6010032",
    },
    {
        "full_name": "Rafael Ernesto Contreras",
        "doc_type": "V",
        "doc_num": "V-31323334",
        "email": "recontreras@mail.com",
        "phone": "0414-6010033",
    },
    {
        "full_name": "Susana Beatriz Aguilar",
        "doc_type": "V",
        "doc_num": "V-35363738",
        "email": "sbaguilar@mail.com",
        "phone": "0424-6010034",
    },
    {
        "full_name": "Orlando Ramón Rojas",
        "doc_type": "V",
        "doc_num": "V-39404142",
        "email": "orrojas@mail.com",
        "phone": "0416-6010035",
    },
    {
        "full_name": "Mónica Elizabeth Carrillo",
        "doc_type": "V",
        "doc_num": "V-43444546",
        "email": "mecarrillo@mail.com",
        "phone": "0412-6010036",
    },
    {
        "full_name": "Esteban Rodrigo Mora",
        "doc_type": "V",
        "doc_num": "V-47484950",
        "email": "ermora@mail.com",
        "phone": "0414-6010037",
    },
    {
        "full_name": "Verónica Andrea Herrera",
        "doc_type": "V",
        "doc_num": "V-51525354",
        "email": "vaherrera@mail.com",
        "phone": "0424-6010038",
    },
    {
        "full_name": "Francisco Javier Guerrero",
        "doc_type": "V",
        "doc_num": "V-55565758",
        "email": "fjguerrero@mail.com",
        "phone": "0416-6010039",
    },
    {
        "full_name": "Luz Marina Cáceres",
        "doc_type": "V",
        "doc_num": "V-59606162",
        "email": "lmcaceres@mail.com",
        "phone": "0412-6010040",
    },
    {
        "full_name": "Gustavo Adolfo Mendoza",
        "doc_type": "V",
        "doc_num": "V-63646566",
        "email": "gamendoza@mail.com",
        "phone": "0414-6010041",
    },
    {
        "full_name": "Gloria Esperanza Barrios",
        "doc_type": "V",
        "doc_num": "V-67686970",
        "email": "gebarrios@mail.com",
        "phone": "0424-6010042",
    },
    {
        "full_name": "Óscar Alberto Figueroa",
        "doc_type": "V",
        "doc_num": "V-71727374",
        "email": "oafigueroa@mail.com",
        "phone": "0416-6010043",
    },
    {
        "full_name": "Mirna Elizabeth Colmenares",
        "doc_type": "V",
        "doc_num": "V-75767778",
        "email": "mecolmenares@mail.com",
        "phone": "0412-6010044",
    },
    {
        "full_name": "Adrián Simón Calderón",
        "doc_type": "V",
        "doc_num": "V-79808182",
        "email": "ascalderon@mail.com",
        "phone": "0414-6010045",
    },
    {
        "full_name": "Teresa Concepción Gil",
        "doc_type": "V",
        "doc_num": "V-83848586",
        "email": "tcgil@mail.com",
        "phone": "0424-6010046",
    },
    {
        "full_name": "Ernesto Luis Villalobos",
        "doc_type": "V",
        "doc_num": "V-87888990",
        "email": "elvillalobos@mail.com",
        "phone": "0416-6010047",
    },
    {
        "full_name": "Yolanda Cecilia Briceño",
        "doc_type": "V",
        "doc_num": "V-91929394",
        "email": "ycbriceno@mail.com",
        "phone": "0412-6010048",
    },
    {
        "full_name": "Alfredo Segundo Domínguez",
        "doc_type": "V",
        "doc_num": "V-95969798",
        "email": "asdominguez@mail.com",
        "phone": "0414-6010049",
    },
    {
        "full_name": "Marisol Beatriz Acevedo",
        "doc_type": "V",
        "doc_num": "V-14253647",
        "email": "mbacevedo@mail.com",
        "phone": "0424-6010050",
    },
]

# ── Vehículos ─────────────────────────────────────────────────────────────────
# Campos: (vin_n, branch_idx, brand, model, year, price, mileage,
#          color, transmission, fuel_type, vehicle_type, status_key)
# status_key: D=disponible  R=reservado  V=vendido  E=en_proceso

_D, _R, _V, _E = "D", "R", "V", "E"

VEHICLES: list[tuple] = [
    # ── Sucursal 0: Caracas Centro (17 vehículos) ─────────────────────────────
    (
        1,
        0,
        "Toyota",
        "Corolla",
        2020,
        22500,
        38000,
        "Blanco",
        "Automatica",
        "Gasolina",
        "Sedan",
        _D,
    ),
    (2, 0, "Toyota", "Hilux", 2021, 52000, 28000, "Plata", "Automatica", "Diesel", "Pickup", _D),
    (
        3,
        0,
        "Toyota",
        "Land Cruiser Prado",
        2022,
        98000,
        12000,
        "Negro",
        "Automatica",
        "Diesel",
        "SUV",
        _D,
    ),
    (4, 0, "Chevrolet", "Captiva", 2021, 32000, 22000, "Gris", "Automatica", "Gasolina", "SUV", _R),
    (5, 0, "Chevrolet", "D-Max", 2020, 38000, 45000, "Blanco", "Manual", "Diesel", "Pickup", _V),
    (6, 0, "Ford", "Ranger", 2021, 48000, 31000, "Plata", "Automatica", "Diesel", "Pickup", _D),
    (7, 0, "Ford", "Explorer", 2022, 65000, 15000, "Negro", "Automatica", "Gasolina", "SUV", _D),
    (8, 0, "Hyundai", "Tucson", 2021, 36000, 27000, "Rojo", "Automatica", "Gasolina", "SUV", _D),
    (
        9,
        0,
        "Hyundai",
        "Accent",
        2020,
        13500,
        52000,
        "Blanco",
        "Automatica",
        "Gasolina",
        "Sedan",
        _V,
    ),
    (10, 0, "Nissan", "Frontier", 2021, 44000, 29000, "Plata", "Manual", "Diesel", "Pickup", _D),
    (11, 0, "Nissan", "X-Trail", 2022, 38500, 18000, "Gris", "Automatica", "Gasolina", "SUV", _D),
    (12, 0, "Kia", "Sportage", 2022, 39000, 14000, "Azul", "Automatica", "Gasolina", "SUV", _D),
    (13, 0, "Honda", "CR-V", 2021, 42000, 22000, "Plata", "Automatica", "Gasolina", "SUV", _D),
    (
        14,
        0,
        "Volkswagen",
        "Tiguan",
        2021,
        40000,
        25000,
        "Negro",
        "Automatica",
        "Gasolina",
        "SUV",
        _D,
    ),
    (15, 0, "Jeep", "Wrangler", 2022, 78000, 8000, "Rojo", "Automatica", "Gasolina", "SUV", _D),
    (16, 0, "Mazda", "CX-5", 2021, 38000, 20000, "Gris", "Automatica", "Gasolina", "SUV", _D),
    (17, 0, "Toyota", "RAV4", 2020, 41000, 34000, "Blanco", "Automatica", "Gasolina", "SUV", _V),
    # ── Sucursal 1: Caracas Este (16 vehículos) ───────────────────────────────
    (18, 1, "Toyota", "Fortuner", 2021, 68000, 19000, "Negro", "Automatica", "Diesel", "SUV", _R),
    (19, 1, "Toyota", "Camry", 2018, 28000, 72000, "Dorado", "Automatica", "Gasolina", "Sedan", _V),
    (20, 1, "Chevrolet", "Aveo", 2019, 9800, 88000, "Rojo", "Manual", "Gasolina", "Sedan", _D),
    (21, 1, "Chevrolet", "Sail", 2020, 12500, 61000, "Azul", "Automatica", "Gasolina", "Sedan", _D),
    (22, 1, "Ford", "F-150", 2021, 62000, 24000, "Plata", "Automatica", "Gasolina", "Pickup", _D),
    (23, 1, "Hyundai", "Santa Fe", 2022, 52000, 11000, "Gris", "Automatica", "Gasolina", "SUV", _D),
    (24, 1, "Hyundai", "Creta", 2022, 29500, 16000, "Blanco", "Automatica", "Gasolina", "SUV", _R),
    (25, 1, "Nissan", "Kicks", 2022, 28000, 17000, "Naranja", "Automatica", "Gasolina", "SUV", _D),
    (
        26,
        1,
        "Mitsubishi",
        "Outlander",
        2022,
        47000,
        13000,
        "Plata",
        "Automatica",
        "Gasolina",
        "SUV",
        _D,
    ),
    (
        27,
        1,
        "Mitsubishi",
        "Eclipse Cross",
        2021,
        38000,
        29000,
        "Negro",
        "Automatica",
        "Gasolina",
        "SUV",
        _V,
    ),
    (28, 1, "Kia", "Sorento", 2022, 55000, 10000, "Azul", "Automatica", "Gasolina", "SUV", _D),
    (29, 1, "Honda", "Accord", 2022, 38500, 14000, "Negro", "Automatica", "Gasolina", "Sedan", _D),
    (
        30,
        1,
        "Volkswagen",
        "T-Cross",
        2022,
        31000,
        18000,
        "Blanco",
        "Automatica",
        "Gasolina",
        "SUV",
        _D,
    ),
    (
        31,
        1,
        "Jeep",
        "Grand Cherokee",
        2021,
        82000,
        16000,
        "Negro",
        "Automatica",
        "Gasolina",
        "SUV",
        _D,
    ),
    (32, 1, "Renault", "Duster", 2020, 19000, 48000, "Naranja", "Manual", "Gasolina", "SUV", _D),
    (
        33,
        1,
        "Toyota",
        "Corolla Cross",
        2022,
        34000,
        12000,
        "Blanco",
        "Automatica",
        "Hibrido",
        "SUV",
        _D,
    ),
    # ── Sucursal 2: Maracaibo (16 vehículos) ──────────────────────────────────
    (34, 2, "Toyota", "Hilux", 2020, 46000, 55000, "Gris", "Manual", "Diesel", "Pickup", _V),
    (35, 2, "Toyota", "Yaris", 2020, 14500, 64000, "Blanco", "Manual", "Gasolina", "Hatchback", _D),
    (
        36,
        2,
        "Chevrolet",
        "Tracker",
        2022,
        30000,
        19000,
        "Rojo",
        "Automatica",
        "Gasolina",
        "SUV",
        _D,
    ),
    (37, 2, "Chevrolet", "Aveo", 2018, 8200, 102000, "Azul", "Manual", "Gasolina", "Sedan", _D),
    (38, 2, "Ford", "Ranger", 2020, 44000, 49000, "Negro", "Automatica", "Diesel", "Pickup", _V),
    (39, 2, "Ford", "Escape", 2020, 31000, 42000, "Plata", "Automatica", "Gasolina", "SUV", _D),
    (
        40,
        2,
        "Hyundai",
        "Elantra",
        2021,
        21000,
        36000,
        "Gris",
        "Automatica",
        "Gasolina",
        "Sedan",
        _D,
    ),
    (
        41,
        2,
        "Nissan",
        "Sentra",
        2020,
        18500,
        57000,
        "Blanco",
        "Automatica",
        "Gasolina",
        "Sedan",
        _V,
    ),
    (42, 2, "Mitsubishi", "L200", 2021, 48000, 31000, "Plata", "Manual", "Diesel", "Pickup", _D),
    (43, 2, "Kia", "Cerato", 2021, 22000, 33000, "Rojo", "Automatica", "Gasolina", "Sedan", _D),
    (44, 2, "Honda", "Fit", 2020, 12800, 69000, "Gris", "Manual", "Gasolina", "Hatchback", _D),
    (
        45,
        2,
        "Volkswagen",
        "Gol",
        2019,
        9500,
        91000,
        "Blanco",
        "Manual",
        "Gasolina",
        "Hatchback",
        _D,
    ),
    (46, 2, "Jeep", "Compass", 2022, 45000, 14000, "Gris", "Automatica", "Gasolina", "SUV", _D),
    (47, 2, "Renault", "Logan", 2019, 10500, 78000, "Plata", "Manual", "Gasolina", "Sedan", _D),
    (
        48,
        2,
        "Renault",
        "Sandero",
        2020,
        11000,
        65000,
        "Gris",
        "Manual",
        "Gasolina",
        "Hatchback",
        _D,
    ),
    (49, 2, "Mazda", "Mazda 3", 2020, 22000, 44000, "Negro", "Automatica", "Gasolina", "Sedan", _D),
    # ── Sucursal 3: Valencia (16 vehículos) ───────────────────────────────────
    (50, 3, "Toyota", "Hilux", 2019, 42000, 68000, "Plata", "Manual", "Diesel", "Pickup", _V),
    (
        51,
        3,
        "Toyota",
        "Land Cruiser 200",
        2020,
        118000,
        27000,
        "Negro",
        "Automatica",
        "Diesel",
        "SUV",
        _D,
    ),
    (
        52,
        3,
        "Chevrolet",
        "Tracker",
        2021,
        28500,
        32000,
        "Verde",
        "Automatica",
        "Gasolina",
        "SUV",
        _R,
    ),
    (
        53,
        3,
        "Chevrolet",
        "Blazer",
        2021,
        48000,
        21000,
        "Negro",
        "Automatica",
        "Gasolina",
        "SUV",
        _D,
    ),
    (54, 3, "Ford", "Ranger", 2019, 40000, 71000, "Blanco", "Manual", "Diesel", "Pickup", _V),
    (55, 3, "Ford", "EcoSport", 2020, 22000, 50000, "Rojo", "Automatica", "Gasolina", "SUV", _D),
    (56, 3, "Hyundai", "Tucson", 2020, 31000, 58000, "Plata", "Automatica", "Gasolina", "SUV", _V),
    (
        57,
        3,
        "Nissan",
        "March",
        2019,
        9000,
        95000,
        "Amarillo",
        "Manual",
        "Gasolina",
        "Hatchback",
        _D,
    ),
    (58, 3, "Nissan", "X-Trail", 2021, 36000, 30000, "Gris", "Automatica", "Gasolina", "SUV", _R),
    (
        59,
        3,
        "Mitsubishi",
        "Montero Sport",
        2021,
        52000,
        24000,
        "Negro",
        "Automatica",
        "Gasolina",
        "SUV",
        _D,
    ),
    (60, 3, "Mitsubishi", "L200", 2020, 44000, 47000, "Plata", "Manual", "Diesel", "Pickup", _R),
    (61, 3, "Kia", "Stinger", 2020, 38000, 41000, "Gris", "Automatica", "Gasolina", "Sedan", _D),
    (62, 3, "Honda", "Pilot", 2022, 62000, 9000, "Negro", "Automatica", "Gasolina", "SUV", _D),
    (
        63,
        3,
        "Volkswagen",
        "Golf",
        2020,
        21000,
        53000,
        "Blanco",
        "Automatica",
        "Gasolina",
        "Hatchback",
        _V,
    ),
    (64, 3, "Jeep", "Gladiator", 2021, 72000, 22000, "Naranja", "Manual", "Diesel", "Pickup", _V),
    (65, 3, "Kia", "Seltos", 2021, 27500, 35000, "Azul", "Automatica", "Gasolina", "SUV", _V),
    # ── Sucursal 4: Barquisimeto (16 vehículos) ───────────────────────────────
    (66, 4, "Toyota", "RAV4", 2021, 43000, 26000, "Blanco", "Automatica", "Gasolina", "SUV", _D),
    (67, 4, "Toyota", "Fortuner", 2020, 62000, 38000, "Negro", "Automatica", "Diesel", "SUV", _E),
    (68, 4, "Toyota", "Hiace", 2018, 34000, 82000, "Blanco", "Manual", "Diesel", "Van", _D),
    (69, 4, "Chevrolet", "Sail", 2019, 11500, 74000, "Verde", "Manual", "Gasolina", "Sedan", _V),
    (
        70,
        4,
        "Chevrolet",
        "Captiva",
        2020,
        29500,
        43000,
        "Gris",
        "Automatica",
        "Gasolina",
        "SUV",
        _D,
    ),
    (71, 4, "Ford", "Bronco", 2022, 74000, 7000, "Naranja", "Automatica", "Gasolina", "SUV", _R),
    (72, 4, "Nissan", "Frontier", 2020, 42000, 52000, "Plata", "Manual", "Diesel", "Pickup", _V),
    (73, 4, "Nissan", "Navara", 2021, 48000, 28000, "Negro", "Manual", "Diesel", "Pickup", _D),
    (
        74,
        4,
        "Mitsubishi",
        "Outlander",
        2020,
        38000,
        46000,
        "Blanco",
        "Automatica",
        "Gasolina",
        "SUV",
        _D,
    ),
    (75, 4, "Kia", "Sportage", 2021, 35500, 31000, "Rojo", "Automatica", "Gasolina", "SUV", _R),
    (76, 4, "Honda", "HR-V", 2021, 27000, 38000, "Gris", "Automatica", "Gasolina", "SUV", _V),
    (
        77,
        4,
        "Volkswagen",
        "Polo",
        2021,
        18500,
        42000,
        "Blanco",
        "Automatica",
        "Gasolina",
        "Sedan",
        _D,
    ),
    (78, 4, "Mazda", "BT-50", 2021, 46000, 35000, "Plata", "Manual", "Diesel", "Pickup", _V),
    (79, 4, "Hyundai", "H-1", 2019, 32000, 68000, "Blanco", "Manual", "Diesel", "Van", _D),
    (
        80,
        4,
        "Hyundai",
        "Sonata",
        2021,
        28000,
        31000,
        "Negro",
        "Automatica",
        "Gasolina",
        "Sedan",
        _D,
    ),
    (
        81,
        4,
        "Toyota",
        "Corolla",
        2019,
        19500,
        63000,
        "Vino",
        "Automatica",
        "Gasolina",
        "Sedan",
        _D,
    ),
]

# ── Ventas ────────────────────────────────────────────────────────────────────
# Campos: (vin_n, client_doc, seller_email, branch_idx,
#          sale_date, sale_price, cost, payment_method, notes)

SALES: list[tuple] = [
    # Caracas Centro
    (
        5,
        "V-12345678",
        "laura.perez@redline.com",
        0,
        datetime(2025, 1, 15, 10, 30, tzinfo=timezone.utc),
        37500,
        32000,
        "Financiamiento",
        "Crédito banco",
    ),
    (
        9,
        "V-23456789",
        "laura.perez@redline.com",
        0,
        datetime(2025, 2, 10, 9, 15, tzinfo=timezone.utc),
        13200,
        11000,
        "Efectivo",
        "Venta de contado",
    ),
    (
        17,
        "V-34567890",
        "laura.perez@redline.com",
        0,
        datetime(2025, 3, 22, 14, 45, tzinfo=timezone.utc),
        40500,
        35000,
        "Transferencia",
        None,
    ),
    # Caracas Este
    (
        19,
        "V-45678901",
        "miguel.torres@redline.com",
        1,
        datetime(2025, 1, 28, 11, 0, tzinfo=timezone.utc),
        27500,
        23000,
        "Zelle",
        "Pago exterior",
    ),
    (
        27,
        "V-56789012",
        "miguel.torres@redline.com",
        1,
        datetime(2025, 4, 14, 16, 20, tzinfo=timezone.utc),
        37500,
        32000,
        "Transferencia",
        None,
    ),
    # Maracaibo
    (
        34,
        "V-67890123",
        "sofia.garcia@redline.com",
        2,
        datetime(2025, 2, 25, 10, 0, tzinfo=timezone.utc),
        45500,
        39000,
        "Efectivo",
        None,
    ),
    (
        38,
        "V-78901234",
        "sofia.garcia@redline.com",
        2,
        datetime(2025, 5, 16, 13, 30, tzinfo=timezone.utc),
        43500,
        37000,
        "Financiamiento",
        "Crédito BBVA",
    ),
    (
        41,
        "V-89012345",
        "sofia.garcia@redline.com",
        2,
        datetime(2025, 6, 30, 9, 45, tzinfo=timezone.utc),
        18200,
        15500,
        "Transferencia",
        None,
    ),
    # Valencia
    (
        50,
        "V-90123456",
        "roberto.silva@redline.com",
        3,
        datetime(2025, 3, 12, 11, 15, tzinfo=timezone.utc),
        41500,
        35500,
        "Financiamiento",
        "Crédito Mercantil",
    ),
    (
        54,
        "V-01234567",
        "roberto.silva@redline.com",
        3,
        datetime(2025, 5, 29, 14, 0, tzinfo=timezone.utc),
        39500,
        34000,
        "Efectivo",
        "Camión de trabajo",
    ),
    (
        56,
        "V-11223344",
        "roberto.silva@redline.com",
        3,
        datetime(2025, 7, 20, 9, 30, tzinfo=timezone.utc),
        30500,
        26000,
        "Zelle",
        None,
    ),
    (
        63,
        "V-22334455",
        "roberto.silva@redline.com",
        3,
        datetime(2025, 8, 25, 16, 0, tzinfo=timezone.utc),
        20500,
        17500,
        "Transferencia",
        None,
    ),
    (
        64,
        "V-33445566",
        "roberto.silva@redline.com",
        3,
        datetime(2025, 9, 10, 10, 45, tzinfo=timezone.utc),
        71000,
        61000,
        "Efectivo",
        "Cliente frecuente",
    ),
    (
        65,
        "V-44556677",
        "roberto.silva@redline.com",
        3,
        datetime(2025, 10, 4, 12, 30, tzinfo=timezone.utc),
        27000,
        23000,
        "Transferencia",
        None,
    ),
    # Barquisimeto
    (
        69,
        "V-55667788",
        "ana.jimenez@redline.com",
        4,
        datetime(2025, 4, 29, 10, 0, tzinfo=timezone.utc),
        11200,
        9500,
        "Efectivo",
        None,
    ),
    (
        72,
        "V-66778899",
        "ana.jimenez@redline.com",
        4,
        datetime(2025, 6, 18, 11, 30, tzinfo=timezone.utc),
        41500,
        35500,
        "Financiamiento",
        "Crédito Banesco",
    ),
    (
        76,
        "V-77889900",
        "ana.jimenez@redline.com",
        4,
        datetime(2025, 8, 5, 14, 15, tzinfo=timezone.utc),
        26500,
        22500,
        "Zelle",
        None,
    ),
    (
        78,
        "V-88990011",
        "ana.jimenez@redline.com",
        4,
        datetime(2025, 9, 22, 9, 0, tzinfo=timezone.utc),
        45500,
        39000,
        "Efectivo",
        "Venta de contado",
    ),
]

# ── Mapas internos ────────────────────────────────────────────────────────────

_STATUS_MAP: dict[str, VehicleStatus] = {
    "D": VehicleStatus.DISPONIBLE,
    "R": VehicleStatus.RESERVADO,
    "V": VehicleStatus.VENDIDO,
    "E": VehicleStatus.EN_PROCESO,
}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_or_create_branch(db, data: dict) -> Branch:
    existing = db.scalar(select(Branch).where(Branch.name == data["name"]))
    if existing:
        return existing
    branch = Branch(
        id=uuid.uuid4(),
        name=data["name"],
        address=data.get("address"),
        phone=data.get("phone"),
        email=data.get("email"),
        status=StatusGeneric.ACTIVE,
    )
    db.add(branch)
    db.flush()
    return branch


def _ensure_branch_access(db, user: User, branch: Branch) -> None:
    existing = db.scalar(
        select(UserBranchAccess).where(
            UserBranchAccess.user_id == user.id,
            UserBranchAccess.branch_id == branch.id,
        )
    )
    if not existing:
        db.add(UserBranchAccess(id=uuid.uuid4(), user_id=user.id, branch_id=branch.id))
        db.flush()


def _get_or_create_user(
    db,
    data: dict,
    branch_map: dict[str, Branch],
    role_map: dict[str, Role],
) -> User:
    existing = db.scalar(select(User).where(User.email == data["email"]))
    if existing:
        return existing
    role = role_map[data["role_code"]]
    user = User(
        id=uuid.uuid4(),
        role_id=role.id,
        full_name=data["full_name"],
        email=data["email"],
        phone=data.get("phone"),
        password_hash=get_password_hash("Demo123*"),
        status=StatusGeneric.ACTIVE,
    )
    db.add(user)
    db.flush()
    branch_names = data.get("branch_names")
    if branch_names is None:
        for branch in branch_map.values():
            _ensure_branch_access(db, user, branch)
    else:
        for bname in branch_names:
            _ensure_branch_access(db, user, branch_map[bname])
    return user


def _get_or_create_client(db, data: dict) -> Client:
    existing = db.scalar(select(Client).where(Client.document_number == data["doc_num"]))
    if existing:
        return existing
    client = Client(
        id=uuid.uuid4(),
        full_name=data["full_name"],
        document_type=data.get("doc_type"),
        document_number=data["doc_num"],
        email=data.get("email"),
        phone=data.get("phone"),
        status=StatusGeneric.ACTIVE,
    )
    db.add(client)
    db.flush()
    return client


def _get_or_create_vehicle(db, data: tuple, branches: list[Branch]) -> Vehicle:
    (
        vin_n,
        branch_idx,
        brand,
        model,
        year,
        price,
        mileage,
        color,
        transmission,
        fuel_type,
        vehicle_type,
        status_key,
    ) = data
    vin = f"RLDEMO{vin_n:04d}"
    existing = db.scalar(select(Vehicle).where(Vehicle.vin == vin))
    if existing:
        return existing
    vehicle = Vehicle(
        id=uuid.uuid4(),
        branch_id=branches[branch_idx].id,
        brand=brand,
        model=model,
        vehicle_year=year,
        price=price,
        mileage=mileage,
        vin=vin,
        color=color,
        transmission=transmission,
        fuel_type=fuel_type,
        vehicle_type=vehicle_type,
        status=_STATUS_MAP[status_key],
    )
    db.add(vehicle)
    db.flush()
    return vehicle


def _get_or_create_sale(
    db,
    data: tuple,
    vehicle_map: dict[int, Vehicle],
    client_by_doc: dict[str, Client],
    user_by_email: dict[str, User],
    branches: list[Branch],
) -> Sale:
    (
        vin_n,
        client_doc,
        seller_email,
        branch_idx,
        sale_date,
        sale_price,
        cost,
        payment_method,
        notes,
    ) = data
    vehicle = vehicle_map[vin_n]
    existing = db.scalar(select(Sale).where(Sale.vehicle_id == vehicle.id))
    if existing:
        return existing
    client = client_by_doc[client_doc]
    seller = user_by_email.get(seller_email)
    profit = sale_price - cost
    sale = Sale(
        id=uuid.uuid4(),
        vehicle_id=vehicle.id,
        client_id=client.id,
        seller_user_id=seller.id if seller else None,
        branch_id=branches[branch_idx].id,
        sale_date=sale_date,
        sale_price=sale_price,
        cost=cost,
        profit=profit,
        payment_method=payment_method,
        status=SaleStatus.COMPLETADA,
        notes=notes,
    )
    db.add(sale)
    db.flush()
    return sale


# ── Punto de entrada ──────────────────────────────────────────────────────────


def run() -> None:
    db = SessionLocal()
    try:
        # Guard: idempotencia — salta si ya fue ejecutado
        if db.scalar(select(Branch).where(Branch.name == "Redline Caracas Centro")):
            print("Demo seed: datos ya existen, saltando.")
            return

        role_map: dict[str, Role] = {r.code: r for r in db.scalars(select(Role)).all()}

        # 1. Sucursales
        branches: list[Branch] = [_get_or_create_branch(db, b) for b in BRANCHES]
        branch_map: dict[str, Branch] = {b.name: b for b in branches}

        # 2. Usuarios demo
        user_by_email: dict[str, User] = {}
        for u_data in USERS:
            user = _get_or_create_user(db, u_data, branch_map, role_map)
            user_by_email[u_data["email"]] = user

        # 3. Clientes
        client_by_doc: dict[str, Client] = {}
        for c_data in CLIENTS:
            client = _get_or_create_client(db, c_data)
            client_by_doc[c_data["doc_num"]] = client

        # 4. Vehículos
        vehicle_map: dict[int, Vehicle] = {}
        for v_data in VEHICLES:
            vehicle = _get_or_create_vehicle(db, v_data, branches)
            vehicle_map[v_data[0]] = vehicle

        # 5. Ventas
        for s_data in SALES:
            _get_or_create_sale(db, s_data, vehicle_map, client_by_doc, user_by_email, branches)

        db.commit()
        print("Demo seed completado exitosamente.")
        print(f"  Sucursales : {len(BRANCHES)}")
        print(f"  Usuarios   : {len(USERS)}  (contraseña: Demo123*)")
        print(f"  Clientes   : {len(CLIENTS)}")
        print(f"  Vehículos  : {len(VEHICLES)}")
        print(f"  Ventas     : {len(SALES)}")
        print(
            f"  Total      : {len(BRANCHES) + len(USERS) + len(CLIENTS) + len(VEHICLES) + len(SALES)} registros"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
