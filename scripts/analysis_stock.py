# scripts/analysis_stock.py

import pandas as pd
from config import DATA_CLEAN_DIR, REPORT_DIR

def analyze_stock(stock_df: pd.DataFrame):
    df = stock_df.copy()

    # 월별 사용량
    df["month"] = df["date"].dt.to_period("M")
    usage = df.groupby(["stock_id", "month"])["quantity_signed"].sum().reset_index()

    # 전체 재고잔량
    balance = df.groupby("stock_id")["quantity_signed"].sum().reset_index()
    balance = balance.rename(columns={"quantity_signed": "balance"})

    # 부족 경고(잔량 10 이하)
    alert = balance[balance["balance"] <= 10]

    out_path = REPORT_DIR / "재고분석.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="raw_stock", index=False)
        usage.to_excel(writer, sheet_name="usage", index=False)
        balance.to_excel(writer, sheet_name="balance", index=False)
        alert.to_excel(writer, sheet_name="low_stock_alert", index=False)

    print(f"[analysis_stock] 재고 분석 보고서 저장됨 → {out_path}")
