"""OpenClaw family inventory assistant demo entry."""

from __future__ import annotations

import os


REQUIRED_ENV = (
    "OPENCLAW_FEISHU_APP_ID",
    "OPENCLAW_FEISHU_APP_SECRET",
    "OPENCLAW_FEISHU_BITABLE_APP_TOKEN",
    "OPENCLAW_FEISHU_BITABLE_TABLE_ID",
)


def check_environment() -> list[str]:
    """Return required variables that are not configured."""
    return [name for name in REQUIRED_ENV if not os.getenv(name)]


def main() -> None:
    missing = check_environment()
    if missing:
        print("Missing environment variables:")
        for name in missing:
            print(f"- {name}")
        print("Copy .env.example to .env and fill in the Feishu values.")
        return

    print("Environment is ready. Connect inventory and OpenClaw modules next.")


if __name__ == "__main__":
    main()
