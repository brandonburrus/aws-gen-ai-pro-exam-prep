"""
Generate a single Study Guide PDF from the domain markdown files for the
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


MD_FILES = [
    "EXAM-GUIDE.md",
    "DOMAIN-1-STUDY-GUIDE.md",
    "DOMAIN-2-STUDY-GUIDE.md",
    "DOMAIN-3-STUDY-GUIDE.md",
    "DOMAIN-4-STUDY-GUIDE.md",
    "DOMAIN-5-STUDY-GUIDE.md",
    "WELL-ARCHITECTED-AI-LENS.md",
    "CONCEPTS.md",
]

OUTPUT_FILE = os.path.join(BASE_DIR, "AIP-C01-Study-Guide.pdf")


def add_cover_page(flowables, styles, available_width):
    flowables.append(Spacer(1, 2 * inch))

    flowables.append(
        Paragraph(
            "AWS Certified Generative AI<br/>Developer - Professional",
            styles["CoverTitle"],
        )
    )
    flowables.append(Spacer(1, 8))
    flowables.append(Paragraph("AIP-C01 Exam Study Guide", styles["CoverSubtitle"]))
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
            "Comprehensive study material covering all five exam domains,<br/>"
            "the AWS Well-Architected Generative AI Lens,<br/>"
            "a ranked concept inventory,<br/>"
            "and key AWS services for GenAI development.",
            styles["CoverDesc"],
        )
    )

    flowables.append(Spacer(1, 1 * inch))

    domain_data = [
        ["Domain", "Weight"],
        ["1. FM Integration, Data Management, and Compliance", "31%"],
        ["2. Implementation and Integration", "26%"],
        ["3. AI Safety, Security, and Governance", "20%"],
        ["4. Operational Efficiency and Optimization", "12%"],
        ["5. Testing, Validation, and Troubleshooting", "11%"],
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
        title="AWS Certified Generative AI Developer - Professional (AIP-C01) Study Guide",
        footer_label="AIP-C01 Study Guide",
    )

    flowables = []
    add_cover_page(flowables, styles, available_width)
    add_table_of_contents(flowables, styles)
    flowables.append(PageBreak())

    for idx, md_file in enumerate(MD_FILES):
        filepath = os.path.join(BASE_DIR, md_file)
        if not os.path.exists(filepath):
            print(f"WARNING: {filepath} not found, skipping.")
            continue

        print(f"Processing: {md_file}")

        with open(filepath, "r", encoding="utf-8") as f:
            md_text = f.read()

        if idx > 0:
            flowables.append(PageBreak())

        flowables.extend(parse_markdown_to_flowables(md_text, styles, available_width))

    print(f"\nBuilding PDF: {OUTPUT_FILE}")
    doc.multiBuild(flowables)
    print(f"Done. File size: {os.path.getsize(OUTPUT_FILE) / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    main()
