"""OpenClaw family inventory assistant demo entry."""

from __future__ import annotations

import os

from inventory import InventoryItem
from workflow_hooks import plan_refill_tasks


REQUIRED_ENV = (
    "OPENCLAW_FEISHU_APP_ID",
    "OPENCLAW_FEISHU_APP_SECRET",
    "OPENCLAW_FEISHU_BITABLE_APP_TOKEN",
    "OPENCLAW_FEISHU_BITABLE_TABLE_ID",
)


def check_environment() -> list[str]:
    """Return required variables that are not configured."""
    return [name for name in REQUIRED_ENV if not os.getenv(name)]


def demo_items() -> list[InventoryItem]:
    return [
        InventoryItem("纸巾", "日用品", 2, 3, "客厅柜"),
        InventoryItem("洗手液", "清洁用品", 1, 1, "卫生间"),
        InventoryItem("电池", "工具耗材", 8, 4, "工具箱"),
    ]


def main() -> None:
    missing = check_environment()
    if missing:
        print("Missing environment variables:")
        for name in missing:
            print(f"- {name}")
        print("Copy .env.example to .env and fill in the Feishu values.")
        return

    print("Environment is ready.")
    print("Planned refill tasks:")
    for task in plan_refill_tasks(demo_items()):
        print(f"- {task.item_name} at {task.location}: {task.reason}")


if __name__ == "__main__":
    main()
