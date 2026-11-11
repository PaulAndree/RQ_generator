"""Install this application's dashboard into the configured shared Grafana."""

import json
import os
from pathlib import Path

import httpx
from dotenv import dotenv_values


def main():
    settings = {**dotenv_values(), **os.environ}
    token = settings.get("GRAFANA_TOKEN") or settings.get("grafana_user_admin_token")
    if not token:
        raise SystemExit("Set GRAFANA_TOKEN in the environment or ignored .env.")
    base = settings.get("GRAFANA_URL", "http://127.0.0.1:3013").rstrip("/")
    path = Path(__file__).resolve().parents[1] / "monitoring/grafana/document-cards.json"
    dashboard = json.loads(path.read_text())
    try:
        with httpx.Client(headers={"Authorization": "Bearer " + token}, timeout=10) as client:
            response = client.post(
                base + "/api/dashboards/db",
                json={
                    "dashboard": dashboard,
                    "overwrite": True,
                    "message": "Update document cards dashboard",
                },
            )
            response.raise_for_status()
            result = response.json()
            check = client.get(base + "/api/dashboards/uid/" + dashboard["uid"])
            check.raise_for_status()
        print(base + result["url"])
    except httpx.HTTPError as exc:
        raise SystemExit("Grafana import failed: " + type(exc).__name__) from None


if __name__ == "__main__":
    main()
