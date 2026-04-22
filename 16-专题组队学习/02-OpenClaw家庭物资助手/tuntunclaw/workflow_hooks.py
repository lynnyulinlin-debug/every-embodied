"""Workflow hooks between inventory checks and OpenClaw actions."""

from __future__ import annotations

from dataclasses import dataclass

from inventory import InventoryItem, find_low_stock_items


@dataclass(frozen=True)
class RefillTask:
    item_name: str
    location: str
    reason: str


def plan_refill_tasks(items: list[InventoryItem]) -> list[RefillTask]:
    """Create task descriptions for items that need a refill."""
    return [
        RefillTask(
            item_name=item.name,
            location=item.location or "unknown",
            reason=f"{item.quantity} <= {item.low_stock_threshold}",
        )
        for item in find_low_stock_items(items)
    ]
