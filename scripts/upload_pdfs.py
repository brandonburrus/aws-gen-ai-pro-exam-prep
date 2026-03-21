"""
Upload all PDFs in this repository to an S3 bucket as content-addressed files.

Each PDF is hashed with SHA-256 and uploaded to a flat S3 prefix as
`<prefix>/doc-<sha256>.pdf`. The source directory structure is not reflected
in the S3 key -- every file lands directly under the prefix.

Usage:
    AWS_PROFILE=my-profile python scripts/upload_pdfs.py <bucket> [--prefix <prefix>]
"""

import argparse
import glob
import hashlib
import os
import sys

import boto3


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_CHUNK_SIZE = 64 * 1024


def file_sha256(path: str) -> str:
    """Return the SHA-256 hex digest of the file at path, read in 64 KB chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while chunk := fh.read(_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def find_pdfs() -> list[str]:
    """Return a sorted list of absolute paths to every PDF file in the repository."""
    pattern = os.path.join(BASE_DIR, "**", "*.pdf")
    return sorted(glob.glob(pattern, recursive=True))


def upload_pdfs(bucket: str, prefix: str) -> None:
    """
    Hash and upload every PDF in the repository to S3 under a flat prefix.

    Args:
        bucket: Name of the destination S3 bucket.
        prefix: Key prefix prepended to each uploaded filename. When non-empty
                each object key is ``<prefix>/doc-<sha256>.pdf``.
    """
    profile = os.environ.get("AWS_PROFILE")
    if not profile:
        print("Error: AWS_PROFILE environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    session = boto3.Session(profile_name=profile)
    s3 = session.client("s3")

    pdfs = find_pdfs()
    if not pdfs:
        print("No PDF files found.")
        return

    dest = f"s3://{bucket}/{prefix}/" if prefix else f"s3://{bucket}/"
    print(f"Found {len(pdfs)} PDF(s). Uploading to {dest}...")

    for pdf_path in pdfs:
        rel_path = os.path.relpath(pdf_path, BASE_DIR)
        digest = file_sha256(pdf_path)
        filename = f"doc-{digest}.pdf"
        key = f"{prefix}/{filename}" if prefix else filename

        s3.upload_file(
            pdf_path,
            bucket,
            key,
            ExtraArgs={"ContentType": "application/pdf"},
        )
        print(f"  {rel_path} -> s3://{bucket}/{key}")

    print(f"\nDone. Uploaded {len(pdfs)} file(s).")


def parse_args() -> argparse.Namespace:
    """Parse and return CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Upload all PDFs in this repository to an S3 bucket as content-addressed files."
    )
    parser.add_argument("bucket", help="Destination S3 bucket name.")
    parser.add_argument(
        "--prefix",
        default="docs",
        help='S3 key prefix prepended to every uploaded filename (default: "docs").',
    )
    return parser.parse_args()


def main() -> None:
    """Entry point."""
    args = parse_args()
    upload_pdfs(args.bucket, args.prefix)


if __name__ == "__main__":
    main()
