"""Command-line entry point for folder processing."""

import argparse
import os
import sys
import time
from contextlib import nullcontext
from pathlib import Path

from dotenv import dotenv_values

from rq_generator.config import Settings
from rq_generator.entities import load_vocabulary
from rq_generator.generation import Generator
from rq_generator.pipeline import run
from rq_generator.services import Services
from rq_generator.storage import discover
from rq_generator.telemetry import Telemetry


def main(argv=None, *, services=None, normalizer=None, telemetry=None):
    parser = argparse.ArgumentParser(
        description="Generate evidence-linked cards from a PDF folder."
    )
    parser.add_argument("pdf_directory", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    for flag in [
        "ocr-base-url",
        "chunking-url",
        "ollama-base-url",
        "ollama-model",
        "vocabulary-dir",
    ]:
        parser.add_argument("--" + flag)
    args = parser.parse_args(argv)
    try:
        paths = discover(args.pdf_directory)
        environment = {
            **{k: v for k, v in dotenv_values(args.env_file).items() if v is not None},
            **os.environ,
        }
        overrides = vars(args).copy()
        overrides.pop("pdf_directory")
        overrides.pop("env_file")
        settings = Settings.from_sources(environment, overrides)
    except (OSError, ValueError):
        print(
            "Invalid input directory or configuration. Check paths and setting types.",
            file=sys.stderr,
        )
        return 2
    telemetry = telemetry or Telemetry(settings)
    created_services = services is None
    start, successes, failures = time.monotonic(), 0, 0
    try:
        context = (
            telemetry.observation(name="folder-run")
            if hasattr(telemetry, "observation")
            else nullcontext()
        )
        with context:
            telemetry.event("run_started", document_count=len(paths), policy="fresh_run")
            if normalizer is None and paths:
                vocabulary = load_vocabulary(settings.vocabulary_dir)
                normalizer = vocabulary.normalize
                telemetry.event("vocabulary_loaded", snapshots=vocabulary.provenance)
            services = services or Services(settings, telemetry=telemetry)
            generator = Generator(settings, services, normalizer or (lambda *_: []))
            successes, failures = run(paths, settings, services, generator, telemetry)
        return 1 if failures else 0
    except Exception:
        failures = max(failures, 1)
        telemetry.event("run_failed", status="failed", error_type="ConfigurationOrPersistenceError")
        print(
            "Processing stopped. Check output access, active writers, and vocabulary resources.",
            file=sys.stderr,
        )
        return 2
    finally:
        if created_services and services:
            services.close()
        telemetry.close(successes=successes, failures=failures, duration=time.monotonic() - start)
