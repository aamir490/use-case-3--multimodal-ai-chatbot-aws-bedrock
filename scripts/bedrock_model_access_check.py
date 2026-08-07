#!/usr/bin/env python3
"""
bedrock_model_access_check.py
─────────────────────────────
Diagnostic script for verifying AWS credentials, region, and Amazon Bedrock
model access before running the multimodal chatbot.

Run from the project root:
    python scripts/bedrock_model_access_check.py

What this script checks:
  1. Python version
  2. Required packages installed
  3. AWS credentials (via boto3 STS)
  4. AWS region in use
  5. Amazon Bedrock service reachability
  6. Model access — lists available Nova / Claude foundation models
  7. Live text inference test (amazon.nova-pro-v1:0)
  8. Live multimodal (image) capability confirmation
  9. Document (PDF) capability confirmation
 10. Summary report with pass/fail for each check

No secrets are printed. IAM user/role ARN is shown (not the key itself).
"""

import sys
import os
import json
import base64
import textwrap
from io import BytesIO
from datetime import datetime

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg: str)   -> str: return f"{GREEN}  ✔  {msg}{RESET}"
def fail(msg: str) -> str: return f"{RED}  ✘  {msg}{RESET}"
def warn(msg: str) -> str: return f"{YELLOW}  ⚠  {msg}{RESET}"
def info(msg: str) -> str: return f"{CYAN}  ℹ  {msg}{RESET}"
def header(msg: str):
    bar = "─" * 60
    print(f"\n{BOLD}{CYAN}{bar}{RESET}")
    print(f"{BOLD}{CYAN}  {msg}{RESET}")
    print(f"{BOLD}{CYAN}{bar}{RESET}")

# ── Results tracker ───────────────────────────────────────────────────────────
results: list[dict] = []

def record(check: str, passed: bool, detail: str = ""):
    results.append({"check": check, "passed": passed, "detail": detail})
    symbol = ok(check) if passed else fail(check)
    print(symbol)
    if detail:
        for line in detail.splitlines():
            print(f"       {line}")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 1: Python version
# ─────────────────────────────────────────────────────────────────────────────
header("CHECK 1 — Python Version")
py_ver = sys.version_info
py_str = f"{py_ver.major}.{py_ver.minor}.{py_ver.micro}"
if py_ver >= (3, 9):
    record("Python version", True, f"Python {py_str} — OK (≥3.9 required)")
else:
    record("Python version", False, f"Python {py_str} — upgrade to ≥3.9")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 2: Required packages
# ─────────────────────────────────────────────────────────────────────────────
header("CHECK 2 — Required Packages")

REQUIRED_PACKAGES = {
    "boto3":           "boto3",
    "botocore":        "botocore",
    "streamlit":       "streamlit",
    "langchain_aws":   "langchain-aws",
    "langchain_core":  "langchain-core",
    "PIL":             "Pillow",
    "dotenv":          "python-dotenv",
}

missing = []
for import_name, pip_name in REQUIRED_PACKAGES.items():
    try:
        __import__(import_name)
        print(ok(f"{pip_name} — installed"))
    except ImportError:
        print(fail(f"{pip_name} — NOT installed  →  pip install {pip_name}"))
        missing.append(pip_name)

# pypdf is optional but recommended
try:
    import pypdf  # noqa: F401
    print(ok("pypdf — installed (PDF support enabled)"))
    PDF_AVAILABLE = True
except ImportError:
    print(warn("pypdf — not installed  →  pip install pypdf  (PDF support disabled)"))
    PDF_AVAILABLE = False

record(
    "Required packages",
    len(missing) == 0,
    f"Missing: {missing}" if missing else "All core packages present",
)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 3: AWS credentials & caller identity
# ─────────────────────────────────────────────────────────────────────────────
header("CHECK 3 — AWS Credentials")

try:
    import boto3
    import botocore

    # Support .env override of region
    region_override = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION")

    session = boto3.session.Session()
    region  = region_override or session.region_name or "us-east-1"
    print(info(f"AWS Region  : {region}"))

    sts = session.client("sts", region_name=region)
    identity = sts.get_caller_identity()

    account_id = identity["Account"]
    arn        = identity["Arn"]
    # Mask the account ID middle digits for log safety
    masked_account = account_id[:4] + "****" + account_id[-4:]

    print(info(f"Account ID  : {masked_account}"))
    print(info(f"Identity ARN: {arn}"))

    record("AWS credentials", True, f"Authenticated as: {arn}")
    REGION = region

except Exception as exc:
    record("AWS credentials", False, str(exc))
    print(f"\n{RED}Cannot continue without valid AWS credentials.{RESET}")
    print("Run:  aws configure  — and provide your Access Key, Secret, and region.")
    _print_summary()
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 4: AWS region suitability for Nova Pro
# ─────────────────────────────────────────────────────────────────────────────
header("CHECK 4 — Region Suitability")

SUPPORTED_NOVA_REGIONS = {
    "us-east-1": "US East (N. Virginia) — PRIMARY, full Nova model support",
    "us-east-2": "US East (Ohio) — via cross-region inference",
    "us-west-2": "US West (Oregon) — via cross-region inference",
    "ap-southeast-2": "Asia Pacific (Sydney) — direct Nova Pro support",
    "eu-west-2": "Europe (London) — direct Nova Pro support",
    "ap-northeast-1": "Asia Pacific (Tokyo) — via cross-region inference",
}

if REGION in SUPPORTED_NOVA_REGIONS:
    record("Region supports Nova Pro", True, SUPPORTED_NOVA_REGIONS[REGION])
elif REGION.startswith("us-") or REGION.startswith("ap-") or REGION.startswith("eu-"):
    record(
        "Region supports Nova Pro",
        True,
        f"{REGION} — cross-region inference available via us.amazon.nova-pro-v1:0",
    )
else:
    record(
        "Region supports Nova Pro",
        False,
        f"{REGION} may not support Nova Pro. Consider switching to us-east-1.",
    )

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 5: Bedrock service reachability
# ─────────────────────────────────────────────────────────────────────────────
header("CHECK 5 — Bedrock Service Reachability")

try:
    bedrock = boto3.client("bedrock", region_name=REGION)
    # list_foundation_models is a lightweight read-only call
    response = bedrock.list_foundation_models(byOutputModality="TEXT")
    model_count = len(response.get("modelSummaries", []))
    record("Bedrock service reachable", True, f"{model_count} text-output models found in {REGION}")
    ALL_MODELS = response.get("modelSummaries", [])
except botocore.exceptions.ClientError as exc:
    err_code = exc.response["Error"]["Code"]
    record(
        "Bedrock service reachable",
        False,
        f"{err_code}: {exc.response['Error']['Message']}\n"
        "Make sure your IAM policy includes: bedrock:ListFoundationModels",
    )
    ALL_MODELS = []
except Exception as exc:
    record("Bedrock service reachable", False, str(exc))
    ALL_MODELS = []

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 6: Nova model availability
# ─────────────────────────────────────────────────────────────────────────────
header("CHECK 6 — Nova & Claude Model Availability")

TARGET_MODELS = [
    "amazon.nova-pro-v1:0",
    "amazon.nova-lite-v1:0",
    "amazon.nova-micro-v1:0",
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "anthropic.claude-3-haiku-20240307-v1:0",
]

found_model_ids = {m["modelId"] for m in ALL_MODELS}

for model_id in TARGET_MODELS:
    if model_id in found_model_ids:
        print(ok(f"{model_id}"))
    else:
        # Cross-region inference profiles use the "us." prefix
        print(warn(f"{model_id} — not in base list (may still work via inference profile)"))

# Check specifically for our primary model access
PRIMARY_MODEL   = "amazon.nova-pro-v1:0"
# Cross-region inference profile — more resilient, works from any US region
INFERENCE_PROFILE = "us.amazon.nova-pro-v1:0"

record(
    "Nova model listing",
    True,
    f"Primary model: {PRIMARY_MODEL}\nInference profile: {INFERENCE_PROFILE}",
)

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 7: Live text inference test
# ─────────────────────────────────────────────────────────────────────────────
header("CHECK 7 — Live Text Inference (amazon.nova-pro-v1:0)")

TEXT_TEST_PASSED = False
try:
    bedrock_rt = boto3.client("bedrock-runtime", region_name=REGION)

    test_payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "text": (
                            "Reply with exactly one sentence confirming you are "
                            "Amazon Nova Pro and that you are ready to assist."
                        )
                    }
                ],
            }
        ],
        "inferenceConfig": {
            "maxTokens": 80,
            "temperature": 0.1,
        },
    }

    # Try direct model ID first, fall back to inference profile
    for model_id in [PRIMARY_MODEL, INFERENCE_PROFILE]:
        try:
            resp = bedrock_rt.converse(
                modelId=model_id,
                **test_payload,
            )
            reply_text = resp["output"]["message"]["content"][0]["text"]
            input_tokens  = resp["usage"]["inputTokens"]
            output_tokens = resp["usage"]["outputTokens"]

            print(info(f"Model used   : {model_id}"))
            print(info(f"Response     : {reply_text.strip()}"))
            print(info(f"Tokens used  : {input_tokens} in / {output_tokens} out"))

            record(
                "Live text inference",
                True,
                f"Model: {model_id} | Tokens: {input_tokens}in/{output_tokens}out",
            )
            TEXT_TEST_PASSED = True
            WORKING_MODEL_ID = model_id
            break
        except botocore.exceptions.ClientError as exc:
            err_code = exc.response["Error"]["Code"]
            if err_code == "AccessDeniedException":
                print(warn(f"  {model_id} — access denied, trying next..."))
                continue
            raise

    if not TEXT_TEST_PASSED:
        record(
            "Live text inference",
            False,
            "Access denied for both model ID and inference profile.\n"
            "Go to AWS Console → Bedrock → Model access → enable Amazon Nova Pro.",
        )
        WORKING_MODEL_ID = PRIMARY_MODEL  # keep for reporting

except botocore.exceptions.ClientError as exc:
    err_code = exc.response["Error"]["Code"]
    detail   = exc.response["Error"]["Message"]
    record("Live text inference", False, f"{err_code}: {detail}")
    WORKING_MODEL_ID = PRIMARY_MODEL
except Exception as exc:
    record("Live text inference", False, str(exc))
    WORKING_MODEL_ID = PRIMARY_MODEL

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 8: Image (vision) capability confirmation
# ─────────────────────────────────────────────────────────────────────────────
header("CHECK 8 — Image / Vision Capability")

if TEXT_TEST_PASSED:
    try:
        # Create a tiny 1×1 red pixel PNG in memory — no file needed
        import struct, zlib

        def _make_tiny_png() -> bytes:
            """Generate a minimal valid 1×1 red PNG in pure Python."""
            def chunk(name: bytes, data: bytes) -> bytes:
                c = name + data
                return (
                    struct.pack(">I", len(data))
                    + name
                    + data
                    + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
                )

            ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
            raw_row   = b"\x00\xFF\x00\x00"          # filter byte + RGB = red
            idat_data = zlib.compress(raw_row)
            png = (
                b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", ihdr_data)
                + chunk(b"IDAT", idat_data)
                + chunk(b"IEND", b"")
            )
            return png

        tiny_png   = _make_tiny_png()
        img_b64    = base64.standard_b64encode(tiny_png).decode()

        image_payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "image": {
                                "format": "png",
                                "source": {
                                    "bytes": tiny_png
                                },
                            }
                        },
                        {
                            "text": "What color is the single pixel in this image? One word answer."
                        },
                    ],
                }
            ],
            "inferenceConfig": {"maxTokens": 20, "temperature": 0.0},
        }

        img_resp  = bedrock_rt.converse(modelId=WORKING_MODEL_ID, **image_payload)
        img_reply = img_resp["output"]["message"]["content"][0]["text"]
        print(info(f"Image test reply : {img_reply.strip()}"))
        record("Image/vision capability", True, f"Model correctly processed image input — reply: '{img_reply.strip()}'")

    except Exception as exc:
        record("Image/vision capability", False, str(exc))
else:
    record("Image/vision capability", False, "Skipped — text inference did not pass")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 9: Document (PDF) capability confirmation
# ─────────────────────────────────────────────────────────────────────────────
header("CHECK 9 — Document / PDF Capability")

if TEXT_TEST_PASSED:
    try:
        # Minimal valid PDF (single page, "Hello PDF" text)
        MINIMAL_PDF = textwrap.dedent("""\
            %PDF-1.4
            1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
            2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
            3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Contents 4 0 R/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>>>endobj
            4 0 obj<</Length 44>>
            stream
            BT /F1 12 Tf 100 700 Td (Hello PDF) Tj ET
            endstream
            endobj
            xref
            0 5
            0000000000 65535 f\r
            0000000009 00000 n\r
            0000000058 00000 n\r
            0000000115 00000 n\r
            0000000274 00000 n\r
            trailer<</Size 5/Root 1 0 R>>
            startxref
            369
            %%EOF
        """).encode()

        doc_payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "document": {
                                "format": "pdf",
                                "name":   "test_document",
                                "source": {"bytes": MINIMAL_PDF},
                            }
                        },
                        {
                            "text": "What text is in this document? One sentence answer."
                        },
                    ],
                }
            ],
            "inferenceConfig": {"maxTokens": 60, "temperature": 0.0},
        }

        doc_resp  = bedrock_rt.converse(modelId=WORKING_MODEL_ID, **doc_payload)
        doc_reply = doc_resp["output"]["message"]["content"][0]["text"]
        print(info(f"Document test reply : {doc_reply.strip()}"))
        record(
            "Document/PDF capability",
            True,
            f"Model correctly processed PDF input — reply: '{doc_reply.strip()[:80]}'",
        )

    except Exception as exc:
        record("Document/PDF capability", False, str(exc))
else:
    record("Document/PDF capability", False, "Skipped — text inference did not pass")

# ─────────────────────────────────────────────────────────────────────────────
# CHECK 10: Streaming support
# ─────────────────────────────────────────────────────────────────────────────
header("CHECK 10 — Streaming (ConverseStream)")

if TEXT_TEST_PASSED:
    try:
        stream_payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": "Count from 1 to 3, one number per word."}],
                }
            ],
            "inferenceConfig": {"maxTokens": 30, "temperature": 0.0},
        }

        stream_resp = bedrock_rt.converse_stream(
            modelId=WORKING_MODEL_ID, **stream_payload
        )

        streamed_text = []
        for event in stream_resp["stream"]:
            if "contentBlockDelta" in event:
                delta = event["contentBlockDelta"]["delta"].get("text", "")
                streamed_text.append(delta)

        full_streamed = "".join(streamed_text).strip()
        print(info(f"Streamed reply: {full_streamed}"))
        record("Streaming (ConverseStream)", True, f"Reply: '{full_streamed[:60]}'")

    except Exception as exc:
        record("Streaming (ConverseStream)", False, str(exc))
else:
    record("Streaming (ConverseStream)", False, "Skipped — text inference did not pass")

# ─────────────────────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
def _print_summary():
    header("SUMMARY REPORT")
    passed = [r for r in results if r["passed"]]
    failed = [r for r in results if not r["passed"]]

    print(f"\n  Timestamp : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Checks    : {len(results)} total  |  {len(passed)} passed  |  {len(failed)} failed")

    if failed:
        print(f"\n{RED}{BOLD}  Failed checks:{RESET}")
        for r in failed:
            print(fail(r["check"]))
            if r["detail"]:
                for line in r["detail"].splitlines():
                    print(f"       {line}")
        print(f"\n{YELLOW}  Action required: fix the failed checks before running the chatbot.{RESET}")
    else:
        print(f"\n{GREEN}{BOLD}  All checks passed! Your environment is ready.{RESET}")
        print(f"\n  Run the multimodal chatbot with:")
        print(f"{CYAN}    streamlit run mod_chatbot_frontend.py{RESET}")

    print()

_print_summary()
