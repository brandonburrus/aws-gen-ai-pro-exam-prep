"""
Generate an Exam Gotchas PDF from the GOTCHAS.md file for the
AWS Certified Generative AI Developer - Professional (AIP-C01) exam.
"""

import os

from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)

from pdf_utils import (
    BASE_DIR,
    PRIMARY,
    SECONDARY,
    ACCENT,
    TABLE_HEADER_BG,
    TABLE_HEADER_FG,
    TABLE_ALT_ROW,
    build_styles,
    build_doc,
    add_table_of_contents,
    parse_markdown_to_flowables,
)


MD_FILE = "GOTCHAS.md"
OUTPUT_FILE = os.path.join(BASE_DIR, "AIP-C01-Exam-Gotchas.pdf")


def add_cover_page(flowables, styles, available_width):
    flowables.append(Spacer(1, 2 * inch))

    flowables.append(
        Paragraph(
            "AWS Certified Generative AI<br/>Developer - Professional",
            styles["CoverTitle"],
        )
    )
    flowables.append(Spacer(1, 8))
    flowables.append(Paragraph("AIP-C01 Exam Gotchas", styles["CoverSubtitle"]))
    flowables.append(Spacer(1, 0.5 * inch))

    flowables.append(
        HRFlowable(
            width="60%",
            thickness=2,
            color=SECONDARY,
            spaceBefore=0,
            spaceAfter=12,
        )
    )

    flowables.append(
        Paragraph(
            "Tricky, counterintuitive, and commonly confused facts<br/>"
            "organized by domain and task.<br/>"
            "These are the details that exam questions exploit<br/>"
            "to create plausible-but-wrong answer choices.",
            styles["CoverDesc"],
        )
    )

    flowables.append(Spacer(1, 1 * inch))

    domain_data = [
        ["Domain", "Weight"],
        ["1. Design and Implement Generative AI Solutions", "31%"],
        ["2. Develop Generative AI Applications", "26%"],
        ["3. Secure Generative AI Solutions", "20%"],
        ["4. Optimize Generative AI Solutions", "12%"],
        ["5. Evaluate Generative AI Solutions", "11%"],
    ]
    t = Table(domain_data, colWidths=[4.5 * inch, 1 * inch])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), TABLE_HEADER_FG),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 13),
                ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, TABLE_ALT_ROW]),
            ]
        )
    )
    flowables.append(t)
    flowables.append(PageBreak())


def main():
    styles = build_styles()
    doc, available_width = build_doc(
        OUTPUT_FILE,
        title="AWS Certified Generative AI Developer - Professional (AIP-C01) Exam Gotchas",
        footer_label="AIP-C01 Exam Gotchas",
    )

    flowables = []
    add_cover_page(flowables, styles, available_width)
    add_table_of_contents(flowables, styles)
    flowables.append(PageBreak())

    filepath = os.path.join(BASE_DIR, MD_FILE)
    if not os.path.exists(filepath):
        print(f"ERROR: {filepath} not found.")
        return

    print(f"Processing: {MD_FILE}")

    with open(filepath, "r", encoding="utf-8") as f:
        md_text = f.read()

    flowables.extend(parse_markdown_to_flowables(md_text, styles, available_width))

    print(f"\nBuilding PDF: {OUTPUT_FILE}")
    doc.multiBuild(flowables)
    print(f"Done. File size: {os.path.getsize(OUTPUT_FILE) / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    main()
