from __future__ import annotations

import csv
from io import BytesIO, StringIO
from typing import Iterable

from openpyxl import Workbook
from openpyxl.styles import Font


def build_csv_bytes(rows: Iterable[dict], headers: list[str]) -> bytes:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=headers)
    writer.writeheader()
    for row in rows:
        writer.writerow({header: row.get(header) for header in headers})
    return buffer.getvalue().encode("utf-8")



def build_xlsx_bytes(rows: Iterable[dict], headers: list[str], sheet_name: str) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name[:31]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in rows:
        ws.append([row.get(header) for header in headers])
    for column in ws.columns:
        max_length = 0
        letter = column[0].column_letter
        for cell in column:
            value = "" if cell.value is None else str(cell.value)
            max_length = max(max_length, len(value))
        ws.column_dimensions[letter].width = min(max_length + 2, 40)
    stream = BytesIO()
    wb.save(stream)
    return stream.getvalue()
