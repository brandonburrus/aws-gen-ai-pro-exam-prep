"""
Test availability of every Anthropic Claude model accessible via Amazon Bedrock
by issuing a minimal InvokeModel request against each one.

Credentials are sourced from the AWS_PROFILE environment variable.

Usage:
    AWS_PROFILE=sandbox python scripts/test_anthropic_model_availability.py
    AWS_PROFILE=sandbox python scripts/test_anthropic_model_availability.py --region us-west-2
    AWS_PROFILE=sandbox python scripts/test_anthropic_model_availability.py --output report.json

Exit codes:
    0  All tested models responded successfully.
    1  One or more models failed or AWS_PROFILE is not set.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import boto3
import botocore.exceptions
from botocore.config import Config


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------

# Each entry is (display_name, model_id).
#
# Group A: models that carry single-region model IDs and can be invoked
# directly without a cross-region inference profile.
SINGLE_REGION_MODELS = [
    ("Claude 3 Haiku", "anthropic.claude-3-haiku-20240307-v1:0"),
    ("Claude 3.5 Haiku", "anthropic.claude-3-5-haiku-20241022-v1:0"),
]

# Group B: US cross-region inference profile IDs (prefix us.).  These are the
# recommended identifiers for all current-generation models and are the only
# way to reach several of the newer ones.
US_CROSS_REGION_MODELS = [
    ("Claude 3 Haiku", "us.anthropic.claude-3-haiku-20240307-v1:0"),
    ("Claude 3 Opus", "us.anthropic.claude-3-opus-20240229-v1:0"),
    ("Claude 3 Sonnet", "us.anthropic.claude-3-sonnet-20240229-v1:0"),
    ("Claude 3.5 Haiku", "us.anthropic.claude-3-5-haiku-20241022-v1:0"),
    ("Claude 3.5 Sonnet", "us.anthropic.claude-3-5-sonnet-20240620-v1:0"),
    ("Claude 3.5 Sonnet v2", "us.anthropic.claude-3-5-sonnet-20241022-v2:0"),
    ("Claude 3.7 Sonnet", "us.anthropic.claude-3-7-sonnet-20250219-v1:0"),
    ("Claude Sonnet 4", "us.anthropic.claude-sonnet-4-20250514-v1:0"),
    ("Claude Opus 4", "us.anthropic.claude-opus-4-20250514-v1:0"),
    ("Claude Opus 4.1", "us.anthropic.claude-opus-4-1-20250805-v1:0"),
    ("Claude Haiku 4.5", "us.anthropic.claude-haiku-4-5-20251001-v1:0"),
    ("Claude Sonnet 4.5", "us.anthropic.claude-sonnet-4-5-20250929-v1:0"),
    ("Claude Opus 4.5", "us.anthropic.claude-opus-4-5-20251101-v1:0"),
    ("Claude Sonnet 4.6", "us.anthropic.claude-sonnet-4-6"),
    ("Claude Opus 4.6", "us.anthropic.claude-opus-4-6-v1"),
]

# Minimal prompt used for every invocation.
_TEST_PROMPT = "Say hello in one short sentence."

# Maximum characters from the model response to display in the results table.
_RESPONSE_PREVIEW_LEN = 60


# ---------------------------------------------------------------------------
# ANSI helpers
# ---------------------------------------------------------------------------

_USE_COLOR = sys.stdout.isatty()


def _green(text: str) -> str:
    return f"\033[32m{text}\033[0m" if _USE_COLOR else text


def _red(text: str) -> str:
    return f"\033[31m{text}\033[0m" if _USE_COLOR else text


def _bold(text: str) -> str:
    return f"\033[1m{text}\033[0m" if _USE_COLOR else text


# ---------------------------------------------------------------------------
# Core invocation logic
# ---------------------------------------------------------------------------


def _build_request_body() -> bytes:
    """Return the serialised Anthropic Messages API payload for the test prompt."""
    payload = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 32,
        "messages": [
            {"role": "user", "content": _TEST_PROMPT},
        ],
    }
    return json.dumps(payload).encode("utf-8")


def test_model(client, model_id: str) -> tuple[bool, str]:
    """
    Invoke a single Bedrock model and return a (success, detail) pair.

    On success, detail contains a truncated preview of the model's response.
    On failure, detail contains the error code and message.

    Args:
        client: A boto3 bedrock-runtime client.
        model_id: The Bedrock model ID or cross-region inference profile ID.

    Returns:
        A tuple of (success: bool, detail: str).
    """
    try:
        response = client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=_build_request_body(),
        )
        body = json.loads(response["body"].read())
        # The Messages API always returns content as a list of blocks.
        text = body.get("content", [{}])[0].get("text", "").strip()
        preview = text[:_RESPONSE_PREVIEW_LEN].replace("\n", " ")
        if len(text) > _RESPONSE_PREVIEW_LEN:
            preview += "..."
        return True, f'"{preview}"'

    except botocore.exceptions.ClientError as exc:
        code = exc.response["Error"]["Code"]
        message = exc.response["Error"]["Message"]
        # Truncate verbose messages so the table stays readable.
        if len(message) > 120:
            message = message[:117] + "..."
        return False, f"{code}: {message}"

    except botocore.exceptions.NoCredentialsError as exc:
        return False, f"NoCredentialsError: {exc}"

    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _print_group(
    title: str,
    models: list[tuple[str, str]],
    results: list[tuple[str, str, bool, str]],
) -> tuple[int, int]:
    """
    Print one model group section and return (passed, total) counts.

    Args:
        title: Section heading.
        models: The (display_name, model_id) entries for this group.
        results: Accumulated (display_name, model_id, success, detail) tuples
                 produced by the test loop; this list is consumed in order.

    Returns:
        A (passed_count, total_count) tuple for the group.
    """
    print(f"\n{_bold(title)}")
    print("-" * len(title))

    passed = 0
    for display_name, model_id, success, detail in results:
        status = _green("[PASS]") if success else _red("[FAIL]")
        label = f"{display_name} ({model_id})"
        print(f"  {status}  {label:<70}  {detail}")
        if success:
            passed += 1

    return passed, len(results)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test availability of Anthropic Claude models on Amazon Bedrock.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--region",
        "-r",
        default="us-east-1",
        metavar="REGION",
        help="AWS region to target (default: us-east-1).",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        metavar="FILE",
        help="Write a JSON report to FILE after all tests complete.",
    )
    return parser.parse_args()


def _build_report(
    region: str,
    aws_profile: str,
    single_results: list[tuple[str, str, bool, str]],
    cross_results: list[tuple[str, str, bool, str]],
) -> dict:
    """
    Assemble a self-contained JSON-serialisable report from test results.

    Args:
        region: The AWS region used for the run.
        aws_profile: The AWS profile name used for the run.
        single_results: (display_name, model_id, success, detail) for single-region models.
        cross_results: (display_name, model_id, success, detail) for cross-region profiles.

    Returns:
        A dict ready for json.dumps.
    """

    def _serialise_group(results: list[tuple[str, str, bool, str]]) -> list[dict]:
        return [
            {
                "display_name": display_name,
                "model_id": model_id,
                "available": success,
                "detail": detail,
            }
            for display_name, model_id, success, detail in results
        ]

    all_results = single_results + cross_results
    total = len(all_results)
    available = sum(1 for _, _, success, _ in all_results if success)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "region": region,
        "aws_profile": aws_profile,
        "summary": {
            "total": total,
            "available": available,
            "unavailable": total - available,
        },
        "single_region_models": _serialise_group(single_results),
        "us_cross_region_profiles": _serialise_group(cross_results),
    }


def main() -> int:
    """
    Run availability checks against all registered Anthropic models.

    Returns:
        0 if every model responded successfully, 1 otherwise.
    """
    args = _parse_args()

    aws_profile = os.environ.get("AWS_PROFILE")
    if not aws_profile:
        print(
            "Error: AWS_PROFILE environment variable is not set.\n"
            "Example: AWS_PROFILE=sandbox python scripts/test_anthropic_model_availability.py",
            file=sys.stderr,
        )
        return 1

    print(_bold("Anthropic Model Availability Test"))
    print(f"  Region : {args.region}")
    print(f"  Profile: {aws_profile}")
    print()

    session = boto3.Session(profile_name=aws_profile, region_name=args.region)
    client = session.client(
        "bedrock-runtime",
        config=Config(
            # 60 s is generous for a tiny prompt but avoids hanging the terminal.
            read_timeout=60,
            # Disable SDK retries so every response (including throttles and
            # access-denied errors) is reported faithfully.
            retries={"max_attempts": 0},
        ),
    )

    def _run_group(models: list[tuple[str, str]]) -> list[tuple[str, str, bool, str]]:
        group_results = []
        for display_name, model_id in models:
            print(f"  Testing {display_name} ({model_id}) ...", end=" ", flush=True)
            success, detail = test_model(client, model_id)
            status_label = _green("ok") if success else _red("failed")
            print(status_label)
            group_results.append((display_name, model_id, success, detail))
        return group_results

    print("--- Single-Region Models ---")
    single_results = _run_group(SINGLE_REGION_MODELS)

    print("\n--- US Cross-Region Inference Profiles ---")
    cross_results = _run_group(US_CROSS_REGION_MODELS)

    # Print full results table.
    print("\n" + "=" * 80)
    print(_bold("Results"))
    print("=" * 80)

    single_passed, single_total = _print_group(
        "Single-Region Models", SINGLE_REGION_MODELS, single_results
    )
    cross_passed, cross_total = _print_group(
        "US Cross-Region Inference Profiles", US_CROSS_REGION_MODELS, cross_results
    )

    total_passed = single_passed + cross_passed
    total_models = single_total + cross_total

    print("\n" + "=" * 80)
    summary_color = _green if total_passed == total_models else _red
    print(
        _bold("Summary: ")
        + summary_color(f"{total_passed}/{total_models} models available")
        + f"  (region: {args.region}, profile: {aws_profile})"
    )
    print("=" * 80)

    if args.output:
        report = _build_report(args.region, aws_profile, single_results, cross_results)
        output_path = args.output
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
            fh.write("\n")
        print(f"\nReport written to {output_path}")

    return 0 if total_passed == total_models else 1


if __name__ == "__main__":
    sys.exit(main())
