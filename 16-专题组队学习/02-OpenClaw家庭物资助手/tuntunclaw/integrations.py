"""External service integration helpers for the tutorial demo."""

from __future__ import annotations

import os
from dataclasses import dataclass

from inventory import InventoryItem


@dataclass(frozen=True)
class FeishuConfig:
    app_id: str
    app_secret: str
    bitable_app_token: str
    bitable_table_id: str


def load_feishu_config() -> FeishuConfig:
    """Load Feishu credentials from environment variables."""
    return FeishuConfig(
        app_id=os.environ["OPENCLAW_FEISHU_APP_ID"],
        app_secret=os.environ["OPENCLAW_FEISHU_APP_SECRET"],
        bitable_app_token=os.environ["OPENCLAW_FEISHU_BITABLE_APP_TOKEN"],
        bitable_table_id=os.environ["OPENCLAW_FEISHU_BITABLE_TABLE_ID"],
    )


def build_bitable_rows(items: list[InventoryItem]) -> list[dict[str, object]]:
    """Convert inventory items to rows that can be sent to Feishu Bitable."""
    return [
        {
            "name": item.name,
            "category": item.category,
            "quantity": item.quantity,
            "low_stock_threshold": item.low_stock_threshold,
            "location": item.location,
            "is_low_stock": item.is_low_stock,
        }
        for item in items
    ]
