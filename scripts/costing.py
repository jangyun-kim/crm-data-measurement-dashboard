import pandas as pd

def calculate_cost(order_df, usage_df, master_df):
    """
    order_df : 주문 테이블
    usage_df : fabric_usage 결과
    master_df: stock_master.xlsx
    """

    # 기본적으로 원단 코드(stock_id) 매핑 필요
    # 여기서는 단일 원단 사용 가정 → F001로 테스트
    fabric_id = "F001"

    cost_per_m = master_df.loc[master_df["stock_id"] == fabric_id, "cost_per_unit"].values
    if len(cost_per_m) == 0:
        cost_per_m = 0
    else:
        cost_per_m = cost_per_m[0]

    df = usage_df.copy()
    df["material_cost"] = df["fabric_usage"] * cost_per_m

    return df[["order_id","item_type","fabric_usage","material_cost"]]
