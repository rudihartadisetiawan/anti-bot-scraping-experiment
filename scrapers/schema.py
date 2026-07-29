# scrapers/schema.py
# Skema data terpadu untuk semua sumber (AliExpress, Walmart, ...)
# ponytail: satu source of truth buat field definition

import json
from pathlib import Path
from typing import Any

# Field yang wajib ada di setiap produk dari sumber mana pun
PRODUCT_FIELDS = [
    "title",
    "price",
    "product_url",
    "rating",
    "sold_count",
    "source",
    "scraped_at",
]

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def validate_product(product: dict) -> list[str]:
    """Validasi satu produk. Return list error (kosong = valid)."""
    errors = []
    for f in PRODUCT_FIELDS:
        if f not in product:
            errors.append(f"missing field: {f}")
    if product.get("source") not in ("aliexpress", "walmart", None):
        errors.append(f"invalid source: {product.get('source')}")
    if not product.get("title"):
        errors.append("empty title")
    return errors


def load_products(source: str) -> list[dict[str, Any]]:
    """Load produk dari JSON file per sumber."""
    filepath = DATA_DIR / f"{source}_products.json"
    if not filepath.exists():
        return []
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, list):
        return []
    return data


def merge_products(*sources: str) -> list[dict[str, Any]]:
    """Gabung produk dari beberapa sumber, validasi, return list terpadu."""
    all_products = []
    for src in sources:
        products = load_products(src)
        for p in products:
            errors = validate_product(p)
            if errors:
                print(f"[schema] skip invalid product from {src}: {errors}")
                continue
            all_products.append(p)
    return all_products


def save_unified(products: list[dict[str, Any]], filename: str = "unified_products.json") -> Path:
    """Simpan hasil gabungan ke JSON."""
    filepath = DATA_DIR / filename
    filepath.write_text(json.dumps(products, indent=2, ensure_ascii=False), encoding="utf-8")
    return filepath
