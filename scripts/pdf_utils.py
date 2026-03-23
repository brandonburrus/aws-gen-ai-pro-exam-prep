"""
Shared PDF generation utilities for AIP-C01 study guide scripts.

Provides styles, markdown parsing, document construction, and common
flowable helpers used by all PDF generator scripts in this project.
"""

import re
import os

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    Preformatted,
)
from reportlab.platypus.tableofcontents import TableOfContents


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# AWS brand colors
PRIMARY = HexColor("#232F3E")
SECONDARY = HexColor("#FF9900")
ACCENT = HexColor("#0073BB")
LIGHT_BG = HexColor("#F2F3F3")
TABLE_HEADER_BG = HexColor("#232F3E")
TABLE_HEADER_FG = white
TABLE_ALT_ROW = HexColor("#F7F7F7")
EXAM_TIP_BG = HexColor("#FFF8E1")
CODE_BG = HexColor("#F5F5F5")


def build_styles():
    """Create all paragraph styles used across study guide PDFs."""
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
            name="CoverDesc",
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=HexColor("#555555"),
            alignment=TA_CENTER,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TierDividerTitle",
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=30,
            textColor=white,
            alignment=TA_CENTER,
            spaceAfter=10,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TierDividerSubtitle",
            fontName="Helvetica",
            fontSize=13,
            leading=18,
            textColor=HexColor("#DDDDDD"),
            alignment=TA_CENTER,
            spaceAfter=6,
        )
    )

    styles.add(
        ParagraphStyle(
            name="TierDividerBullet",
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor=white,
            leftIndent=24,
            bulletIndent=10,
            spaceAfter=3,
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
    """Paragraph subclass that carries TOC metadata for afterFlowable detection."""

    def __init__(self, text, style, toc_level=None, toc_text=None, **kwargs):
        super().__init__(text, style, **kwargs)
        self._toc_level = toc_level
        self._toc_text = toc_text


class StudyGuideDocTemplate(BaseDocTemplate):
    """DocTemplate that notifies the TOC widget when heading flowables are laid out."""

    def afterFlowable(self, flowable):
        if isinstance(flowable, HeadingParagraph) and flowable._toc_level is not None:
            level = flowable._toc_level
            text = flowable._toc_text or ""
            key = f"toc-h{level}-{self.page}-{id(flowable)}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level)
            self.notify("TOCEntry", (level, text, self.page, key))


def make_footer_handler(label: str):
    """Return a page footer callback that renders the given label with a page number."""

    def footer_handler(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(HexColor("#999999"))
        page_num = canvas.getPageNumber()
        canvas.drawCentredString(
            letter[0] / 2.0, 0.4 * inch, f"{label}  |  Page {page_num}"
        )
        canvas.restoreState()

    return footer_handler


def build_doc(
    output_path: str,
    title: str,
    footer_label: str,
    subject: str = "AIP-C01 Exam Preparation",
) -> tuple:
    """
    Create a configured StudyGuideDocTemplate with standard margins and a footer.

    Returns a (doc, available_width) tuple. The caller is responsible for
    adding page templates and calling multiBuild.
    """
    page_width, page_height = letter
    left_margin = 0.75 * inch
    right_margin = 0.75 * inch
    top_margin = 0.75 * inch
    bottom_margin = 0.75 * inch
    available_width = page_width - left_margin - right_margin

    frame = Frame(
        left_margin,
        bottom_margin,
        available_width,
        page_height - top_margin - bottom_margin,
        id="main_frame",
    )

    doc = StudyGuideDocTemplate(
        output_path,
        pagesize=letter,
        title=title,
        author="Study Guide",
        subject=subject,
    )

    doc.addPageTemplates(
        PageTemplate(
            id="main",
            frames=[frame],
            onPage=make_footer_handler(footer_label),
        )
    )

    return doc, available_width


def escape_xml(text: str) -> str:
    """Escape XML special characters for use inside reportlab Paragraph markup."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def format_inline(text: str) -> str:
    """Convert markdown inline formatting to reportlab XML tags.

    Inline code spans are extracted to placeholders before bold/italic
    substitution so that backtick content never interacts with asterisk
    patterns, preventing mismatched XML tag nesting in the output.
    """
    text = escape_xml(text)

    # Pull out inline code spans early so their content is not touched by
    # the bold/italic regexes, then restore them after.
    code_spans: list[str] = []

    def stash_code(m: re.Match) -> str:
        code_spans.append(m.group(1))
        return f"\x00CODE{len(code_spans) - 1}\x00"

    text = re.sub(r"`([^`]+?)`", stash_code, text)

    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<b><i>\1</i></b>", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)

    # The captured code content was already XML-escaped by the escape_xml call
    # at the top of this function, so restore it as-is without re-escaping.
    for idx, code in enumerate(code_spans):
        text = text.replace(
            f"\x00CODE{idx}\x00",
            f'<font face="Courier" size="8.5">{code}</font>',
        )

    return text


def parse_table(lines: list[str]) -> list[list[str]]:
    """Parse markdown table lines into a list of rows, skipping separator lines."""
    rows = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            continue
        if re.match(r"^\|[\s\-:|]+\|$", line):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        rows.append(cells)
    return rows


def build_table(rows: list[list[str]], styles, available_width: float):
    """Build a styled reportlab Table from parsed markdown table rows."""
    if not rows:
        return None

    num_cols = len(rows[0])
    if num_cols == 0:
        return None

    for row in rows:
        while len(row) < num_cols:
            row.append("")

    table_data = []
    for i, row in enumerate(rows):
        cell_style = styles["TableHeaderCell"] if i == 0 else styles["TableCell"]
        table_data.append([Paragraph(format_inline(cell), cell_style) for cell in row])

    col_widths = _column_widths(num_cols, available_width)

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


def _column_widths(num_cols: int, available_width: float) -> list[float]:
    """Return proportional column widths for common column counts."""
    presets = {
        2: [0.30, 0.70],
        3: [0.25, 0.35, 0.40],
        4: [0.20, 0.25, 0.25, 0.30],
        5: [0.15, 0.20, 0.20, 0.20, 0.25],
    }
    ratios = presets.get(num_cols, [1 / num_cols] * num_cols)
    return [available_width * r for r in ratios]


def parse_markdown_to_flowables(md_text: str, styles, available_width: float) -> list:
    """Convert a markdown string into a list of reportlab flowables."""
    flowables = []
    lines = md_text.split("\n")
    i = 0
    in_code_block = False
    code_lines: list[str] = []

    while i < len(lines):
        line = lines[i]

        if line.strip().startswith("```"):
            if in_code_block:
                code_text = "\n".join(code_lines)
                if code_text.strip():
                    flowables.append(Spacer(1, 4))
                    flowables.append(
                        Preformatted(escape_xml(code_text), styles["CodeBlock"])
                    )
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

        if not stripped:
            i += 1
            continue

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

        if stripped.startswith("#"):
            match = re.match(r"^(#{1,4})\s+(.*)", stripped)
            if match:
                level = len(match.group(1))
                raw_text = match.group(2)
                formatted = format_inline(raw_text)
                style_name = f"H{level}" if f"H{level}" in styles.byName else "H4"

                if level <= 2:
                    plain = re.sub(r"[*_`]", "", raw_text)
                    flowables.append(
                        HeadingParagraph(
                            formatted,
                            styles[style_name],
                            toc_level=level - 1,
                            toc_text=plain,
                        )
                    )
                else:
                    flowables.append(Paragraph(formatted, styles[style_name]))
            i += 1
            continue

        if stripped.startswith(">"):
            tip_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                tip_lines.append(lines[i].strip().lstrip("> ").strip())
                i += 1
            flowables.append(
                Paragraph(format_inline(" ".join(tip_lines)), styles["ExamTip"])
            )
            continue

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

        num_match = re.match(r"^(\d+)\.\s+(.*)", stripped)
        if num_match:
            flowables.append(
                Paragraph(
                    f"{num_match.group(1)}. {format_inline(num_match.group(2))}",
                    styles["NumberedItem"],
                )
            )
            i += 1
            continue

        sub_bullet_match = re.match(r"^\s{2,}[-*]\s+(.*)", line)
        if sub_bullet_match:
            flowables.append(
                Paragraph(
                    format_inline(sub_bullet_match.group(1)),
                    styles["BulletItemL2"],
                    bulletText="\u2013",
                )
            )
            i += 1
            continue

        bullet_match = re.match(r"^[-*]\s+(.*)", stripped)
        if bullet_match:
            flowables.append(
                Paragraph(
                    format_inline(bullet_match.group(1)),
                    styles["BulletItem"],
                    bulletText="\u2022",
                )
            )
            i += 1
            continue

        # Accumulate consecutive plain-text lines into a single paragraph.
        para_lines = []
        while i < len(lines):
            l = lines[i].strip()
            if not l:
                break
            if l.startswith(("#", "|", ">", "```")):
                break
            if re.match(r"^[-*]\s+", l) or re.match(r"^\d+\.\s+", l):
                break
            if re.match(r"^---+$", l) or re.match(r"^\*\*\*+$", l):
                break
            para_lines.append(l)
            i += 1

        if para_lines:
            flowables.append(
                Paragraph(format_inline(" ".join(para_lines)), styles["BodyText2"])
            )

    return flowables


def add_table_of_contents(flowables: list, styles) -> TableOfContents:
    """Append a TOC heading and widget to flowables. Returns the TOC object."""
    flowables.append(Paragraph("Table of Contents", styles["TOCHeading"]))
    toc = TableOfContents()
    toc.levelStyles = [styles["TOCLevel0"], styles["TOCLevel1"]]
    toc.dotsMinLevel = 0
    flowables.append(toc)
    return toc
