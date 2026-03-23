"""
Generate a single PDF from all service-specific study guides for the
AWS Certified Generative AI Developer - Professional (AIP-C01) exam.

Guides are ordered by exam relevance across four tiers:
  Tier 1 - Core GenAI Services       (appear in nearly every domain)
  Tier 2 - High-Frequency Services   (referenced 5+ times across domains)
  Tier 3 - Important Infrastructure  (referenced 3-5 times)
  Tier 4 - Supporting Services       (referenced 1-2 times)
"""

import os
import itertools

from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, white
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
    FrameBreak,
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


SERVICES_DIR = os.path.join(BASE_DIR, "services")
OUTPUT_FILE = os.path.join(BASE_DIR, "AIP-C01-Service-Study-Guides.pdf")

# Each entry: (filename, display_name, tier_label)
# Order within each tier reflects relative frequency of exam task references.
SERVICE_GUIDES: list[tuple[str, str, str]] = [
    # Tier 1: Core GenAI Services
    # Bedrock and its sub-services dominate the exam. Every domain references
    # these services. Master these first.
    ("AMAZON-BEDROCK-STUDY-GUIDE.md", "Amazon Bedrock", "Tier 1: Core GenAI Services"),
    (
        "BEDROCK-KNOWLEDGE-BASES-STUDY-GUIDE.md",
        "Bedrock Knowledge Bases & RAG",
        "Tier 1: Core GenAI Services",
    ),
    (
        "PROMPT-MGMT-FLOWS-AGENTIC-AI-STUDY-GUIDE.md",
        "Agents, Prompt Management & Flows",
        "Tier 1: Core GenAI Services",
    ),
    # Tier 2: High-Frequency Supporting Services
    # Each is cited 5 or more times across the five exam domains.
    # Expect multiple questions requiring deep knowledge of each.
    (
        "SAGEMAKER-STUDY-GUIDE.md",
        "Amazon SageMaker AI Ecosystem",
        "Tier 2: High-Frequency Services",
    ),
    (
        "AI-ML-SERVICES-STUDY-GUIDE.md",
        "AI/ML Services (Comprehend, Kendra, Q, Titan, Transcribe, and more)",
        "Tier 2: High-Frequency Services",
    ),
    (
        "APPLICATION-INTEGRATION-STUDY-GUIDE.md",
        "Application Integration (Step Functions, EventBridge, SQS, SNS, AppConfig)",
        "Tier 2: High-Frequency Services",
    ),
    (
        "COMPUTE-SERVICES-STUDY-GUIDE.md",
        "Compute Services (Lambda, EC2, App Runner, Outposts, Wavelength)",
        "Tier 2: High-Frequency Services",
    ),
    # Tier 3: Important Infrastructure
    # Referenced 3-5 times. Expect 1-2 questions per service group.
    (
        "MANAGEMENT-GOVERNANCE-STUDY-GUIDE.md",
        "Management & Governance (CloudWatch, CloudTrail, Cost Tools, Well-Architected)",
        "Tier 3: Important Infrastructure",
    ),
    (
        "SECURITY-IDENTITY-COMPLIANCE-STUDY-GUIDE.md",
        "Security, Identity & Compliance (IAM, Cognito, KMS, WAF, Macie)",
        "Tier 3: Important Infrastructure",
    ),
    (
        "NETWORKING-CONTENT-DELIVERY-STUDY-GUIDE.md",
        "Networking & Content Delivery (API Gateway, VPC, CloudFront, AppSync)",
        "Tier 3: Important Infrastructure",
    ),
    (
        "ANALYTICS-SERVICES-STUDY-GUIDE.md",
        "Analytics Services (OpenSearch, Glue, Athena, Kinesis, MSK)",
        "Tier 3: Important Infrastructure",
    ),
    (
        "DATABASE-SERVICES-STUDY-GUIDE.md",
        "Database Services (Aurora pgvector, DynamoDB, ElastiCache, Neptune)",
        "Tier 3: Important Infrastructure",
    ),
    # Tier 4: Supporting Services
    # Referenced 1-2 times. Know when to use them and how they differ from alternatives.
    (
        "DEVELOPER-TOOLS-STUDY-GUIDE.md",
        "Developer Tools (X-Ray, Amplify, CDK, CI/CD, SDKs)",
        "Tier 4: Supporting Services",
    ),
    (
        "CONTAINER-SERVICES-STUDY-GUIDE.md",
        "Container Services (ECS, EKS, Fargate, ECR)",
        "Tier 4: Supporting Services",
    ),
    (
        "STORAGE-AND-MIGRATION-STUDY-GUIDE.md",
        "Storage & Migration (S3, EBS, EFS, DataSync)",
        "Tier 4: Supporting Services",
    ),
    ("AMAZON-CONNECT-STUDY-GUIDE.md", "Amazon Connect", "Tier 4: Supporting Services"),
]

TIER_DESCRIPTIONS = {
    "Tier 1: Core GenAI Services": (
        "These services appear in virtually every exam domain and task statement. "
        "Amazon Bedrock alone accounts for the majority of exam questions. "
        "Expect deep integration knowledge, API-level details, and architectural patterns."
    ),
    "Tier 2: High-Frequency Services": (
        "Each service group is cited five or more times across the five exam domains. "
        "Expect multiple questions requiring solid knowledge of configuration, "
        "integration patterns, and when to use each service over its alternatives."
    ),
    "Tier 3: Important Infrastructure": (
        "These services are referenced three to five times across domains. "
        "Focus on how they integrate with Bedrock and SageMaker, key configuration "
        "options, and the scenarios that distinguish them from similar services."
    ),
    "Tier 4: Supporting Services": (
        "Referenced once or twice. Know their primary purpose, the specific GenAI "
        "scenario each addresses, and the key decision criteria for choosing them "
        "over alternatives."
    ),
}

TIER_COLORS = {
    "Tier 1: Core GenAI Services": HexColor("#1A2A3A"),
    "Tier 2: High-Frequency Services": HexColor("#0D4F8B"),
    "Tier 3: Important Infrastructure": HexColor("#1A6B3C"),
    "Tier 4: Supporting Services": HexColor("#5D4037"),
}


def add_cover_page(flowables, styles, available_width):
    flowables.append(Spacer(1, 1.75 * inch))

    flowables.append(
        Paragraph(
            "AWS Certified Generative AI<br/>Developer - Professional",
            styles["CoverTitle"],
        )
    )
    flowables.append(Spacer(1, 8))
    flowables.append(Paragraph("AIP-C01 Service Study Guides", styles["CoverSubtitle"]))
    flowables.append(Spacer(1, 0.4 * inch))

    flowables.append(
        HRFlowable(
            width="60%",
            thickness=2,
            color=SECONDARY,
            spaceBefore=0,
            spaceAfter=14,
        )
    )

    flowables.append(
        Paragraph(
            "Comprehensive service-by-service study material covering all 80+<br/>"
            "in-scope AWS services from Appendix B of the exam guide,<br/>"
            "ordered by exam relevance across four tiers.",
            styles["CoverDesc"],
        )
    )

    flowables.append(Spacer(1, 0.75 * inch))

    tier_data = [
        ["Tier", "Exam Relevance", "Key Services"],
        [
            "Tier 1",
            "Core GenAI\n(Most tested)",
            "Amazon Bedrock, Knowledge Bases, Agents,\nPrompt Management, Prompt Flows",
        ],
        [
            "Tier 2",
            "High-Frequency\n(5+ references)",
            "SageMaker, Comprehend, Kendra, Q Business,\nStep Functions, Lambda, Titan",
        ],
        [
            "Tier 3",
            "Important\n(3-5 references)",
            "CloudWatch, IAM, API Gateway, OpenSearch,\nDynamoDB, S3, KMS",
        ],
        [
            "Tier 4",
            "Supporting\n(1-2 references)",
            "X-Ray, Amplify, ECS, EKS, DataSync,\nAmazon Connect",
        ],
    ]

    col_widths = [available_width * r for r in [0.12, 0.22, 0.66]]
    t = Table(tier_data, colWidths=col_widths)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TABLE_HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), TABLE_HEADER_FG),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("LEADING", (0, 0), (-1, -1), 13),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#CCCCCC")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#F7F7F7")]),
                # Tier color accents in the first column
                ("BACKGROUND", (0, 1), (0, 1), HexColor("#1A2A3A")),
                ("TEXTCOLOR", (0, 1), (0, 1), white),
                ("BACKGROUND", (0, 2), (0, 2), HexColor("#0D4F8B")),
                ("TEXTCOLOR", (0, 2), (0, 2), white),
                ("BACKGROUND", (0, 3), (0, 3), HexColor("#1A6B3C")),
                ("TEXTCOLOR", (0, 3), (0, 3), white),
                ("BACKGROUND", (0, 4), (0, 4), HexColor("#5D4037")),
                ("TEXTCOLOR", (0, 4), (0, 4), white),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ]
        )
    )
    flowables.append(t)
    flowables.append(PageBreak())


def add_tier_divider(flowables, styles, available_width, tier_label, guide_entries):
    """Insert a full-page tier divider between tier groups."""
    flowables.append(PageBreak())

    bg_color = TIER_COLORS.get(tier_label, PRIMARY)
    description = TIER_DESCRIPTIONS.get(tier_label, "")

    # Full-width colored banner as a single-cell table
    banner_data = [[Paragraph(tier_label, styles["TierDividerTitle"])]]
    banner = Table(banner_data, colWidths=[available_width])
    banner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg_color),
                ("TOPPADDING", (0, 0), (-1, -1), 28),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 28),
                ("LEFTPADDING", (0, 0), (-1, -1), 18),
                ("RIGHTPADDING", (0, 0), (-1, -1), 18),
            ]
        )
    )
    flowables.append(banner)

    flowables.append(Spacer(1, 18))

    flowables.append(Paragraph(description, styles["BodyText2"]))

    flowables.append(Spacer(1, 18))

    flowables.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=HexColor("#CCCCCC"),
            spaceBefore=4,
            spaceAfter=12,
        )
    )

    flowables.append(Paragraph("Guides in this tier:", styles["H3"]))
    flowables.append(Spacer(1, 6))

    for _, display_name, _ in guide_entries:
        flowables.append(
            Paragraph(
                display_name,
                styles["BulletItem"],
                bulletText="\u2022",
            )
        )

    flowables.append(PageBreak())


def main():
    styles = build_styles()
    doc, available_width = build_doc(
        OUTPUT_FILE,
        title="AWS Certified Generative AI Developer - Professional (AIP-C01) Service Study Guides",
        footer_label="AIP-C01 Service Study Guides",
    )

    flowables = []

    add_cover_page(flowables, styles, available_width)
    add_table_of_contents(flowables, styles)
    flowables.append(PageBreak())

    # Group consecutive entries by tier while preserving order.
    grouped = itertools.groupby(SERVICE_GUIDES, key=lambda entry: entry[2])

    for tier_label, tier_iter in grouped:
        tier_entries = list(tier_iter)

        add_tier_divider(flowables, styles, available_width, tier_label, tier_entries)

        for guide_idx, (filename, display_name, _) in enumerate(tier_entries):
            filepath = os.path.join(SERVICES_DIR, filename)
            if not os.path.exists(filepath):
                print(f"WARNING: {filepath} not found, skipping.")
                continue

            print(f"Processing [{tier_label}]: {display_name}")

            with open(filepath, "r", encoding="utf-8") as f:
                md_text = f.read()

            if guide_idx > 0:
                flowables.append(PageBreak())

            flowables.extend(
                parse_markdown_to_flowables(md_text, styles, available_width)
            )

    print(f"\nBuilding PDF: {OUTPUT_FILE}")
    doc.multiBuild(flowables)
    print(f"Done. File size: {os.path.getsize(OUTPUT_FILE) / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    main()
