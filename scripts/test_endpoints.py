#!/usr/bin/env python3
"""
Redline API — Test completo de endpoints

Uso:
    python scripts/test_endpoints.py
    python scripts/test_endpoints.py --base-url http://localhost:8000
    python scripts/test_endpoints.py --email admin@redline.com --password Admin123*

Requiere: pip install requests
"""

import argparse
import json
import sys
from dataclasses import dataclass, field

try:
    import requests
except ImportError:
    print("Dependencia faltante. Instala con:  pip install requests")
    sys.exit(1)

# ── Colores ───────────────────────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def _ok(msg):
    return f"{GREEN}✓  {msg}{RESET}"


def _fail(msg):
    return f"{RED}✗  {msg}{RESET}"


def _skip(msg):
    return f"{YELLOW}~  {msg}{RESET}"


def _hdr(msg):
    return f"\n{BOLD}{CYAN}══  {msg}  ══{RESET}"


# ── Estado compartido ─────────────────────────────────────────────────────────
@dataclass
class State:
    base: str
    token: str = ""
    branch_id: str = ""
    vehicle_id: str = ""
    client_id: str = ""
    sale_id: str = ""
    user_id: str = ""
    document_id: str = ""
    results: list = field(default_factory=list)  # (label, True|False|None, detail)

    def headers(self) -> dict:
        h: dict = {}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def url(self, path: str) -> str:
        return f"{self.base}{path}"


# ── Runner ────────────────────────────────────────────────────────────────────
def run(
    s: State,
    label: str,
    method: str,
    path: str,
    expected,
    json_body=None,
    data=None,
    files=None,
    params=None,
    skip_if: str = "",
):
    if skip_if and not getattr(s, skip_if):
        print(_skip(f"{method:6} {path:55} (sin {skip_if})"))
        s.results.append((label, None, f"skipped — no {skip_if}"))
        return None

    expected_codes = expected if isinstance(expected, list) else [expected]

    try:
        resp = requests.request(
            method,
            s.url(path),
            headers=s.headers(),
            json=json_body,
            data=data,
            files=files,
            params=params,
            timeout=20,
        )
    except requests.exceptions.ConnectionError:
        print(_fail(f"{method:6} {path:55} [SIN CONEXIÓN]"))
        s.results.append((label, False, "connection error"))
        return None

    passed = resp.status_code in expected_codes
    detail = str(resp.status_code)

    try:
        body = resp.json()
        if not passed:
            detail += f"  {json.dumps(body, ensure_ascii=False)[:160]}"
    except Exception:
        body = {}

    print((_ok if passed else _fail)(f"{method:6} {path:55} [{resp.status_code}]"))
    s.results.append((label, passed, detail))
    return body if passed else None


def _raw_delete(s: State, path: str, label: str, extra_ok: tuple = ()) -> None:
    try:
        r = requests.delete(s.url(path), headers=s.headers(), timeout=15)
        ok_codes = (204,) + extra_ok
        passed = r.status_code in ok_codes
        s.results.append((label, passed, str(r.status_code)))
        print((_ok if passed else _fail)(f"DELETE {path:53} [{r.status_code}]"))
    except Exception as exc:
        s.results.append((label, False, str(exc)))
        print(_fail(f"DELETE {path:53} [ERR]"))


def print_summary(results: list) -> None:
    passed = sum(1 for _, p, _ in results if p is True)
    skipped = sum(1 for _, p, _ in results if p is None)
    failed = sum(1 for _, p, _ in results if p is False)
    total = len(results)

    print(f"\n{BOLD}{'─' * 70}")
    print(
        f"  Resultados:  {GREEN}{passed} OK{RESET}  "
        f"{RED}{failed} FAIL{RESET}  "
        f"{YELLOW}{skipped} SKIP{RESET}  "
        f"/ {total} total"
    )
    print(f"{'─' * 70}{RESET}")

    if failed:
        print(f"\n{RED}Fallos:{RESET}")
        for lbl, p, detail in results:
            if p is False:
                print(f"  {RED}✗{RESET}  {lbl}  →  {detail}")


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Redline API — test completo de endpoints"
    )
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--email", default="admin@redline.com")
    parser.add_argument("--password", default="Admin123*")
    args = parser.parse_args()

    s = State(base=args.base_url.rstrip("/") + "/api/v1")
    print(f"{BOLD}Redline API — Test completo de endpoints{RESET}")
    print(f"Base URL : {args.base_url}")
    print(f"Usuario  : {args.email}\n")

    # ── Health ────────────────────────────────────────────────────────────────
    print(_hdr("HEALTH"))
    run(s, "GET /health", "GET", "/health", 200)
    run(s, "GET /health/detailed", "GET", "/health/detailed", 200)
    run(s, "GET /health/ready", "GET", "/health/ready", [200, 503])
    run(s, "GET /health/live", "GET", "/health/live", 200)

    try:
        r = requests.get(args.base_url.rstrip("/") + "/", timeout=5)
        passed = r.status_code == 200
        s.results.append(("GET / (root)", passed, str(r.status_code)))
        print((_ok if passed else _fail)(f"GET    /{' ' * 54}[{r.status_code}]"))
    except Exception:
        s.results.append(("GET / (root)", False, "error"))

    # ── Endpoints públicos ────────────────────────────────────────────────────
    print(_hdr("PÚBLICOS (sin autenticación)"))
    run(s, "GET /branches/public", "GET", "/branches/public", 200)
    run(s, "GET /vehicles/public", "GET", "/vehicles/public", 200, params={"limit": 5})
    run(s, "GET /bulk/templates/vehicles", "GET", "/bulk/templates/vehicles", 200)
    run(s, "GET /bulk/templates/clients", "GET", "/bulk/templates/clients", 200)

    # ── Autenticación ─────────────────────────────────────────────────────────
    print(_hdr("AUTENTICACIÓN"))
    body = run(
        s,
        "POST /auth/login",
        "POST",
        "/auth/login",
        200,
        json_body={"email": args.email, "password": args.password},
    )
    if not body or "access_token" not in body:
        print(
            f"\n{RED}Login fallido — no se puede continuar con endpoints protegidos.{RESET}"
        )
        print_summary(s.results)
        sys.exit(1)

    s.token = body["access_token"]
    print(f"  {CYAN}Token obtenido correctamente.{RESET}")

    run(s, "GET /auth/me", "GET", "/auth/me", 200)

    bad = requests.post(
        s.url("/auth/login"),
        json={"email": args.email, "password": "clave_incorrecta"},
        timeout=10,
    )
    passed = bad.status_code == 401
    s.results.append(
        ("POST /auth/login (creds incorrectas) → 401", passed, str(bad.status_code))
    )
    print(
        (_ok if passed else _fail)(
            f"POST   /auth/login (creds incorrectas)                  [{bad.status_code}]"
        )
    )

    # ── Roles ─────────────────────────────────────────────────────────────────
    print(_hdr("ROLES"))
    roles_body = run(s, "GET /roles", "GET", "/roles", 200)
    run(s, "GET /roles/permissions", "GET", "/roles/permissions", 200)
    role_id = (
        roles_body[0]["id"] if roles_body and isinstance(roles_body, list) else None
    )

    # ── Settings ──────────────────────────────────────────────────────────────
    print(_hdr("SETTINGS"))
    run(s, "GET /settings", "GET", "/settings", 200)
    run(
        s,
        "PATCH /settings",
        "PATCH",
        "/settings",
        200,
        json_body={"business_name": "Redline Test"},
    )

    # ── Cache ─────────────────────────────────────────────────────────────────
    print(_hdr("CACHE"))
    run(s, "GET /cache/stats", "GET", "/cache/stats", 200)
    run(s, "GET /cache/keys", "GET", "/cache/keys", 200, params={"pattern": "*"})
    run(s, "POST /cache/warmup", "POST", "/cache/warmup", [200, 500])

    # ── Usuarios ──────────────────────────────────────────────────────────────
    print(_hdr("USUARIOS"))
    run(s, "GET /users", "GET", "/users", 200)

    import time as _t

    _ts = int(_t.time())
    if role_id:
        r = run(
            s,
            "POST /users",
            "POST",
            "/users",
            201,
            json_body={
                "role_id": role_id,
                "full_name": "Test User Script",
                "email": f"test_script_{_ts}@redline.com",
                "phone": "+50299001234",
                "password": "Test1234*",
                "status": "active",
            },
        )
        if r and "id" in r:
            s.user_id = r["id"]

    run(s, "GET /users/{id}", "GET", f"/users/{s.user_id}", 200, skip_if="user_id")
    run(
        s,
        "PATCH /users/{id}",
        "PATCH",
        f"/users/{s.user_id}",
        200,
        json_body={"full_name": "Test User Actualizado"},
        skip_if="user_id",
    )
    run(
        s,
        "PATCH /users/{id}/status",
        "PATCH",
        f"/users/{s.user_id}/status",
        200,
        json_body={"status": "inactive"},
        skip_if="user_id",
    )

    # ── Sucursales ────────────────────────────────────────────────────────────
    print(_hdr("SUCURSALES"))
    run(s, "GET /branches", "GET", "/branches", 200)

    r = run(
        s,
        "POST /branches",
        "POST",
        "/branches",
        201,
        json_body={
            "name": "Sucursal Test Script",
            "address": "Calle Falsa 123, Zona 1",
            "phone": "+50222334455",
            "email": "sucursal.script@redline.com",
            "status": "active",
        },
    )
    if r and "id" in r:
        s.branch_id = r["id"]

    run(
        s,
        "GET /branches/{id}",
        "GET",
        f"/branches/{s.branch_id}",
        200,
        skip_if="branch_id",
    )
    run(
        s,
        "PATCH /branches/{id}",
        "PATCH",
        f"/branches/{s.branch_id}",
        200,
        json_body={"name": "Sucursal Test Actualizada"},
        skip_if="branch_id",
    )

    if s.user_id and s.branch_id:
        run(
            s,
            "PUT /users/{id}/branches",
            "PUT",
            f"/users/{s.user_id}/branches",
            200,
            json_body={"branch_ids": [s.branch_id]},
        )

    # ── Catálogos ─────────────────────────────────────────────────────────────
    print(_hdr("CATÁLOGOS"))
    run(s, "GET /catalogs/vehicles", "GET", "/catalogs/vehicles", 200)
    run(
        s,
        "GET /catalogs/vehicle-models",
        "GET",
        "/catalogs/vehicle-models",
        200,
        params={"brand_code": "toyota"},
    )

    # ── Vehículos ─────────────────────────────────────────────────────────────
    print(_hdr("VEHÍCULOS"))
    run(s, "GET /vehicles", "GET", "/vehicles", 200)

    if s.branch_id:
        vin_suffix = s.branch_id[:8].replace("-", "").upper()
        r = run(
            s,
            "POST /vehicles",
            "POST",
            "/vehicles",
            201,
            json_body={
                "branch_id": s.branch_id,
                "brand": "Toyota",
                "model": "Corolla",
                "vehicle_year": 2022,
                "price": 18500,
                "vin": f"TSCR{vin_suffix}01",
                "mileage": 15000,
                "color": "Blanco",
                "transmission": "automatico",
                "fuel_type": "gasolina",
                "vehicle_type": "sedan",
            },
        )
        if r and "id" in r:
            s.vehicle_id = r["id"]

    run(
        s,
        "GET /vehicles/{id}",
        "GET",
        f"/vehicles/{s.vehicle_id}",
        200,
        skip_if="vehicle_id",
    )
    run(
        s,
        "PATCH /vehicles/{id}",
        "PATCH",
        f"/vehicles/{s.vehicle_id}",
        200,
        json_body={"price": 17900, "mileage": 16000},
        skip_if="vehicle_id",
    )
    run(
        s,
        "GET /vehicles/{id}/status-history",
        "GET",
        f"/vehicles/{s.vehicle_id}/status-history",
        200,
        skip_if="vehicle_id",
    )
    run(
        s,
        "PATCH /vehicles/{id}/status en_proceso",
        "PATCH",
        f"/vehicles/{s.vehicle_id}/status",
        [200, 400],
        json_body={"status": "en_proceso", "notes": "Test"},
        skip_if="vehicle_id",
    )
    run(
        s,
        "PATCH /vehicles/{id}/status disponible",
        "PATCH",
        f"/vehicles/{s.vehicle_id}/status",
        [200, 400],
        json_body={"status": "disponible"},
        skip_if="vehicle_id",
    )
    run(
        s,
        "GET /vehicles/{id}/images",
        "GET",
        f"/vehicles/{s.vehicle_id}/images",
        200,
        skip_if="vehicle_id",
    )
    run(
        s,
        "GET /vehicles/public (search)",
        "GET",
        "/vehicles/public",
        200,
        params={"search": "Toyota", "limit": 10},
    )
    run(
        s,
        "GET /vehicles/public/{id}",
        "GET",
        f"/vehicles/public/{s.vehicle_id}",
        200,
        skip_if="vehicle_id",
    )

    if s.vehicle_id:
        pub_client = {
            "full_name": "Pub Test Script",
            "email": "pub.test.script@redline.com",
            "phone": "+50211223344",
            "document_type": "DPI",
            "document_number": "111222333444",
        }
        run(
            s,
            "POST /vehicles/public/{id}/reserve",
            "POST",
            f"/vehicles/public/{s.vehicle_id}/reserve",
            [200, 201, 422],
            json_body={"client": pub_client},
        )
        run(
            s,
            "(reset → disponible A)",
            "PATCH",
            f"/vehicles/{s.vehicle_id}/status",
            [200, 400],
            json_body={"status": "disponible"},
        )
        run(
            s,
            "POST /vehicles/public/{id}/purchase_intent",
            "POST",
            f"/vehicles/public/{s.vehicle_id}/purchase_intent",
            [200, 201, 422],
            json_body={"client": pub_client},
        )
        run(
            s,
            "(reset → disponible B)",
            "PATCH",
            f"/vehicles/{s.vehicle_id}/status",
            [200, 400],
            json_body={"status": "disponible"},
        )

    # ── Clientes ──────────────────────────────────────────────────────────────
    print(_hdr("CLIENTES"))
    run(s, "GET /clients", "GET", "/clients", 200)

    r = run(
        s,
        "POST /clients",
        "POST",
        "/clients",
        201,
        json_body={
            "full_name": "Cliente Test Script",
            "email": "cliente.test.script@redline.com",
            "phone": "+50299887766",
            "document_type": "DPI",
            "document_number": "998877665544",
        },
    )
    if r and "id" in r:
        s.client_id = r["id"]

    run(
        s,
        "GET /clients/{id}",
        "GET",
        f"/clients/{s.client_id}",
        200,
        skip_if="client_id",
    )
    run(
        s,
        "PATCH /clients/{id}",
        "PATCH",
        f"/clients/{s.client_id}",
        200,
        json_body={"notes": "Actualizado por test script"},
        skip_if="client_id",
    )
    run(
        s,
        "GET /clients/{id}/history",
        "GET",
        f"/clients/{s.client_id}/history",
        200,
        skip_if="client_id",
    )
    run(
        s,
        "GET /clients/{id}/images",
        "GET",
        f"/clients/{s.client_id}/images",
        200,
        skip_if="client_id",
    )

    # ── Ventas ────────────────────────────────────────────────────────────────
    print(_hdr("VENTAS"))
    run(s, "GET /sales", "GET", "/sales", 200)

    if s.vehicle_id and s.client_id and s.branch_id:
        me = requests.get(s.url("/auth/me"), headers=s.headers(), timeout=10).json()
        seller_id = me.get("id", "")

        r = run(
            s,
            "POST /sales",
            "POST",
            "/sales",
            201,
            json_body={
                "vehicle_id": s.vehicle_id,
                "client_id": s.client_id,
                "branch_id": s.branch_id,
                "seller_user_id": seller_id,
                "sale_price": 17900,
                "payment_method": "contado",
                "notes": "Venta generada por test script",
            },
        )
        if r and "id" in r:
            s.sale_id = r["id"]
            run(s, "GET /sales/{id}", "GET", f"/sales/{s.sale_id}", 200)
            run(s, "GET /sales/{id}/pdf", "GET", f"/sales/{s.sale_id}/pdf", 200)
            run(
                s,
                "PATCH /sales/{id}",
                "PATCH",
                f"/sales/{s.sale_id}",
                200,
                json_body={"notes": "Actualizado por test script"},
            )
            run(s, "DELETE /sales/{id}", "DELETE", f"/sales/{s.sale_id}", 204)
            s.sale_id = ""

    # ── Reportes ──────────────────────────────────────────────────────────────
    print(_hdr("REPORTES"))
    run(s, "GET /reports/dashboard", "GET", "/reports/dashboard", 200)
    run(s, "GET /reports/inventory-summary", "GET", "/reports/inventory-summary", 200)
    run(s, "GET /reports/sales-summary", "GET", "/reports/sales-summary", 200)
    run(s, "GET /reports/inventory-rows", "GET", "/reports/inventory-rows", 200)
    run(s, "GET /reports/sales-rows", "GET", "/reports/sales-rows", 200)

    # ── Búsqueda ──────────────────────────────────────────────────────────────
    print(_hdr("BÚSQUEDA"))
    run(
        s,
        "GET /search/vehicles",
        "GET",
        "/search/vehicles",
        200,
        params={"q": "Toyota"},
    )
    run(s, "GET /search/clients", "GET", "/search/clients", 200, params={"q": "Test"})
    run(s, "GET /search (global)", "GET", "/search", 200, params={"q": "Toyota"})
    run(s, "GET /search/suggest", "GET", "/search/suggest", 200, params={"q": "Toy"})

    # ── Bulk ──────────────────────────────────────────────────────────────────
    print(_hdr("BULK"))
    if s.branch_id:
        vin_bulk = "BULK" + s.branch_id[:8].replace("-", "").upper() + "01"
        r = run(
            s,
            "POST /bulk/vehicles",
            "POST",
            "/bulk/vehicles",
            200,
            json_body={
                "vehicles": [
                    {
                        "branch_id": s.branch_id,
                        "brand": "Honda",
                        "model": "Civic",
                        "vehicle_year": 2021,
                        "price": 14000,
                        "vin": vin_bulk,
                    }
                ]
            },
        )
        if r and isinstance(r.get("results"), list) and r["results"]:
            bvid = r["results"][0].get("id")
            if bvid:
                requests.delete(
                    s.url(f"/vehicles/{bvid}"), headers=s.headers(), timeout=10
                )

    import time as _time

    bulk_email = f"bulk.script.{int(_time.time())}@redline.com"
    r = run(
        s,
        "POST /bulk/clients",
        "POST",
        "/bulk/clients",
        200,
        json_body={
            "clients": [{"full_name": "Bulk Cliente Script", "email": bulk_email}]
        },
    )
    if r and isinstance(r.get("results"), list) and r["results"]:
        bcid = r["results"][0].get("id")
        if bcid:
            requests.delete(s.url(f"/clients/{bcid}"), headers=s.headers(), timeout=10)

    if s.branch_id:
        csv_v = (
            "branch_id,brand,model,vehicle_year,price,vin\n"
            f"{s.branch_id},Nissan,Sentra,2020,12000,CSVTEST0001SCRPT\n"
        )
        run(
            s,
            "POST /bulk/vehicles/import",
            "POST",
            "/bulk/vehicles/import",
            [200, 201],
            files={"file": ("vehicles.csv", csv_v.encode(), "text/csv")},
        )

    csv_c = "full_name,email\nCSV Test Script,csv.script@redline.com\n"
    run(
        s,
        "POST /bulk/clients/import",
        "POST",
        "/bulk/clients/import",
        [200, 201],
        files={"file": ("clients.csv", csv_c.encode(), "text/csv")},
    )

    # CSV no-UTF-8 → debe retornar 400
    bad_utf8 = b"\xff\xfe" + "nombre,email\n".encode("utf-16-le")
    r_bad = requests.post(
        s.url("/bulk/clients/import"),
        headers=s.headers(),
        files={"file": ("bad.csv", bad_utf8, "text/csv")},
        timeout=10,
    )
    passed = r_bad.status_code == 400
    s.results.append(
        ("POST /bulk/clients/import (no-UTF-8) → 400", passed, str(r_bad.status_code))
    )
    print(
        (_ok if passed else _fail)(
            f"POST   /bulk/clients/import (CSV no-UTF-8)              [{r_bad.status_code}]"
        )
    )

    # ── Documentos ────────────────────────────────────────────────────────────
    print(_hdr("DOCUMENTOS"))
    run(s, "GET /documents", "GET", "/documents", 200)

    if s.vehicle_id:
        minimal_pdf = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF"
        r = run(
            s,
            "POST /documents",
            "POST",
            "/documents",
            201,
            files={"file": ("contrato.pdf", minimal_pdf, "application/pdf")},
            data={
                "entity_type": "vehicles",
                "entity_id": s.vehicle_id,
                "document_type": "otro",
            },
        )
        if r and "id" in r:
            s.document_id = r["id"]
            run(s, "GET /documents/{id}", "GET", f"/documents/{s.document_id}", 200)
            run(
                s,
                "GET /documents/entity/vehicles/{vid}",
                "GET",
                f"/documents/entity/vehicles/{s.vehicle_id}",
                200,
            )
            run(
                s,
                "PATCH /documents/{id}",
                "PATCH",
                f"/documents/{s.document_id}",
                200,
                json_body={"document_type": "otro"},
            )
            run(
                s,
                "DELETE /documents/{id}",
                "DELETE",
                f"/documents/{s.document_id}",
                204,
            )
            s.document_id = ""

        # Ejecutable binario → debe rechazarse
        r_bad_doc = requests.post(
            s.url("/documents"),
            headers=s.headers(),
            files={"file": ("malware.exe", b"MZ\x90\x00", "application/octet-stream")},
            data={
                "entity_type": "vehicles",
                "entity_id": s.vehicle_id,
                "document_type": "otro",
            },
            timeout=10,
        )
        passed = r_bad_doc.status_code in (400, 422)
        s.results.append(
            ("POST /documents (archivo .exe) → 4xx", passed, str(r_bad_doc.status_code))
        )
        print(
            (_ok if passed else _fail)(
                f"POST   /documents (archivo .exe inválido)               [{r_bad_doc.status_code}]"
            )
        )

    # ── Cache clear ───────────────────────────────────────────────────────────
    print(_hdr("CACHE CLEAR"))
    run(s, "POST /cache/clear", "POST", "/cache/clear", [200, 500])

    # ── Seguridad: sin token → 401 ────────────────────────────────────────────
    print(_hdr("SEGURIDAD — sin token deben retornar 401"))
    protected = [
        ("GET", "/users"),
        ("GET", "/branches"),
        ("GET", "/vehicles"),
        ("GET", "/clients"),
        ("GET", "/sales"),
        ("GET", "/reports/dashboard"),
        ("GET", "/settings"),
        ("GET", "/cache/stats"),
        ("GET", "/search/vehicles?q=x"),
    ]
    for method, path in protected:
        try:
            r = requests.request(method, s.url(path), timeout=10)
            passed = r.status_code == 401
            s.results.append(
                (f"{method} {path} sin token → 401", passed, str(r.status_code))
            )
            print((_ok if passed else _fail)(f"{method:6} {path:53} [{r.status_code}]"))
        except Exception as exc:
            s.results.append((f"{method} {path} sin token", False, str(exc)))

    # ── Limpieza ──────────────────────────────────────────────────────────────
    print(_hdr("LIMPIEZA"))
    if s.vehicle_id:
        _raw_delete(s, f"/vehicles/{s.vehicle_id}", "cleanup vehicle")
    if s.client_id:
        _raw_delete(s, f"/clients/{s.client_id}", "cleanup client")
    if s.user_id:
        _raw_delete(s, f"/users/{s.user_id}", "cleanup user", extra_ok=(403,))
    if s.branch_id:
        _raw_delete(s, f"/branches/{s.branch_id}", "cleanup branch", extra_ok=(409,))

    # ── Resumen ───────────────────────────────────────────────────────────────
    print_summary(s.results)
    sys.exit(0 if all(p is not False for _, p, _ in s.results) else 1)


if __name__ == "__main__":
    main()
