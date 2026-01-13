import pandas as pd
from datetime import datetime
from config import DATA_RAW_DIR
from generate_stock_id import detect_category, get_next_id

MASTER = DATA_RAW_DIR / "stock_master.xlsx"
MOVEMENT = DATA_RAW_DIR / "재고입출고.xlsx"

# 단위 표준
UNIT_MAP = {
    "fabric": "m",
    "lining": "m",
    "interlining": "m",
    "button": "ea",
    "zipper": "ea",
    "other": "ea",
}

def load_master():
    try:
        return pd.read_excel(MASTER)
    except:
        return pd.DataFrame(columns=["stock_id","stock_name","category","unit","cost_per_unit","note"])

def save_master(df):
    df.to_excel(MASTER, index=False)

def load_movement():
    try:
        df = pd.read_excel(MOVEMENT)
    except:
        return pd.DataFrame(columns=[
            "date","stock_id","stock_name","type",
            "quantity","quantity_signed","unit",
            "related_order_id","note"
        ])

    # quantity_signed가 없는 경우 생성
    if "quantity_signed" not in df.columns:
        df["quantity_signed"] = df.apply(
            lambda row: -row["quantity"] if row["type"] == "OUT"
                        else row["quantity"],
            axis=1
        )

    return df


def save_movement(df):
    df.to_excel(MOVEMENT, index=False)

def register_material(name, cost_per_unit=0, initial_qty=0):
    master = load_master()
    movement = load_movement()

    prefix = detect_category(name)
    new_id = get_next_id(master, prefix)

    category = {
        "F": "fabric",
        "L": "lining",
        "I": "interlining",
        "B": "button",
        "Z": "zipper",
    }.get(prefix, "other")

    unit = UNIT_MAP[category]

    # 마스터에 신규 등록 추가
    new_row = {
        "stock_id": new_id,
        "stock_name": name,
        "category": category,
        "unit": unit,
        "cost_per_unit": cost_per_unit,
        "note": ""
    }
    master = pd.concat([master, pd.DataFrame([new_row])], ignore_index=True)
    save_master(master)

    # 초기 입고 처리
    if initial_qty > 0:
        movement_row = {
            "date": datetime.today().strftime("%Y-%m-%d"),
            "stock_id": new_id,
            "stock_name": name,
            "type": "IN",
            "quantity": initial_qty,
            "unit": unit,
            "related_order_id": "",
            "note": "초기입고"
        }
        movement = pd.concat([movement, pd.DataFrame([movement_row])], ignore_index=True)
        save_movement(movement)

    print(f"[등록 완료] {name} → {new_id} | 단가={cost_per_unit}, 초기입고={initial_qty} {unit}")
    return new_id
