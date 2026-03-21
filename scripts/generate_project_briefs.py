"""
Generate a project-brief.pdf for each project in the projects/ directory.

Reads each project's README.md and renders it as a formatted PDF using
reportlab. Output is written to <project-dir>/project-brief.pdf alongside
the source README.
"""

import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    Preformatted,
    KeepTogether,
)

# Colors matching the existing study guide palette
PRIMARY = HexColor("#232F3E")  # AWS dark navy
SECONDARY = HexColor("#FF9900")  # AWS orange
ACCENT = HexColor("#0073BB")  # AWS blue
TABLE_HEADER_BG = HexColor("#232F3E")
TABLE_HEADER_FG = white
TABLE_ALT_ROW = HexColor("#F7F7F7")
CODE_BG = HexColor("#F5F5F5")
RULE_COLOR = HexColor("#CCCCCC")

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 0.75 * inch
AVAILABLE_WIDTH = PAGE_WIDTH - 2 * MARGIN


def build_styles():
    """Create paragraph styles for the project brief PDF."""
    base = getSampleStyleSheet()

    styles = {}

    styles["ProjectTitle"] = ParagraphStyle(
        name="ProjectTitle",
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=26,
        textColor=PRIMARY,
        spaceBefore=0,
        spaceAfter=8,
        alignment=TA_LEFT,
    )

    styles["H2"] = ParagraphStyle(
        name="H2",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=19,
        textColor=PRIMARY,
        spaceBefore=16,
        spaceAfter=6,
    )

    styles["H3"] = ParagraphStyle(
        name="H3",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=ACCENT,
        spaceBefore=12,
        spaceAfter=4,
    )

    styles["H4"] = ParagraphStyle(
        name="H4",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=PRIMARY,
        spaceBefore=8,
        spaceAfter=3,
    )

    styles["Body"] = ParagraphStyle(
        name="Body",
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=black,
        spaceBefore=2,
        spaceAfter=4,
        alignment=TA_JUSTIFY,
    )

    styles["BulletItem"] = ParagraphStyle(
        name="BulletItem",
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=black,
        spaceBefore=1,
        spaceAfter=1,
        leftIndent=18,
        bulletIndent=6,
    )

    styles["BulletItemL2"] = ParagraphStyle(
        name="BulletItemL2",
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=black,
        spaceBefore=1,
        spaceAfter=1,
        leftIndent=36,
        bulletIndent=24,
    )

    styles["NumberedItem"] = ParagraphStyle(
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

    styles["CodeBlock"] = ParagraphStyle(
        name="CodeBlock",
        fontName="Courier",
        fontSize=7.5,
        leading=10.5,
        textColor=HexColor("#333333"),
        spaceBefore=4,
        spaceAfter=4,
        leftIndent=8,
        backColor=CODE_BG,
        borderPadding=6,
    )

    styles["TableCell"] = ParagraphStyle(
        name="TableCell",
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=black,
    )

    styles["TableHeaderCell"] = ParagraphStyle(
        name="TableHeaderCell",
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=TABLE_HEADER_FG,
    )

    styles["Footer"] = ParagraphStyle(
        name="Footer",
        fontName="Helvetica",
        fontSize=7,
        leading=9,
        textColor=HexColor("#999999"),
        alignment=TA_CENTER,
    )

    return styles


def escape_xml(text):
    """Escape XML special characters for use in reportlab Paragraph markup."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def format_inline(text):
    """Convert markdown inline formatting to reportlab XML markup tags."""
    text = escape_xml(text)
    # Bold + italic
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", text)
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    # Inline code
    text = re.sub(r"`([^`]+?)`", r'<font face="Courier" size="8">\1</font>', text)
    # Strip markdown link syntax, keeping the display text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text


def parse_table(lines):
    """Parse a sequence of markdown pipe-table lines into a list of cell-rows."""
    rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        # Skip the header/body separator row (e.g. |---|---|)
        if re.match(r"^\|[\s\-:|]+\|$", line):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        rows.append(cells)
    return rows


def build_table_flowable(rows, styles):
    """Convert parsed markdown table rows into a styled reportlab Table."""
    if not rows:
        return None

    num_cols = max(len(r) for r in rows)
    if num_cols == 0:
        return None

    # Pad any short rows
    for row in rows:
        while len(row) < num_cols:
            row.append("")

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

    # Proportional column widths by number of columns
    w = AVAILABLE_WIDTH
    col_widths_map = {
        1: [w],
        2: [w * 0.30, w * 0.70],
        3: [w * 0.20, w * 0.30, w * 0.50],
        4: [w * 0.18, w * 0.22, w * 0.25, w * 0.35],
        5: [w * 0.15, w * 0.18, w * 0.20, w * 0.22, w * 0.25],
    }
    col_widths = col_widths_map.get(num_cols, [w / num_cols] * num_cols)

    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), TABLE_HEADER_FG),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("LEADING", (0, 0), (-1, -1), 12),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, RULE_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, TABLE_ALT_ROW]),
    ]

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle(style_cmds))
    return t


def parse_markdown_to_flowables(md_text, styles):
    """
    Convert a README.md string to an ordered list of reportlab flowables.

    Handles: headings (H1-H4), fenced code blocks, pipe tables, unordered
    and ordered lists (including indented sub-bullets and checkbox items),
    blockquotes, horizontal rules, and plain body paragraphs.
    """
    flowables = []
    lines = md_text.split("\n")
    i = 0
    in_code_block = False
    code_lines = []

    while i < len(lines):
        line = lines[i]

        # Fenced code block handling
        if line.strip().startswith("```"):
            if in_code_block:
                code_text = "\n".join(code_lines)
                if code_text.strip():
                    flowables.append(Spacer(1, 3))
                    flowables.append(
                        Preformatted(escape_xml(code_text), styles["CodeBlock"])
                    )
                    flowables.append(Spacer(1, 3))
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

        if not stripped:
            i += 1
            continue

        # Horizontal rules
        if re.match(r"^---+$", stripped) or re.match(r"^\*\*\*+$", stripped):
            flowables.append(
                HRFlowable(
                    width="100%",
                    thickness=0.5,
                    color=RULE_COLOR,
                    spaceBefore=6,
                    spaceAfter=6,
                )
            )
            i += 1
            continue

        # Headings
        if stripped.startswith("#"):
            match = re.match(r"^(#{1,4})\s+(.*)", stripped)
            if match:
                level = len(match.group(1))
                header_text = format_inline(match.group(2))
                if level == 1:
                    flowables.append(Paragraph(header_text, styles["ProjectTitle"]))
                    flowables.append(
                        HRFlowable(
                            width="100%",
                            thickness=2,
                            color=SECONDARY,
                            spaceBefore=2,
                            spaceAfter=10,
                        )
                    )
                elif level == 2:
                    flowables.append(Paragraph(header_text, styles["H2"]))
                elif level == 3:
                    flowables.append(Paragraph(header_text, styles["H3"]))
                else:
                    flowables.append(Paragraph(header_text, styles["H4"]))
            i += 1
            continue

        # Blockquotes
        if stripped.startswith(">"):
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_text = lines[i].strip().lstrip("> ").strip()
                quote_lines.append(quote_text)
                i += 1
            full_quote = " ".join(quote_lines)
            flowables.append(Paragraph(format_inline(full_quote), styles["Body"]))
            continue

        # Pipe tables
        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            rows = parse_table(table_lines)
            t = build_table_flowable(rows, styles)
            if t:
                flowables.append(Spacer(1, 4))
                flowables.append(t)
                flowables.append(Spacer(1, 6))
            continue

        # Ordered list items
        num_match = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if num_match:
            num = num_match.group(1)
            text = format_inline(num_match.group(2))
            # Accumulate continuation lines (indented, non-list, non-blank)
            i += 1
            while i < len(lines):
                cont = lines[i]
                cont_stripped = cont.strip()
                if not cont_stripped:
                    break
                if re.match(r"^(\d+)\.\s+", cont_stripped):
                    break
                if re.match(r"^[-*]\s+", cont_stripped):
                    break
                if cont_stripped.startswith("#") or cont_stripped.startswith("|"):
                    break
                if cont_stripped.startswith("```"):
                    break
                text += " " + format_inline(cont_stripped)
                i += 1
            flowables.append(Paragraph(f"{num}. {text}", styles["NumberedItem"]))
            continue

        # Sub-bullet items (2+ spaces of indent before - or *)
        sub_match = re.match(r"^\s{2,}[-*]\s+(.*)", line)
        if sub_match:
            text = format_inline(sub_match.group(1))
            flowables.append(
                Paragraph(text, styles["BulletItemL2"], bulletText="\u2013")
            )
            i += 1
            continue

        # Top-level bullet items (- or *)
        bullet_match = re.match(r"^[-*]\s+(.*)", stripped)
        if bullet_match:
            raw = bullet_match.group(1)
            # Render checkbox items with a prefix indicator
            if raw.startswith("[ ]"):
                raw = "[ ] " + raw[3:].strip()
            elif raw.startswith("[x]") or raw.startswith("[X]"):
                raw = "[x] " + raw[3:].strip()
            text = format_inline(raw)
            flowables.append(Paragraph(text, styles["BulletItem"], bulletText="\u2022"))
            i += 1
            continue

        # Plain body paragraph -- accumulate consecutive non-structural lines
        para_lines = []
        while i < len(lines):
            l = lines[i]
            ls = l.strip()
            if not ls:
                break
            if ls.startswith("#") or ls.startswith("|") or ls.startswith(">"):
                break
            if ls.startswith("```"):
                break
            if re.match(r"^[-*]\s+", ls):
                break
            if re.match(r"^\d+\.\s+", ls):
                break
            if re.match(r"^---+$", ls) or re.match(r"^\*\*\*+$", ls):
                break
            para_lines.append(ls)
            i += 1

        if para_lines:
            text = " ".join(para_lines)
            flowables.append(Paragraph(format_inline(text), styles["Body"]))

    return flowables


def footer_handler(canvas, doc):
    """Draw a centered page-number footer on every page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(HexColor("#999999"))
    page_num = canvas.getPageNumber()
    # Extract a short project label from the output path
    label = os.path.basename(os.path.dirname(doc.filename))
    canvas.drawCentredString(
        PAGE_WIDTH / 2.0,
        0.4 * inch,
        f"Project Brief  |  {label}  |  Page {page_num}",
    )
    canvas.restoreState()


def generate_brief(readme_path, output_path):
    """
    Read a single README.md and write a project-brief.pdf to output_path.

    Args:
        readme_path: Absolute path to the source README.md file.
        output_path: Absolute path where the PDF will be written.
    """
    with open(readme_path, "r", encoding="utf-8") as fh:
        md_text = fh.read()

    styles = build_styles()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=0.75 * inch,
        title=os.path.basename(os.path.dirname(readme_path)),
        author="AWS GenAI Pro Exam Prep",
        subject="Project Brief",
    )

    flowables = parse_markdown_to_flowables(md_text, styles)
    doc.build(flowables, onFirstPage=footer_handler, onLaterPages=footer_handler)


def main():
    """Discover all project directories and generate a project-brief.pdf for each."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    projects_dir = os.path.join(base_dir, "projects")

    if not os.path.isdir(projects_dir):
        print(f"ERROR: projects/ directory not found at {projects_dir}")
        return

    project_dirs = sorted(
        entry.path for entry in os.scandir(projects_dir) if entry.is_dir()
    )

    if not project_dirs:
        print("No project directories found.")
        return

    print(f"Found {len(project_dirs)} project(s). Generating PDFs...\n")

    results = []
    for project_dir in project_dirs:
        readme_path = os.path.join(project_dir, "README.md")
        output_path = os.path.join(project_dir, "project-brief.pdf")
        project_name = os.path.basename(project_dir)

        if not os.path.exists(readme_path):
            print(f"  SKIP  {project_name}  (no README.md found)")
            continue

        try:
            generate_brief(readme_path, output_path)
            size_kb = os.path.getsize(output_path) / 1024
            print(f"  OK    {project_name}/project-brief.pdf  ({size_kb:.1f} KB)")
            results.append((project_name, output_path, size_kb))
        except Exception as exc:
            print(f"  FAIL  {project_name}  -- {exc}")
            raise

    print(f"\nDone. Generated {len(results)} PDF(s).")


if __name__ == "__main__":
    main()
