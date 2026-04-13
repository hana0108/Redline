from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


@dataclass(slots=True)
class CompanyInfo:
    business_name: str
    contact_email: str | None = None
    contact_phone: str | None = None
    whatsapp: str | None = None
    address: str | None = None


styles = getSampleStyleSheet()
TITLE_STYLE = styles["Title"]
BODY_STYLE = styles["BodyText"]
LABEL_STYLE = ParagraphStyle(
    "LabelStyle",
    parent=BODY_STYLE,
    fontName="Helvetica-Bold",
    fontSize=10,
    leading=13,
)
SMALL_STYLE = ParagraphStyle(
    "SmallStyle",
    parent=BODY_STYLE,
    fontSize=9,
    textColor=colors.HexColor("#4B5563"),
)


def _safe(value: object | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, Decimal):
        return f"{float(value):,.2f}"
    return str(value)


def _money(value: object | None) -> str:
    if value is None:
        return "—"
    try:
        return f"RD$ {float(value):,.2f}"
    except Exception:
        return str(value)


def _build_doc(title: str, company: CompanyInfo, sections: Iterable[list[list[str]]]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=title,
    )
    story = [
        Paragraph(company.business_name or "Redline", TITLE_STYLE),
        Spacer(1, 4),
        Paragraph(title, LABEL_STYLE),
        Spacer(1, 4),
    ]

    company_lines = [
        company.address,
        company.contact_phone,
        company.whatsapp,
        company.contact_email,
    ]
    for line in [x for x in company_lines if x]:
        story.append(Paragraph(str(line), SMALL_STYLE))
    story.append(Spacer(1, 8))

    for rows in sections:
        table_data = []
        for label, value in rows:
            table_data.append([
                Paragraph(f"<b>{label}</b>", BODY_STYLE),
                Paragraph(_safe(value), BODY_STYLE),
            ])
        table = Table(table_data, colWidths=[55 * mm, 105 * mm], hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E5E7EB")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 10))

    doc.build(story)
    return buffer.getvalue()

def build_sale_pdf(*, company: CompanyInfo, sale, vehicle, client, branch, seller=None) -> bytes:
    sections = [
        [
            ["Venta ID", sale.id],
            ["Fecha de venta", sale.sale_date],
            ["Estado", sale.status.value if hasattr(sale.status, "value") else sale.status],
            ["Precio de venta", _money(sale.sale_price)],
            ["Costo", _money(sale.cost)],
            ["Ganancia", _money(sale.profit)],
            ["Método de pago", sale.payment_method],
        ],
        [
            ["Cliente", client.full_name],
            ["Documento", f"{client.document_type or ''} {client.document_number or ''}".strip() or "—"],
            ["Correo", client.email],
            ["Teléfono", client.phone],
            ["Dirección", client.address],
        ],
        [
            ["Vehículo", f"{vehicle.brand} {vehicle.model} {vehicle.vehicle_year}"],
            ["VIN", vehicle.vin],
            ["Precio listado", _money(vehicle.price)],
            ["Color", vehicle.color],
            ["Transmisión", vehicle.transmission],
        ],
        [
            ["Sucursal", branch.name],
            ["Dirección sucursal", branch.address],
            ["Vendedor", getattr(seller, "full_name", None)],
            ["Notas", sale.notes],
        ],
    ]
    return _build_doc("Comprobante de venta", company, sections)


def build_simple_report_pdf(*, company: CompanyInfo, title: str, rows: list[dict[str, object]]) -> bytes:
    sections: list[list[list[str]]] = []
    for row in rows:
        sections.append([[str(k), _safe(v)] for k, v in row.items()])
    if not sections:
        sections = [[["Resultado", "Sin datos"]]]
    return _build_doc(title, company, sections)
