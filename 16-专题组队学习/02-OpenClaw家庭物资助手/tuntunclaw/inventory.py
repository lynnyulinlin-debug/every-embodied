"""Inventory data helpers for the OpenClaw family assistant tutorial."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InventoryItem:
    name: str
    category: str
    quantity: int
    low_stock_threshold: int
    location: str = ""

    @property
    def is_low_stock(self) -> bool:
        return self.quantity <= self.low_stock_threshold


def find_low_stock_items(items: list[InventoryItem]) -> list[InventoryItem]:
    """Return items that should trigger a refill reminder."""
    return [item for item in items if item.is_low_stock]
