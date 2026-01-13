# scripts/analysis_production.py
import pandas as pd
from config import DATA_CLEAN_DIR, REPORT_DIR, TARGET_YEAR

def analyze_production(orders: pd.DataFrame, year: int = TARGET_YEAR):
    """
    간단한 생산/주문 분석 예시:
    - 월별 주문건수
    - 요일별 주문 패턴 등
    나중에 '완성일', '납품일' 컬럼이 생기면 리드타임까지 확장.
    """
    df = orders.copy()

    # 월별 주문건수
    df["month"] = df["order_date"].dt.month
    month_summary = df.groupby("month")["order_id"].nunique().reset_index()
    month_summary = month_summary.rename(columns={"order_id": "order_count"})

    # 요일별 주문 패턴
    weekday_summary = df.groupby("weekday")["order_id"].nunique().reset_index()
    weekday_summary = weekday_summary.rename(columns={"order_id": "order_count"})

    # 저장
    out_path = REPORT_DIR / f"생산분석_{year}.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="orders_raw", index=False)
        month_summary.to_excel(writer, sheet_name="month_summary", index=False)
        weekday_summary.to_excel(writer, sheet_name="weekday_summary", index=False)

    print(f"[analysis_production] 생산/주문 분석 결과 저장: {out_path}")
