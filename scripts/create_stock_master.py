import pandas as pd
from config import DATA_RAW_DIR

def create_stock_master():
    columns = [
        "stock_id",      # F001, B002 ...
        "stock_name",    # 이태리 순모 100수 네이비
        "category",      # fabric/button/lining/zipper/other
        "unit",          # m / ea
        "cost_per_unit", # 단가
        "note"
    ]

    df = pd.DataFrame(columns=columns)

    path = DATA_RAW_DIR / "stock_master.xlsx"
    df.to_excel(path, index=False)
    print(f"[생성됨] stock_master.xlsx → {path}")

if __name__ == "__main__":
    create_stock_master()
