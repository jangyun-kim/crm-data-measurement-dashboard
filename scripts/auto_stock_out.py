import pandas as pd
from datetime import datetime
from config import DATA_RAW_DIR, DATA_CLEAN_DIR
from stock_register import load_movement, save_movement
from fabric_usage import calc_fabric_usage

def auto_stock_out(order_id, orders_df, master_df):
    """
    특정 주문(order_id)에 대한 원단 자동 OUT 기능
    """

    # 1) 주문 row 찾기
    order = orders_df[orders_df["order_id"] == order_id]
    if order.empty:
        print(f"[ERROR] 주문 {order_id} 를 찾을 수 없습니다.")
        return False

    # 2) 해당 주문의 원단 사용량 계산
    usage_df = calc_fabric_usage(order)
    usage = usage_df["fabric_usage"].sum()

    if usage <= 0:
        print(f"[INFO] 주문 {order_id} 는 원단 사용량이 계산되지 않았습니다.")
        return False

    print(f"[INFO] 주문 {order_id} 원단 필요량: {usage:.2f} m")

    # 3) 원단 stock_id 찾기 (지금은 F001 기준)
    fabric_row = master_df[master_df["category"] == "fabric"]
    if fabric_row.empty:
        print("[ERROR] stock_master에서 fabric 카테고리를 찾을 수 없습니다.")
        return False

    # 단일 원단 사용하는 것을 기본 가정 (추후 멀티 원단 지원 가능)
    fabric_id = fabric_row.iloc[0]["stock_id"]
    fabric_name = fabric_row.iloc[0]["stock_name"]
    unit = fabric_row.iloc[0]["unit"]

    # 4) OUT 기록 생성
    movement = load_movement()

    # 수량 부호 처리
    signed_qty = -abs(usage)  # OUT은 음수

    new_row = {
        "date": datetime.today().strftime("%Y-%m-%d"),
        "stock_id": fabric_id,
        "stock_name": fabric_name,
        "type": "OUT",
        "quantity": usage,
        "quantity_signed": signed_qty,
        "unit": unit,
        "related_order_id": order_id,
        "note": "자동 원단 소요 처리"
    }


    movement = pd.concat([movement, pd.DataFrame([new_row])], ignore_index=True)
    save_movement(movement)

    print(f"[자동 처리 완료] 주문 {order_id} → {fabric_id} 원단 {usage:.2f}{unit} 출고")
    return True


if __name__ == "__main__":
    # 테스트 예시 (직접 지정)
    import pandas as pd
    orders_df = pd.read_excel(DATA_CLEAN_DIR / "orders_2025.xlsx")
    master_df = pd.read_excel(DATA_RAW_DIR / "stock_master.xlsx")

    auto_stock_out("2025-0001-01", orders_df, master_df)
