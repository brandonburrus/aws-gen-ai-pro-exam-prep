"""
Generate a single Study Guide PDF from the markdown files for the
AWS Certified Generative AI Developer - Professional (AIP-C01) exam.
"""

import re
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable,
    Preformatted,
)
from reportlab.platypus.tableofcontents import TableOfContents


# -- Configuration --

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

# Colors
PRIMARY = HexColor("#232F3E")  # AWS dark navy
SECONDARY = HexColor("#FF9900")  # AWS orange
ACCENT = HexColor("#0073BB")  # AWS blue
LIGHT_BG = HexColor("#F2F3F3")  # Light gray background
TABLE_HEADER_BG = HexColor("#232F3E")
TABLE_HEADER_FG = white
TABLE_ALT_ROW = HexColor("#F7F7F7")
EXAM_TIP_BG = HexColor("#FFF8E1")  # Light yellow
CODE_BG = HexColor("#F5F5F5")


def build_styles():
    """Create all paragraph styles for the PDF."""
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=34,
            textColor=PRIMARY,
            alignment=TA_CENTER,
            spaceAfter=12,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CoverSubtitle",
            fontName="Helvetica",
            fontSize=16,
            leading=20,
            textColor=ACCENT,
            alignment=TA_CENTER,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="H1",
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=26,
            textColor=PRIMARY,
            spaceBefore=24,
            spaceAfter=10,
        )
    )

    styles.add(
        ParagraphStyle(
            name="H2",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=21,
            textColor=PRIMARY,
            spaceBefore=18,
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="H3",
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=17,
            textColor=ACCENT,
            spaceBefore=14,
            spaceAfter=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="H4",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=PRIMARY,
            spaceBefore=10,
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BodyText2",
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=black,
            spaceBefore=2,
            spaceAfter=4,
            alignment=TA_JUSTIFY,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BulletItem",
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=black,
            spaceBefore=1,
            spaceAfter=1,
            leftIndent=18,
            bulletIndent=6,
            bulletFontName="Helvetica",
            bulletFontSize=9.5,
        )
    )

    styles.add(
        ParagraphStyle(
            name="BulletItemL2",
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=black,
            spaceBefore=1,
            spaceAfter=1,
            leftIndent=36,
            bulletIndent=24,
            bulletFontName="Helvetica",
            bulletFontSize=9.5,
        )
    )

    styles.add(
        ParagraphStyle(
            name="NumberedItem",
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=black,
            spaceBefore=1,
            spaceAfter=1,
            leftIndent=18,
            bulletIndent=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="ExamTip",
            fontName="Helvetica-Oblique",
            fontSize=9.5,
            leading=13.5,
            textColor=HexColor("#5D4037"),
            spaceBefore=6,
            spaceAfter=6,
            leftIndent=12,
            rightIndent=12,
            backColor=EXAM_TIP_BG,
            borderPadding=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="CodeBlock",
            fontName="Courier",
            fontSize=8,
            leading=11,
            textColor=HexColor("#333333"),
            spaceBefore=4,
            spaceAfter=4,
            leftIndent=12,
            backColor=CODE_BG,
            borderPadding=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TableCell",
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            textColor=black,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TableHeaderCell",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11.5,
            textColor=TABLE_HEADER_FG,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Footer",
            fontName="Helvetica",
            fontSize=7,
            leading=9,
            textColor=HexColor("#999999"),
            alignment=TA_CENTER,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TOCHeading",
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=26,
            textColor=PRIMARY,
            spaceBefore=12,
            spaceAfter=16,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TOCLevel0",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=16,
            leftIndent=0,
            textColor=PRIMARY,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TOCLevel1",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            leftIndent=18,
            textColor=black,
        )
    )

    return styles


class HeadingParagraph(Paragraph):
    """A Paragraph subclass that carries TOC metadata for afterFlowable detection."""

    def __init__(self, text, style, toc_level=None, toc_text=None, **kwargs):
        super().__init__(text, style, **kwargs)
        self._toc_level = toc_level
        self._toc_text = toc_text


class StudyGuideDocTemplate(BaseDocTemplate):
    """Custom DocTemplate that notifies the TOC when heading flowables are laid out."""

    def afterFlowable(self, flowable):
        if isinstance(flowable, HeadingParagraph) and flowable._toc_level is not None:
            level = flowable._toc_level
            text = flowable._toc_text or ""
            key = f"toc-h{level}-{self.page}-{id(flowable)}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level)
            self.notify("TOCEntry", (level, text, self.page, key))


def escape_xml(text):
    """Escape XML special characters for reportlab Paragraph."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def format_inline(text):
    """Convert markdown inline formatting to reportlab XML tags."""
    # Escape XML first
    text = escape_xml(text)

    # Bold + italic (***text*** or ___text___)
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", text)

    # Bold (**text** or __text__)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

    # Italic (*text* or _text_)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)

    # Inline code (`text`)
    text = re.sub(r"`([^`]+?)`", r'<font face="Courier" size="8.5">\1</font>', text)

    return text


def parse_table(lines):
    """Parse markdown table lines into a list of rows (each row is a list of cells)."""
    rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        # Skip separator rows
        if re.match(r"^\|[\s\-:|]+\|$", line):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        rows.append(cells)
    return rows


def build_table(rows, styles, available_width):
    """Build a reportlab Table from parsed markdown table rows."""
    if not rows or len(rows) < 1:
        return None

    num_cols = len(rows[0])
    if num_cols == 0:
        return None

    # Normalize rows to have the same number of columns
    for row in rows:
        while len(row) < num_cols:
            row.append("")

    # Build table data with Paragraphs
    table_data = []
    for i, row in enumerate(rows):
        if i == 0:
            styled_row = [
                Paragraph(format_inline(cell), styles["TableHeaderCell"])
                for cell in row
            ]
        else:
            styled_row = [
                Paragraph(format_inline(cell), styles["TableCell"]) for cell in row
            ]
        table_data.append(styled_row)

    # Calculate column widths
    col_width = available_width / num_cols
    col_widths = [col_width] * num_cols

    # For 2-column tables, give more space to the second column
    if num_cols == 2:
        col_widths = [available_width * 0.3, available_width * 0.7]
    elif num_cols == 3:
        col_widths = [
            available_width * 0.25,
            available_width * 0.35,
            available_width * 0.4,
        ]
    elif num_cols == 4:
        col_widths = [
            available_width * 0.2,
            available_width * 0.25,
            available_width * 0.25,
            available_width * 0.3,
        ]
    elif num_cols == 5:
        col_widths = [
            available_width * 0.15,
            available_width * 0.2,
            available_width * 0.2,
            available_width * 0.2,
            available_width * 0.25,
        ]
    elif num_cols == 6:
        col_widths = [available_width / 6] * 6
    elif num_cols == 7:
        col_widths = [available_width / 7] * 7

    # Build style commands
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), TABLE_HEADER_FG),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LEADING", (0, 0), (-1, -1), 11.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, TABLE_ALT_ROW]),
    ]

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle(style_cmds))
    return t


def parse_markdown_to_flowables(md_text, styles, available_width):
    """Convert markdown text to a list of reportlab flowables."""
    flowables = []
    lines = md_text.split("\n")
    i = 0
    in_code_block = False
    code_lines = []

    while i < len(lines):
        line = lines[i]

        # Code blocks
        if line.strip().startswith("```"):
            if in_code_block:
                # End code block
                code_text = "\n".join(code_lines)
                if code_text.strip():
                    # Use Preformatted to preserve whitespace
                    flowables.append(Spacer(1, 4))
                    pre = Preformatted(escape_xml(code_text), styles["CodeBlock"])
                    flowables.append(pre)
                    flowables.append(Spacer(1, 4))
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            i += 1
            continue

        # Horizontal rules
        if re.match(r"^---+$", stripped) or re.match(r"^\*\*\*+$", stripped):
            flowables.append(Spacer(1, 6))
            flowables.append(
                HRFlowable(
                    width="100%",
                    thickness=1,
                    color=HexColor("#CCCCCC"),
                    spaceBefore=4,
                    spaceAfter=4,
                )
            )
            i += 1
            continue

        # Headers
        if stripped.startswith("#"):
            match = re.match(r"^(#{1,4})\s+(.*)", stripped)
            if match:
                level = len(match.group(1))
                raw_header_text = match.group(2)
                header_text = format_inline(raw_header_text)
                style_name = f"H{level}"
                if style_name not in [s for s in styles.byName]:
                    style_name = "H4"

                # H1 and H2 go into the TOC and PDF bookmarks
                if level <= 2:
                    toc_level = level - 1  # TOC uses 0-indexed levels
                    # Strip markdown formatting for the TOC/bookmark text
                    plain_text = re.sub(r"[*_`]", "", raw_header_text)
                    flowables.append(
                        HeadingParagraph(
                            header_text,
                            styles[style_name],
                            toc_level=toc_level,
                            toc_text=plain_text,
                        )
                    )
                else:
                    flowables.append(Paragraph(header_text, styles[style_name]))
                i += 1
                continue

        # Exam tips (blockquotes starting with > **Exam tip:**)
        if stripped.startswith(">"):
            tip_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                tip_text = lines[i].strip().lstrip("> ").strip()
                tip_lines.append(tip_text)
                i += 1
            full_tip = " ".join(tip_lines)
            full_tip = format_inline(full_tip)
            flowables.append(Paragraph(full_tip, styles["ExamTip"]))
            continue

        # Tables
        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            rows = parse_table(table_lines)
            if rows:
                t = build_table(rows, styles, available_width)
                if t:
                    flowables.append(Spacer(1, 4))
                    flowables.append(t)
                    flowables.append(Spacer(1, 4))
            continue

        # Numbered list items
        num_match = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if num_match:
            num = num_match.group(1)
            text = format_inline(num_match.group(2))
            flowables.append(
                Paragraph(
                    f"{num}. {text}",
                    styles["NumberedItem"],
                )
            )
            i += 1
            continue

        # Sub-bullet items (indented - or *) -- check original line BEFORE stripping
        sub_bullet_match = re.match(r"^\s{2,}[-*]\s+(.*)", line)
        if sub_bullet_match:
            text = format_inline(sub_bullet_match.group(1))
            flowables.append(
                Paragraph(
                    text,
                    styles["BulletItemL2"],
                    bulletText="\u2013",
                )
            )
            i += 1
            continue

        # Bullet list items (- or *)
        bullet_match = re.match(r"^[-*]\s+(.*)", stripped)
        if bullet_match:
            text = format_inline(bullet_match.group(1))
            flowables.append(
                Paragraph(
                    text,
                    styles["BulletItem"],
                    bulletText="\u2022",
                )
            )
            i += 1
            continue

        # Regular paragraph -- accumulate consecutive lines
        para_lines = []
        while i < len(lines):
            l = lines[i].strip()
            if not l:
                break
            if l.startswith("#") or l.startswith("|") or l.startswith(">"):
                break
            if l.startswith("```"):
                break
            if re.match(r"^[-*]\s+", l):
                break
            if re.match(r"^\d+\.\s+", l):
                break
            if re.match(r"^---+$", l) or re.match(r"^\*\*\*+$", l):
                break
            para_lines.append(l)
            i += 1

        if para_lines:
            text = " ".join(para_lines)
            text = format_inline(text)
            flowables.append(Paragraph(text, styles["BodyText2"]))

    return flowables


def add_cover_page(flowables, styles):
    """Add a cover page to the PDF."""
    flowables.append(Spacer(1, 2 * inch))

    flowables.append(
        Paragraph(
            "AWS Certified Generative AI<br/>Developer - Professional",
            styles["CoverTitle"],
        )
    )
    flowables.append(Spacer(1, 8))
    flowables.append(
        Paragraph(
            "AIP-C01 Exam Study Guide",
            styles["CoverSubtitle"],
        )
    )
    flowables.append(Spacer(1, 0.5 * inch))

    flowables.append(
        HRFlowable(
            width="60%", thickness=2, color=SECONDARY, spaceBefore=0, spaceAfter=12
        )
    )

    flowables.append(
        Paragraph(
            "Comprehensive study material covering all five exam domains,<br/>"
            "the AWS Well-Architected Generative AI Lens,<br/>"
            "a ranked concept inventory,<br/>"
            "and key AWS services for GenAI development.",
            ParagraphStyle(
                name="CoverDesc",
                fontName="Helvetica",
                fontSize=11,
                leading=16,
                textColor=HexColor("#555555"),
                alignment=TA_CENTER,
            ),
        )
    )

    flowables.append(Spacer(1, 1 * inch))

    # Domain weights summary
    domain_data = [
        ["Domain", "Weight"],
        ["1. FM Integration, Data Management, and Compliance", "31%"],
        ["2. Implementation and Integration", "26%"],
        ["3. AI Safety, Security, and Governance", "20%"],
        ["4. Operational Efficiency and Optimization", "12%"],
        ["5. Testing, Validation, and Troubleshooting", "11%"],
    ]
    col_widths = [4.5 * inch, 1 * inch]
    t = Table(domain_data, colWidths=col_widths)
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


def add_table_of_contents(flowables, styles):
    """Add a Table of Contents page after the cover."""
    flowables.append(Paragraph("Table of Contents", styles["TOCHeading"]))

    toc = TableOfContents()
    toc.levelStyles = [
        styles["TOCLevel0"],
        styles["TOCLevel1"],
    ]
    toc.dotsMinLevel = 0
    flowables.append(toc)

    flowables.append(PageBreak())
    return toc


def footer_handler(canvas, doc):
    """Draw page number footer on each page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(HexColor("#999999"))
    page_num = canvas.getPageNumber()
    text = f"AIP-C01 Study Guide  |  Page {page_num}"
    canvas.drawCentredString(letter[0] / 2.0, 0.4 * inch, text)
    canvas.restoreState()


def main():
    styles = build_styles()

    # Page dimensions
    page_width, page_height = letter
    left_margin = 0.75 * inch
    right_margin = 0.75 * inch
    top_margin = 0.75 * inch
    bottom_margin = 0.75 * inch
    available_width = page_width - left_margin - right_margin

    # Build document using BaseDocTemplate for TOC support (requires multiBuild)
    frame = Frame(
        left_margin,
        bottom_margin,
        available_width,
        page_height - top_margin - bottom_margin,
        id="main_frame",
    )

    doc = StudyGuideDocTemplate(
        OUTPUT_FILE,
        pagesize=letter,
        title="AWS Certified Generative AI Developer - Professional (AIP-C01) Study Guide",
        author="Study Guide",
        subject="AIP-C01 Exam Preparation",
    )

    doc.addPageTemplates(
        PageTemplate(
            id="main",
            frames=[frame],
            onPage=footer_handler,
        )
    )

    flowables = []

    # Cover page
    add_cover_page(flowables, styles)

    # Table of Contents
    toc = add_table_of_contents(flowables, styles)

    # Process each markdown file
    for idx, md_file in enumerate(MD_FILES):
        filepath = os.path.join(BASE_DIR, md_file)
        if not os.path.exists(filepath):
            print(f"WARNING: {filepath} not found, skipping.")
            continue

        print(f"Processing: {md_file}")

        with open(filepath, "r", encoding="utf-8") as f:
            md_text = f.read()

        # Add a page break between sections (except before the first)
        if idx > 0:
            flowables.append(PageBreak())

        # Parse and add flowables
        section_flowables = parse_markdown_to_flowables(
            md_text, styles, available_width
        )
        flowables.extend(section_flowables)

    # Build the PDF (multiBuild resolves TOC page numbers in two passes)
    print(f"\nBuilding PDF: {OUTPUT_FILE}")
    doc.multiBuild(flowables)
    print(f"PDF created successfully: {OUTPUT_FILE}")

    # Print file size
    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f"File size: {size_mb:.2f} MB")


if __name__ == "__main__":
    main()
