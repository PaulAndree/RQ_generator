"""Read validated settings without exposing secret values in errors."""

from pathlib import Path
from typing import Any

from pydantic import Field, SecretStr

from rq_generator.models import StrictModel


class Settings(StrictModel):
    output_dir: Path = Path("output")
    ocr_base_url: str = "http://127.0.0.1:8084"
    chunking_url: str = "http://localhost:8085"
    ollama_base_url: str = "http://localhost:11436"
    ollama_model: str = "qwen3:14b"
    context_tokens: int = Field(default=32768, ge=4096)
    output_tokens: int = Field(default=8192, ge=128)
    service_timeout: float = Field(default=600, gt=0)
    retries: int = Field(default=2, ge=0, le=10)
    chunk_tokens: int = Field(default=800, ge=1)
    environment: str = "local"
    loki_url: str = "http://127.0.0.1:3101"
    pushgateway_url: str = "http://127.0.0.1:9095"
    prometheus_url: str = "http://127.0.0.1:9094"
    grafana_url: str = "http://127.0.0.1:3013"
    langfuse_base_url: str = ""
    langfuse_public_key: SecretStr = SecretStr("")
    langfuse_secret_key: SecretStr = SecretStr("")
    capture_content: bool = False
    vocabulary_dir: Path = Path.home() / ".cache" / "rq-generator" / "vocabularies"

    @classmethod
    def from_sources(cls, environment: dict[str, str], overrides: dict[str, Any] | None = None):
        names = {
            "OCR_BASE_URL": "ocr_base_url",
            "CHUNKING_URL": "chunking_url",
            "OLLAMA_BASE_URL": "ollama_base_url",
            "OLLAMA_MODEL": "ollama_model",
            "OLLAMA_CONTEXT_TOKENS": "context_tokens",
            "OLLAMA_OUTPUT_TOKENS": "output_tokens",
            "SERVICE_TIMEOUT_SECONDS": "service_timeout",
            "SERVICE_RETRIES": "retries",
            "CHUNK_MAX_TOKENS": "chunk_tokens",
            "APP_ENV": "environment",
            "LOKI_URL": "loki_url",
            "PUSHGATEWAY_URL": "pushgateway_url",
            "PROMETHEUS_URL": "prometheus_url",
            "GRAFANA_URL": "grafana_url",
            "LANGFUSE_BASE_URL": "langfuse_base_url",
            "LANGFUSE_HOST": "langfuse_base_url",
            "LANGFUSE_PUBLIC_KEY": "langfuse_public_key",
            "LANGFUSE_SECRET_KEY": "langfuse_secret_key",
            "TRACE_CAPTURE_CONTENT": "capture_content",
            "VOCABULARY_DIR": "vocabulary_dir",
            "OUTPUT_DIR": "output_dir",
        }
        values = {field: environment[key] for key, field in names.items() if key in environment}
        if environment.get("LANGFUSE_BASE_URL"):
            values["langfuse_base_url"] = environment["LANGFUSE_BASE_URL"]
        values.update({k: v for k, v in (overrides or {}).items() if v is not None})
        settings = cls.model_validate(values)
        if settings.context_tokens <= settings.output_tokens + 1024:
            raise ValueError("Context budget must exceed output reserve and safety margin")
        return settings
