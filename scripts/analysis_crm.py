# scripts/analysis_crm.py
import pandas as pd
from config import REPORT_DIR, TARGET_YEAR

def analyze_crm(customers: pd.DataFrame, orders: pd.DataFrame, year: int = TARGET_YEAR):
    """
    간단 CRM 자동 리포트 예시:
    - 최근 주문일 기준 이탈위험 고객
    - 연간 주문횟수 기준 VIP 후보
    (생일/주소 기반 마케팅은 나중에 확장 가능)
    """
    # orders 기준으로 고객코드 → customer_id 매핑이 필요하지만
    # 현재는 customer_code_raw만 있으므로,
    # 우선은 '이름 기반' join 등은 보류하고,
    # orders만으로 '주문 빈도' 기준 분석 예시를 작성.

    df = orders.copy()
    df["year"] = df["order_date"].dt.year
    df_year = df[df["year"] == year].copy()

    # 연간 주문건수 기준 상위 N명
    vip = (
        df_year.groupby("customer_code_raw")["order_id"]
        .nunique()
        .reset_index()
        .rename(columns={"order_id": "order_count"})
        .sort_values("order_count", ascending=False)
    )

    # 최근 주문일 기준 정렬 (이탈 위험 후보: 오래 주문 없는 코드)
    last_order = (
        df.groupby("customer_code_raw")["order_date"]
        .max()
        .reset_index()
        .rename(columns={"order_date": "last_order_date"})
    )

    # 저장
    out_path = REPORT_DIR / f"CRM_기본분석_{year}.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        customers.to_excel(writer, sheet_name="customers_raw", index=False)
        df_year.to_excel(writer, sheet_name="orders_this_year", index=False)
        vip.to_excel(writer, sheet_name="VIP_candidates_code", index=False)
        last_order.to_excel(writer, sheet_name="last_order_by_code", index=False)

    print(f"[analysis_crm] CRM 기본 분석 결과 저장: {out_path}")
