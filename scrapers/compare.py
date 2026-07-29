# scrapers/compare.py
# Analisis perbandingan lintas sumber
# ponytail: stats sederhana via pandas, cukup untuk eksperimen

import json
from pathlib import Path

import pandas as pd

from scrapers.schema import merge_products, save_unified

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def _parse_price(price_str) -> float | None:
    """Konversi string harga ke float. Handle format $12.99, US $5.00, IDR 50.000, dll."""
    if price_str is None:
        return None
    if isinstance(price_str, (int, float)):
        return float(price_str)
    import re

    cleaned = re.sub(r"[^\d.,]", "", str(price_str).strip())
    cleaned = cleaned.replace(",", "")  # asumsi pemisah ribuan, bukan desimal
    try:
        return float(cleaned)
    except ValueError:
        # coba fallback: mungkin koma adalah desimal (format Eropa)
        try:
            return float(cleaned.replace(".", "").replace(",", "."))
        except ValueError:
            return None


def _parse_rating(rating_str) -> float | None:
    """Ekstrak angka rating dari string seperti '4.5 (120 reviews)'."""
    if rating_str is None:
        return None
    if isinstance(rating_str, (int, float)):
        return float(rating_str)
    import re

    match = re.search(r"(\d+\.?\d*)", str(rating_str))
    if match:
        return float(match.group(1))
    return None


def run_comparison():
    """Load data dari kedua sumber, gabung, analisis, simpan hasil."""
    products = merge_products("aliexpress", "walmart")

    if not products:
        print("\n=== NO DATA TO COMPARE ===")
        print("Kedua sumber menghasilkan 0 produk (captcha/block di environment ini).")
        print("Skema terpadu dan fungsi perbandingan siap digunakan saat data tersedia.")
        save_unified([], "unified_products.json")
        return

    df = pd.DataFrame(products)
    df["price_numeric"] = df["price"].apply(_parse_price)
    df["rating_numeric"] = df["rating"].apply(_parse_rating)

    print("\n=========== CROSS-SOURCE COMPARISON ===========")
    print(f"Total products              : {len(df)}")
    print(f"  AliExpress                : {len(df[df['source'] == 'aliexpress'])}")
    print(f"  Walmart                   : {len(df[df['source'] == 'walmart'])}")

    print(f"\n--- Price Distribution ---")
    for src in ["aliexpress", "walmart"]:
        subset = df[df["source"] == src]["price_numeric"]
        if subset.dropna().empty:
            print(f"  {src}: no valid prices")
        else:
            print(
                f"  {src}: count={subset.count()}, "
                f"min=${subset.min():.2f}, max=${subset.max():.2f}, "
                f"mean=${subset.mean():.2f}"
            )

    print(f"\n--- Rating Distribution ---")
    for src in ["aliexpress", "walmart"]:
        subset = df[df["source"] == src]["rating_numeric"]
        if subset.dropna().empty:
            print(f"  {src}: no valid ratings")
        else:
            print(
                f"  {src}: count={subset.count()}, "
                f"min={subset.dropna().min():.1f}, max={subset.dropna().max():.1f}, "
                f"mean={subset.dropna().mean():.1f}"
            )

    print(f"\n--- Top 5 Products by Price ---")
    top = df.dropna(subset=["price_numeric"]).nlargest(5, "price_numeric")
    for _, row in top.iterrows():
        print(f"  [{row['source']}] ${row['price_numeric']:.2f} — {row['title'][:60]}")

    print(f"\n--- Top 5 Products by Rating ---")
    top_rated = df.dropna(subset=["rating_numeric"]).nlargest(5, "rating_numeric")
    for _, row in top_rated.iterrows():
        print(f"  [{row['source']}] {row['rating_numeric']:.1f}/5 — {row['title'][:60]}")

    print("================================================\n")

    output = save_unified(
        df.drop(columns=["price_numeric", "rating_numeric"]).to_dict(orient="records"),
        "unified_products.json",
    )
    print(f"Unified data saved: {output}")


if __name__ == "__main__":
    run_comparison()
