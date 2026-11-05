import pytest


@pytest.fixture(autouse=True)
def disable_external_telemetry(monkeypatch):
    for name in [
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "PUSHGATEWAY_URL",
        "LOKI_URL",
    ]:
        monkeypatch.delenv(name, raising=False)
