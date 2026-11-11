"""HTTP contracts for existing OCR, section-aware chunking, and Ollama."""

import json
import time
from contextlib import nullcontext
from pathlib import Path

import httpx

from rq_generator.config import Settings
from rq_generator.storage import make_chunk


class Services:
    def __init__(self, settings: Settings, client=None, telemetry=None, sleep=time.sleep):
        self.settings = settings
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(settings.service_timeout, connect=10)
        )
        self.owns_client = client is None
        self.telemetry = telemetry
        self.sleep = sleep

    def request(self, method, url, *, observation=None, on_response=None, **kwargs):
        for attempt in range(self.settings.retries + 1):
            span = (
                self.telemetry.observation(
                    **(observation or {"name": "service-request"}), attempt=attempt
                )
                if self.telemetry
                else nullcontext()
            )
            try:
                with span:
                    response = self.client.request(method, url, **kwargs)
                    response.raise_for_status()
                    if on_response:
                        return on_response(response)
                return response
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                retryable = not isinstance(exc, httpx.HTTPStatusError) or (
                    exc.response.status_code == 429 or exc.response.status_code >= 500
                )
                if not retryable or attempt == self.settings.retries:
                    raise
                self.sleep(2**attempt)
        raise RuntimeError("Unreachable retry state")

    def extract(self, path: Path, doc_id: str):
        result = self.request(
            "POST",
            self.settings.ocr_base_url.rstrip("/") + "/services/ocr",
            data={"type_name": "pdf", "doc_id": doc_id},
            files={"file": (path.name, path.read_bytes(), "application/pdf")},
            observation={"name": "ocr"},
        ).json()
        text = result.get("content_parsed")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("OCR returned no usable text")
        result2 = self.request(
            "POST",
            self.settings.chunking_url.rstrip("/") + "/services/chunking/doc_by_titles",
            data={
                "content_parsed": text,
                "doc_id": doc_id,
                "max_split_tokens": str(self.settings.chunk_tokens),
            },
            observation={"name": "section-aware-chunking"},
        ).json()
        texts, titles, tokens = (
            result2.get(key) for key in ["chunk_list", "chunk_title", "token_count"]
        )
        if (
            not isinstance(texts, list)
            or not texts
            or not isinstance(titles, list)
            or not isinstance(tokens, list)
            or len(texts) != len(titles)
            or len(texts) != len(tokens)
            or result2.get("chunk_size") != len(texts)
        ):
            raise ValueError("Chunking returned malformed aligned lists")
        chunks = []
        for index, (content, title, count) in enumerate(zip(texts, titles, tokens, strict=True)):
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Chunking returned empty text")
            chunks.append(
                make_chunk(
                    doc_id,
                    index,
                    content,
                    title,
                    {
                        "token_count": count,
                        "chunk_language": result2.get("chunk_language"),
                        "ocr_language": result.get("ocr_language"),
                    },
                )
            )
        return chunks

    def generate(self, prompt: str, schema: dict):
        observation = {"name": "ollama-generation", "model": self.settings.ollama_model}
        if self.settings.capture_content:
            observation["input"] = prompt
        start = time.monotonic()

        def process(response):
            result = response.json()
            content = result["message"]["content"]
            if self.telemetry:
                self.telemetry.model_result(result, time.monotonic() - start, content)
            if result.get("done_reason") == "length":
                raise ValueError("Model output exhausted its token budget")
            return json.loads(content)

        return self.request(
            "POST",
            self.settings.ollama_base_url.rstrip("/") + "/api/chat",
            json={
                "model": self.settings.ollama_model,
                "stream": False,
                "think": False,
                "format": schema,
                "messages": [{"role": "user", "content": prompt}],
                "options": {
                    "num_ctx": self.settings.context_tokens,
                    "num_predict": self.settings.output_tokens,
                    "temperature": 0,
                },
            },
            observation=observation,
            on_response=process,
        )

    def close(self):
        if self.owns_client:
            self.client.close()
