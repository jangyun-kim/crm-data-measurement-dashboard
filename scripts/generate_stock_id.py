# scripts/generate_stock_id.py

import pandas as pd
from config import DATA_RAW_DIR

# 재고입출고 파일(템플릿 포함)
FILE_STOCK = DATA_RAW_DIR / "재고입출고.xlsx"

# 자재명 키워드 → 타입 매핑
CATEGORY_MAP = {
    "원단": "F",
    "fabric": "F",
    "안감": "L",
    "lining": "L",
    "심지": "I",
    "interlining": "I",
    "단추": "B",
    "button": "B",
    "지퍼": "Z",
    "zipper": "Z",
}

def detect_category(material_name: str) -> str:
    """
    자재명을 기반으로 카테고리 자동 분류 (prefix 반환)
    """
    name_lower = material_name.lower()
    for key, prefix in CATEGORY_MAP.items():
        if key in material_name or key in name_lower:
            return prefix
    return "A"  # 기본: 기타 액세서리


def get_next_id(df: pd.DataFrame, prefix: str) -> str:
    """
    동일 prefix(F, L, I, B...)에서 가장 큰 번호를 찾아 +1 하여 새 ID 생성
    """
    existing = df[df["stock_id"].astype(str).str.startswith(prefix)]

    if existing.empty:
        return f"{prefix}001"

    # 숫자 부분만 추출
    nums = (
        existing["stock_id"]
        .dropna()
        .astype(str)
        .str.replace(prefix, "", regex=False)
        .astype(int)
    )
    new_num = nums.max() + 1
    return f"{prefix}{new_num:03d}"


def generate_stock_id(material_name: str) -> str:
    """
    자재명을 입력하면 자동으로 stock_id 생성.
    """
    try:
        df = pd.read_excel(FILE_STOCK)
    except FileNotFoundError:
        print("⚠️ 재고입출고.xlsx 파일이 존재하지 않아 신규 템플릿을 참조할 수 없습니다.")
        print("   먼저 create_stock_template.py 를 실행하여 템플릿을 생성하세요.")
        return None

    prefix = detect_category(material_name)
    new_id = get_next_id(df, prefix)

    print(f"[자동 생성됨] {material_name} → {new_id}")
    return new_id


if __name__ == "__main__":
    test_name = "이태리 순모 원단 네이비"
    generate_stock_id(test_name)
