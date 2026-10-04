import io
from fpdf import FPDF


def build_pdf_report(
    summary: str,
    kpi_results: list[tuple[str, str]],
    chart_images: list[tuple[str, bytes]],
    rows_shown: int,
    rows_total: int,
) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Dashboard Report", ln=True)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Rows analyzed: {rows_shown:,} of {rows_total:,}", ln=True)
    pdf.ln(4)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "Key Insights", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 6, summary or "No summary available.")
    pdf.ln(4)

    if kpi_results:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Key Metrics", ln=True)
        pdf.set_font("Helvetica", "", 11)
        for label, value in kpi_results:
            pdf.cell(0, 7, f"- {label}: {value}", ln=True)
        pdf.ln(4)

    if chart_images:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Charts", ln=True)

        page_width = pdf.w - 2 * pdf.l_margin
        for title, png_bytes in chart_images:
            # Start a new page for each chart if there isn't enough room left
            if pdf.get_y() > pdf.h - 110:
                pdf.add_page()

            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 8, title, ln=True)
            pdf.image(io.BytesIO(png_bytes), w=page_width * 0.85)
            pdf.ln(4)

    return bytes(pdf.output())