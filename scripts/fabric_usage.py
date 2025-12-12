import pandas as pd

FABRIC_RULE = {
    "상": 1.6,
    "하": 1.1,
    "조": 0.8,
}

def parse_items(text):
    if pd.isna(text):
        return []

    text = str(text).replace(" ", "")
    parts = text.split(",")

    result = []
    for p in parts:
        if len(p) < 2:
            continue

        code = p[0]        # 상, 하, 조 등
        num = p[1:]        # 숫자

        if not num.isdigit():
            continue

        num = int(num)

        if code in FABRIC_RULE:
            result.append((code, num))

    return result


def calc_fabric_usage(df_orders):
    df = df_orders.copy()

    # 여기서 items 컬럼을 명시적으로 사용
    if "items" not in df.columns:
        # items 컬럼이 없으면 오류 대신 0 반환
        df["fabric_usage"] = 0
        return df[["order_id", "fabric_usage"]]

    df["parsed"] = df["items"].apply(parse_items)

    df["fabric_usage"] = df["parsed"].apply(
        lambda items: sum(FABRIC_RULE[c] * n for c, n in items)
    )

    return df[["order_id", "fabric_usage", "items"]]
