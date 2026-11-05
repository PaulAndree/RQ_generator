"""Command-line entry point."""

import argparse
import os
from pathlib import Path

from .pipeline import run
from .services import Config, Services
from .telemetry import configure_logging, logger


def main():
    parser = argparse.ArgumentParser(
        description="Generate evidence-linked scientific document cards from a PDF folder."
    )
    parser.add_argument("pdf_directory", type=Path)
    parser.add_argument("--output", type=Path, default=Path("output"))
    parser.add_argument("--ocr-url", default=os.getenv("OCR_BASE_URL", Config.ocr_url))
    parser.add_argument(
        "--chunking-url", default=os.getenv("CHUNKING_URL", Config.chunking_url)
    )
    parser.add_argument(
        "--ollama-url", default=os.getenv("OLLAMA_BASE_URL", Config.ollama_url)
    )
    parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL", Config.model))
    parser.add_argument(
        "--context-tokens",
        type=int,
        default=os.getenv("OLLAMA_CONTEXT_TOKENS", "16384"),
    )
    parser.add_argument(
        "--output-tokens", type=int, default=os.getenv("OLLAMA_OUTPUT_TOKENS", "2048")
    )
    parser.add_argument(
        "--timeout", type=float, default=os.getenv("SERVICE_TIMEOUT_SECONDS", "600")
    )
    args = parser.parse_args()
    configure_logging()
    services = None
    try:
        config = Config(
            ocr_url=args.ocr_url,
            chunking_url=args.chunking_url,
            ollama_url=args.ollama_url,
            model=args.model,
            context_tokens=args.context_tokens,
            output_tokens=args.output_tokens,
            timeout=args.timeout,
        )
        services = Services(config)
        code = run(args.pdf_directory, args.output, services)
    except (ValueError, OSError) as exc:
        logger.error("run_failed", extra={"fields": {"error_type": type(exc).__name__}})
        code = 2
    finally:
        if services:
            services.close()
    raise SystemExit(code)
