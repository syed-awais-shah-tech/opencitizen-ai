"""Helper functions for dynamically generating small, valid test PDFs for unit tests."""

import io
import pypdf


def create_test_pdf(pages_text: list[str]) -> bytes:
    """Generate a minimal valid PDF containing the specified text on each page."""
    pdf_parts = [b"%PDF-1.4\n"]
    total_pages = len(pages_text)
    offsets: list[int] = []

    def add_obj(obj_bytes: bytes) -> None:
        offsets.append(sum(len(p) for p in pdf_parts))
        pdf_parts.append(obj_bytes)

    add_obj(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")

    page_refs = " ".join(f"{4 + i * 2} 0 R" for i in range(total_pages))
    add_obj(
        f"2 0 obj\n<< /Type /Pages /Kids [{page_refs}] /Count {total_pages} >>\nendobj\n".encode(
            "utf-8"
        )
    )
    add_obj(
        b"3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    )

    for i, text in enumerate(pages_text):
        content_num = 5 + i * 2
        page_num = 4 + i * 2
        clean = (
            text.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )
        stream_data = f"BT /F1 12 Tf 50 700 Td ({clean}) Tj ET".encode("utf-8")

        content_obj = (
            f"{content_num} 0 obj\n<< /Length {len(stream_data)} >>\nstream\n".encode(
                "utf-8"
            )
            + stream_data
            + b"\nendstream\nendobj\n"
        )

        page_obj = (
            f"{page_num} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_num} 0 R >>\nendobj\n".encode(
                "utf-8"
            )
        )

        add_obj(page_obj)
        add_obj(content_obj)

    xref_offset = sum(len(p) for p in pdf_parts)
    num_objs = 4 + total_pages * 2
    xref = f"xref\n0 {num_objs}\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n"
    trailer = (
        f"trailer\n<< /Size {num_objs} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF"
    )
    pdf_parts.append(xref.encode("utf-8") + trailer.encode("utf-8"))

    return b"".join(pdf_parts)


def create_blank_pdf(num_pages: int = 1) -> bytes:
    """Generate a valid PDF containing empty/blank pages using pypdf."""
    writer = pypdf.PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=612, height=792)
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()
