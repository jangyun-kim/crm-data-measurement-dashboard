# scripts/create_stock_template.py

import pandas as pd
from config import DATA_RAW_DIR
from datetime import datetime

def create_stock_template():
    """
    양복점 재고 자동화 시스템에서 사용할 기본 템플릿 생성.
    직원들은 이 파일에 입/출고 기록만 입력하면 됨.
    """

    columns = [
        "date",              # YYYY-MM-DD
        "stock_id",          # 원단/부자재 코드 (ex: F001, L003, B010)
        "stock_name",        # 원단명 또는 부자재명
        "type",              # IN / OUT
        "quantity",          # 수량
        "unit",              # m 또는 ea
        "related_order_id",  # 주문번호 (출고 시 연결)
        "note"               # 기타 비고
    ]

    # 샘플 데이터(직원이 이해하기 쉬움)
    today = datetime.today().strftime("%Y-%m-%d")
    example_rows = [
        [today, "F001", "이태리 순모 100수 네이비", "IN", 30, "m", "", "초도 입고"],
        [today, "L001", "고급 안감 150D", "IN", 50, "m", "", ""],
        [today, "B001", "소뿔버튼 블랙 L", "IN", 200, "ea", "", ""],
        ["", "", "", "", "", "", "", ""],
        ["2025-01-12", "F001", "이태리 순모 100수 네이비", "OUT", 2.3, "m", "2025-0001-01", "재단 사용"],
        ["2025-01-12", "B001", "소뿔버튼 블랙 L", "OUT", 7, "ea", "2025-0001-01", "단추 작업"],
    ]

    df = pd.DataFrame(example_rows, columns=columns)

    # 저장 경로
    out_path = DATA_RAW_DIR / "재고입출고.xlsx"
    df.to_excel(out_path, index=False)

    print(f"[템플릿 생성 완료] 재고입출고.xlsx 파일이 생성되었습니다.\n→ {out_path}")

if __name__ == "__main__":
    create_stock_template()
