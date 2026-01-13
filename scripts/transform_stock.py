# scripts/transform_stock.py

import pandas as pd
from config import DATA_RAW_DIR, DATA_CLEAN_DIR

FILE_STOCK_TABLE = DATA_RAW_DIR / "재고입출고.xlsx"

def transform_stock_table():
    df = pd.read_excel(FILE_STOCK_TABLE)

    # 날짜 datetime 변환
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # IN → +, OUT → -
    df["quantity_signed"] = df.apply(
        lambda r: r["quantity"] if r["type"] == "IN" else -r["quantity"],
        axis=1
    )

    df.to_excel(DATA_CLEAN_DIR / "stock_movement.xlsx", index=False)

    return df
