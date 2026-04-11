from __future__ import annotations

from io import BytesIO

from fastapi.responses import StreamingResponse


PDF_MEDIA_TYPE = "application/pdf"
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
CSV_MEDIA_TYPE = "text/csv; charset=utf-8"


def stream_bytes(*, content: bytes, media_type: str, filename: str, disposition: str = "attachment") -> StreamingResponse:
    return StreamingResponse(
        BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
    )


def stream_pdf(*, content: bytes, filename: str, inline: bool = True) -> StreamingResponse:
    return stream_bytes(
        content=content,
        media_type=PDF_MEDIA_TYPE,
        filename=filename,
        disposition="inline" if inline else "attachment",
    )
